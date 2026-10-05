"""Evidence-first bilingual workflow; language predictions never grant permissions."""

import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from factored_banking import policy
from factored_banking.fixtures import AS_OF
from factored_banking.fraud import assess
from factored_banking.language import authorization_polarity
from factored_banking.privacy import customer_report, redact_text
from factored_banking.references import resolve_reference


class TransactionEvidence(BaseModel):
    """Runtime allowlist for the documented historical sandbox record contract.

    Values are validated before any evidence, prose, handoff or risk input is built.
    Extra tool fields (including labels or personal data) are never projected onward.
    """

    model_config = ConfigDict(strict=True, extra="ignore")
    id: str = Field(min_length=1, max_length=40)
    amount: str = Field(min_length=1, max_length=50)
    currency: Literal["MXN", "COP", "ARS", "USD"]
    status: Literal["completed", "pending", "declined"]
    source: str = Field(min_length=1, max_length=500)
    as_of: str
    provenance: Literal["team_authored_synthetic"]
    merchant: str | None = Field(default=None, max_length=200)
    date: str | None = None
    transaction_date: str | None = None
    channel: str | None = None
    transaction_type: str | None = None
    country: str | None = None

    @field_validator("amount")
    @classmethod
    def valid_amount(cls, value):
        try:
            parsed = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError("Amount must be a decimal string") from exc
        if not parsed.is_finite() or parsed < 0:
            raise ValueError("Amount must be finite and nonnegative")
        return value

    @field_validator("as_of", "date")
    @classmethod
    def valid_date(cls, value):
        if value is not None:
            if len(value) != 10:
                raise ValueError("Date must be ISO YYYY-MM-DD")
            date.fromisoformat(value)
        return value

    @field_validator("transaction_date")
    @classmethod
    def valid_timestamp(cls, value):
        if value is not None:
            datetime.fromisoformat(value)
        return value

    @field_validator("source")
    @classmethod
    def nonblank_source(cls, value):
        if not value.strip():
            raise ValueError("Evidence source must be present")
        return value


COPY = {
    "choose": (
        "¿Cuál de estas operaciones quieres revisar? Dime el comercio, el importe o su número.",
        "Qual destas operações você quer consultar? Diga o estabelecimento, o valor ou o número.",
    ),
    "unsupported": (
        "Puedo explicar operaciones y preparar casos de revisión. No puedo mover dinero, "
        "aprobar créditos ni cambiar datos bancarios. Puedes pedir un agente.",
        "Posso explicar operações e preparar casos para análise. Não posso movimentar dinheiro, "
        "aprovar crédito nem alterar dados bancários. Você pode pedir um agente.",
    ),
    "denied": (
        "No hay una operación autorizada con esa referencia en tu sesión.",
        "Não há uma operação autorizada com essa referência na sua sessão.",
    ),
    "invalid_record": (
        "No puedo verificar los datos de esta operación. Preparé una propuesta de revisión "
        "humana sin presentar esos datos como hechos. "
        "Confírmala si deseas crear un caso de prueba.",
        "Não posso verificar os dados desta operação. Preparei uma proposta de análise humana "
        "sem apresentar esses dados como fatos. Confirme se deseja criar um caso de teste.",
    ),
    "verify_record": (
        "Verificar los datos incompletos o inconsistentes antes de responder sobre la operación.",
        "Verificar os dados incompletos ou inconsistentes antes de responder sobre a operação.",
    ),
    "confirm": (
        "Preparé un caso de prueba para revisión humana. Revisa la evidencia y usa Confirmar caso "
        "para crearlo. Aún no se ha realizado ninguna acción.",
        "Preparei um caso de teste para análise humana. Revise as evidências e use Confirmar caso "
        "para criá-lo. Nenhuma ação foi realizada ainda.",
    ),
    "cancel": (
        "Cancelé la propuesta pendiente. No se creó un caso nuevo.",
        "Cancelei a proposta pendente. Nenhum caso novo foi criado.",
    ),
    "use_button": (
        "Para crear el caso, revisa la propuesta y usa su botón de confirmación. "
        "Puedes cancelarla.",
        "Para criar o caso, revise a proposta e use o botão de confirmação. Você pode cancelá-la.",
    ),
    "cases": (
        "Consulta Mis casos para ver el estado verificado de tus solicitudes de prueba.",
        "Consulte Meus casos para ver o estado verificado das suas solicitações de teste.",
    ),
    "privacy": (
        "No envíes contraseñas, códigos ni datos personales. Esta demostración usa solo "
        "operaciones ficticias y no puede consultar otras cuentas.",
        "Não envie senhas, códigos nem dados pessoais. Esta demonstração usa apenas "
        "operações fictícias e não pode consultar outras contas.",
    ),
    "clarify_topic": (
        "¿Te refieres a una operación o a un caso de revisión? Dime el comercio, "
        "el importe o la referencia del caso para consultar la información correcta.",
        "Você se refere a uma operação ou a um caso de análise? Diga o estabelecimento, "
        "o valor ou a referência do caso para consultar a informação correta.",
    ),
}


def say(key, language):
    return COPY[key][language == "pt"]


def normalize(text):
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", text.lower())
        if not unicodedata.combining(char)
    )


def deictic_selection(text, language):
    """Recognize only a complete short selection reply, never a request prefix."""
    patterns = {
        "es": r"(?:esta|esa|aquella|este|ese|aquel)"
        r"(?: (?:operacion|transaccion|movimiento|pago|cargo))?",
        "pt": r"(?:esta|essa|aquela|este|esse|aquele)"
        r"(?: (?:operacao|transacao|movimento|pagamento|cobranca))?",
    }
    normalized = " ".join(text.split()).strip(".!?¿¡ ")
    return bool(language in patterns and re.fullmatch(patterns[language], normalized))


def transaction_evidence(transaction, language):
    return {
        "id": transaction["id"],
        "title": "Registro de operación" if language == "es" else "Registro da operação",
        "source": transaction["source"],
        "text": f"{transaction['amount']} {transaction['currency']} · {transaction['status']}",
        "as_of": transaction["as_of"],
        "provenance": transaction["provenance"],
    }


def validated_records(records):
    """Only complete, uniquely keyed evidence may be offered as a chat reference."""
    values = []
    ids = [row.get("id") for row in records or [] if isinstance(row, dict)]
    for row in records or []:
        try:
            value = TransactionEvidence.model_validate(row).model_dump()
            if ids.count(value["id"]) == 1:
                values.append(value)
        except (ValidationError, ValueError):
            continue
    return values


def clarify(result, intent, report, records, language, *, unmatched=False):
    options = [
        {
            key: row.get(key)
            for key in (
                "id",
                "merchant",
                "amount",
                "currency",
                "status",
                "date",
                "source",
                "as_of",
                "provenance",
            )
        }
        for row in records[:20]
    ]
    prefix = (
        (
            "No encuentro una coincidencia exacta con esos datos. "
            if language == "es"
            else "Não encontro uma correspondência exata com esses dados. "
        )
        if unmatched
        else ""
    )
    labels = {
        "completed": ("completada", "concluída"),
        "pending": ("pendiente", "pendente"),
        "declined": ("rechazada", "recusada"),
    }
    lines = [prefix + say("choose", language)]
    for index, row in enumerate(options, 1):
        merchant = row["merchant"] or (
            "comercio no informado" if language == "es" else "estabelecimento não informado"
        )
        label = labels[row["status"]][language == "pt"]
        lines.append(
            f"{index}. {merchant} · {row['amount']} {row['currency']} · {label}"
            f" · {row['date'] or row['as_of']} ({row['id']})"
        )
    if not options:
        lines = [
            "No tengo una operación con datos verificables. Puedes indicar su referencia "
            "o pedir revisión humana."
            if language == "es"
            else "Não tenho uma operação com dados verificáveis. Você pode informar a referência "
            "ou pedir análise humana."
        ]
    result.update(
        message="\n".join(lines),
        intent=intent,
        state="clarification",
        transaction_options=options,
        evidence=[transaction_evidence(row, language) for row in records[:20]],
        context={
            "pending_intent": intent if intent != "ambiguous" else "transaction_status",
            "customer_report": report,
            "transaction_candidates": [row["id"] for row in options],
        },
    )
    return result


def run(message, language, transaction_id, context, records, classifier):
    message = redact_text(message)
    text = normalize(message)
    result = {
        "message": "",
        "intent": "unsupported",
        "state": "abstained",
        "evidence": [],
        "as_of": AS_OF,
        "proposal": None,
        "receipt": None,
    }
    courtesy = re.fullmatch(
        r"(?:hola|ola|oi|buenas|buenos dias|buenas tardes|buenas noches|"
        r"bom dia|boa tarde|boa noite|"
        r"gracias|muchas gracias|obrigado|obrigada|muito obrigado|muito obrigada)"
        r"(?: claro)?[.!¡¿? ]*",
        text,
    )
    language_request = re.fullmatch(
        r"(?:(?:responde|responda|habla|fale|continua|continue|cambia|mude) )?"
        r"(?:en|em) (?:espanol|castellano|portugues)(?: por favor)?[.!¡¿? ]*",
        text,
    )
    if courtesy or language_request:
        thanks = bool(re.search(r"gracias|obrigad", text))
        response = (
            (
                "Con gusto. Puedes seguir preguntando aquí."
                if thanks
                else "Hola. Cuéntame qué ocurrió o pregunta por un movimiento; buscaré los datos "
                "de tu sesión de prueba. No compartas claves ni datos personales."
            )
            if language == "es"
            else (
                "De nada. Você pode continuar perguntando aqui."
                if thanks
                else "Olá. Conte o que aconteceu ou pergunte sobre uma operação; "
                "consultarei os dados da sua sessão de teste. "
                "Não compartilhe senhas nem dados pessoais."
            )
        )
        if language_request:
            response = (
                "Claro, seguimos en español. Puedes continuar con tu consulta."
                if language == "es"
                else "Claro, continuamos em português. Você pode continuar sua consulta."
            )
        result.update(message=response, intent="ambiguous", state="resolved", context=dict(context))
        return result
    if re.fullmatch(
        r"(?:por favor )?(?:cancelar|cancela|cancel|cancele)"
        r"(?: (?:el |o |la |a |mi |minha )?(?:caso|propuesta|proposta|solicitud|solicitacao))?"
        r"(?: por favor)?[.! ]*",
        text,
    ):
        result.update(message=say("cancel", language), state="cancelled", context={})
        return result
    if text.strip(" .!¿?¡") in {"si", "sim", "yes", "confirmo", "confirmar"}:
        result.update(message=say("use_button", language), state="awaiting_confirmation")
        return result
    if re.search(
        r"ignore.*(instru|regla|rule)|system prompt|^(revela|revele).*(contrase|senha)|"
        r"otro cliente|outr[oa] client|other customer|revela.*secret|reveal.*secret",
        text,
    ):
        result.update(message=say("privacy", language), state="blocked")
        return result
    try:
        assessment = classifier(message, language)
    except Exception:
        # Model outage is visible and fails closed to human assistance, never a fake prediction.
        assessment = {
            "intent": "human",
            "confidence": 0.0,
            "model_version": "unavailable",
            "signals": ["model_unavailable"],
        }
    intent = assessment.get("intent", "unsupported")
    signals = assessment.get("signals", [])
    authorization = authorization_polarity(message)
    review_required = (
        bool(
            set(signals)
            & {
                "model_unavailable",
                "provider_uncertain",
                "customer_reported_scam",
                "customer_reported_dispute",
                "explicit_human_request",
            }
        )
        or authorization == "negated"
    )
    # Reports, urgency and explicit requests override only toward review, never toward a write.
    if "model_unavailable" in signals or "provider_uncertain" in signals:
        intent = "human"
    elif "customer_reported_scam" in signals:
        intent = "scam"
    elif "customer_reported_dispute" in signals or authorization == "negated":
        intent = "dispute"
    elif "explicit_human_request" in signals:
        intent = "human"
    if intent not in {
        "transaction_status",
        "dispute",
        "scam",
        "human",
        "case_status",
        "ambiguous",
        "unsupported",
    }:
        intent = "unsupported"
    result["assessment"] = assessment
    usable = validated_records(records)
    reference = resolve_reference(message, context, usable)
    case_reference = bool(re.search(r"\bCASE-[A-Z0-9]+\b", message.upper()))
    case_terms = bool(re.search(r"\b(?:caso|casos|reclamo|reclamacion|chamado|protocolo)\b", text))
    tracking_reference = case_reference or bool(
        re.search(
            r"\b(?:casos?|tickets?|folios?|protocolos?|expedientes?|reclamos?|reclamaciones?|"
            r"reclamacao|reclamacoes|chamados?|disputas?|contestacao|contestacoes|solicitud|solicitudes|"
            r"solicitacao|solicitacoes|pedidos?|processos?|seguimiento|acompanhamento|referencia|"
            r"soporte|suporte|revision|analise|investigacion|investigacao)\b",
            text,
        )
    )
    known_case = context.get("last_case_id")
    if (
        known_case
        and intent == "ambiguous"
        and re.search(
            r"\b(?:antes|anterior|previo|previa|eso|essa|esse|aquello|aquilo|mesmo|igual|"
            r"sigue|segue|continua)\b",
            text,
        )
        and not re.search(
            r"transacci|transac|operacion|operacao|movimiento|movimento|cargo|cobranca|pago|pagamento",
            text,
        )
    ):
        intent = "case_status"
    unsupported_action = bool(
        re.search(
            r"\b(?:transfiere|transfira|transferir|envia|envie|mueve|movimente|reembolsa|reembolse|"
            r"aprueba|aprove|bloquea|bloqueie|desbloquea|desbloqueie)\b|"
            r"\b(?:cambia|cambie|altera|altere).{0,30}(?:contrasena|senha|direccion|endereco|datos|dados)|"
            r"\b(?:receta|receita|poema|clima)\b",
            text,
        )
    )
    explicit_fact_request = bool(
        re.search(
            r"[?¿]|\b(?:cual|qual|como|cuando|onde|donde|por que|dime|diga|"
            r"saber|consultar|ver|explica|explique|informame|informe|muestra|mostre)\b",
            text,
        )
    )
    status_question = (
        explicit_fact_request
        and bool(
            re.search(
                r"\b(?:estado|estatus|status|importe|monto|valor|quantia|situacion|situacao|"
                r"informacion|informacoes)\b|"
                r"(?:que paso|que aconteceu|por que|porque|ya salio|ja saiu)",
                text,
            )
        )
        and bool(
            reference.mentioned
            or context.get("transaction_id")
            or re.search(
                r"transacci|transac|operacion|operacao|movimiento|movimento|cargo|cobranca|"
                r"pago|pagamento|transferencia|compra|lancamento|debito|\btx-",
                text,
            )
        )
    )
    affirmative_authorization = authorization == "affirmed" and not review_required
    recorded_status_query = (
        status_question
        and bool(
            re.search(
                r"\b(?:estado|estatus|status|situacion|situacao)\b",
                text,
            )
        )
        and not re.search(
            r"\b(?:registrar|registre|registrare|abrir|reportar|reclamar|contestar)\b|"
            r"incorret|incorrect|duplicad|coincid|dos veces|duas vezes",
            text,
        )
    )
    # Exact scoped detail + an explicit fact question outranks a mistaken learned
    # intent. Reports, human requests and unavailable inference still require review.
    if not review_required:
        if unsupported_action:
            intent = "unsupported"
        elif (
            status_question
            and (
                intent not in {"dispute", "scam"}
                or (intent == "dispute" and (affirmative_authorization or recorded_status_query))
            )
            and (not case_reference and not case_terms)
        ):
            intent = "transaction_status"
    if not review_required and (
        case_reference
        or re.fullmatch(r"(?:mis|meus|meus? |mis? )?\s*(?:casos|reclamos|chamados)[.!? ]*", text)
    ):
        intent = "case_status"
    if intent == "case_status" and not tracking_reference and not known_case:
        if context.get("pending_intent") in {"transaction_status", "dispute", "scam", "human"}:
            intent = "ambiguous"
        else:
            result.update(
                message=say("clarify_topic", language),
                intent="ambiguous",
                state="clarification",
                context={},
            )
            return result
    # A selection completes the pending task; a new explicit request replaces it.
    authorized_ids = [
        row["id"]
        for row in records or []
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    ]
    selection_only = re.fullmatch(
        r"TX-[A-Z]{2}-\d+", message.strip().upper()
    ) is not None or message.strip().casefold() in {
        identifier.casefold() for identifier in authorized_ids
    }
    pending = context.get("pending_intent")
    selection_reply = (
        selection_only or deictic_selection(text, language) or reference.selection_only
    )
    explicit_new_request = bool(
        unsupported_action
        or status_question
        or re.search(
            r"\b(?:otro|otra|outro|outra|nuevo|nueva|novo|nova) "
            r"(?:cargo|cobranca|pago|pagamento|operacion|operacao|transaccion|transacao|"
            r"transferencia|compra|debito|movimiento|movimento)\b",
            text,
        )
        or re.match(
            r"(?:(?:ahora|agora|en cambio|por otra parte|por outro lado)[, ]+)?"
            r"(?:quiero|quero|necesito|preciso|me gustaria|gostaria|dime|diga|muestra|mostre|"
            r"consulta|consulte|explica|explique|abre|abra|registrar|registre|abrir) "
            r"(?!(?:agregar|anadir|aclarar|completar|acrescentar|adicionar|esclarecer|"
            r"complementar)\b)",
            text,
        )
    )
    continuation = (
        pending in {"transaction_status", "dispute", "scam", "human"}
        and not explicit_new_request
        and (
            selection_reply
            or (intent == "ambiguous" and not review_required)
            or (
                pending in {"dispute", "scam", "human"}
                and (reference.mentioned or intent in {"dispute", "scam", "human"})
            )
        )
    )
    report = customer_report(
        message, context, continuation=continuation, selection_only=selection_reply
    )
    result["customer_report"] = report
    # Record ambiguity can return before selecting a transaction. Restore the
    # pending review intent first so those clarifications retain the same task.
    if (
        not review_required
        and continuation
        and pending in {"dispute", "scam", "human"}
        and intent in {"ambiguous", "transaction_status", "unsupported"}
    ):
        intent = pending
    referenced = re.findall(r"\bTX-[A-Z]{2}-\d+\b", message.upper())
    for identifier in authorized_ids:
        if re.search(r"(?<!\w)" + re.escape(identifier) + r"(?!\w)", message, re.IGNORECASE):
            if identifier.upper() not in {value.upper() for value in referenced}:
                referenced.append(identifier)
    if len(set(referenced)) > 1:
        return clarify(result, intent, report, usable, language)
    if referenced:
        if transaction_id and referenced[0] != transaction_id:
            return clarify(result, intent, report, usable, language)
        transaction_id = referenced[0]
        if (
            transaction_id in {row["id"] for row in usable}
            and reference.mentioned
            and (transaction_id not in {row["id"] for row in reference.candidates})
        ):
            return clarify(result, intent, report, usable, language, unmatched=True)
    if intent == "case_status":
        result.update(
            message=say("cases", language), intent=intent, state="case_lookup", context={}
        )
        if not tracking_reference and known_case:
            result["case_context_id"] = known_case
        return result
    retained_transaction_id = context.get("transaction_id")
    if (
        reference.mentioned
        and not referenced
        and (intent != "unsupported" or reference.selection_only)
        and not unsupported_action
    ):
        if len(reference.candidates) != 1 or (
            transaction_id and reference.candidates[0]["id"] != transaction_id
        ):
            if intent in {"scam", "human"} and not transaction_id:
                # Urgent scam/human help must not wait for a record match. Retain
                # the allegation without attaching a guessed historical record.
                retained_transaction_id = None
            else:
                return clarify(
                    result,
                    intent if intent != "unsupported" else pending or "transaction_status",
                    report,
                    reference.candidates or usable,
                    language,
                    unmatched=not reference.candidates,
                )
        else:
            transaction_id = reference.candidates[0]["id"]
    if not review_required:
        if pending in {"transaction_status", "dispute", "scam", "human"} and (
            deictic_selection(text, language) or reference.selection_only
        ):
            # Without a selected record this still clarifies; it never chooses a record.
            intent = pending
        elif transaction_id and (intent == "ambiguous" or selection_only):
            intent = context.get("pending_intent", "transaction_status")
        elif intent == "ambiguous" and context.get("transaction_id"):
            intent = context.get("pending_intent", "transaction_status")
        elif reference.selection_only and intent in {"unsupported", "ambiguous"}:
            intent = "transaction_status"
    selected = transaction_id or retained_transaction_id
    matches = [
        row
        for row in (records or [])
        if selected and isinstance(row, dict) and row.get("id") == selected
    ]
    transaction = matches[0] if len(matches) == 1 else None
    if selected and matches:
        try:
            if len(matches) != 1:
                raise ValueError("Ambiguous record key")
            transaction = TransactionEvidence.model_validate(transaction).model_dump()
        except (ValidationError, ValueError):
            result.update(
                message=say("invalid_record", language),
                intent="human",
                state="awaiting_confirmation",
                context={"customer_report": report},
                evidence=policy.retrieve("human", language),
            )
            payload = proposal_payload("human", language, result, "invalid_transaction_evidence")
            payload["unverified_transaction_reference"] = selected
            payload["open_questions"].insert(0, say("verify_record", language))
            result["proposal_payload"] = payload
            return result
    if selected and transaction is None:
        result.update(message=say("denied", language), state="blocked", context={})
        return result
    result["intent"] = intent
    result["context"] = (
        {"pending_intent": intent, "customer_report": report}
        if intent in {"transaction_status", "dispute", "scam", "human"}
        else {}
    )
    if intent in {"transaction_status", "dispute", "ambiguous"} and transaction is None:
        return clarify(result, intent, report, usable, language)
    result["evidence"] = policy.retrieve(intent, language)
    if transaction:
        result["transaction"] = transaction
        result["evidence"].insert(0, transaction_evidence(transaction, language))
        result["context"] = {
            "transaction_id": transaction["id"],
            "pending_intent": intent,
            "customer_report": report,
        }
    if intent == "transaction_status":
        states = {
            "completed": ("completada", "concluída"),
            "pending": ("pendiente", "pendente"),
            "declined": ("rechazada", "recusada"),
        }
        status = states[transaction["status"]][language == "pt"]
        merchant = transaction.get("merchant") or (
            "comercio no informado" if language == "es" else "estabelecimento não informado"
        )
        if language == "es":
            response = (
                f"La operación {transaction['id']} por {transaction['amount']} "
                f"{transaction['currency']} en {merchant} figura como {status}. "
                f"Registro histórico al {transaction['as_of']}."
            )
        else:
            response = (
                f"A operação {transaction['id']} de {transaction['amount']} "
                f"{transaction['currency']} em {merchant} consta como {status}. "
                f"Registro histórico em {transaction['as_of']}."
            )
        response += " " + policy.POLICIES[intent][language]
        result.update(message=response, state="resolved")
    elif intent in {"dispute", "scam", "human"}:
        result.update(message=say("confirm", language), state="awaiting_confirmation")
        result["proposal_payload"] = proposal_payload(intent, language, result)
    elif intent == "case_status":
        result.update(message=say("cases", language), state="case_lookup")
    else:
        result.update(message=say("unsupported", language), state="abstained")
    return result


def proposal_payload(intent, language, result, reason=None):
    report = result.get("customer_report", "")
    risk = assess(result.get("transaction") or {})
    return {
        "intent": intent,
        "language": language,
        "customer_report": report,
        "report_provenance": "customer_allegation_redacted_not_verified",
        "transaction": result.get("transaction"),
        "evidence": result["evidence"],
        "priority": "high" if intent == "scam" else "normal",
        "policy_version": policy.VERSION,
        "risk": risk,
        "open_questions": [
            "Se requiere valoración humana del reporte del cliente."
            if language == "es"
            else "O relato do cliente precisa de avaliação humana."
        ],
        "actions_taken": [],
        "reason": reason or intent,
        "summary": policy.POLICIES[intent][language],
        "provenance": "team_authored_sandbox",
    }

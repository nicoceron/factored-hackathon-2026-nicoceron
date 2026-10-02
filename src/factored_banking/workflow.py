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
from factored_banking.privacy import customer_report, redact_text


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
        "¿A qué transacción te refieres? Selecciona una de tus operaciones para continuar.",
        "A qual transação você se refere? Selecione uma das suas operações para continuar.",
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
    review_required = bool(
        set(signals)
        & {
            "model_unavailable",
            "provider_uncertain",
            "customer_reported_scam",
            "customer_reported_dispute",
            "explicit_human_request",
        }
    )
    # Reports, urgency and explicit requests override only toward review, never toward a write.
    if "model_unavailable" in signals or "provider_uncertain" in signals:
        intent = "human"
    elif "customer_reported_scam" in signals:
        intent = "scam"
    elif "customer_reported_dispute" in signals:
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
    # A selection completes the pending task; a new explicit request replaces it.
    selection_only = re.fullmatch(r"TX-[A-Z]{2}-\d+", message.strip().upper()) is not None
    pending = context.get("pending_intent")
    continuation = pending in {"transaction_status", "dispute", "scam", "human"} and (
        selection_only
        or deictic_selection(text, language)
        or (intent == "ambiguous" and not review_required)
    )
    report = customer_report(message, context, continuation=continuation)
    result["customer_report"] = report
    referenced = re.findall(r"\bTX-[A-Z]{2}-\d+\b", message.upper())
    if len(set(referenced)) > 1:
        result.update(
            message=say("choose", language),
            intent="ambiguous",
            state="clarification",
            context={
                "pending_intent": intent if intent != "ambiguous" else "transaction_status",
                "customer_report": report,
            },
        )
        return result
    if referenced:
        if transaction_id and referenced[0] != transaction_id:
            result.update(
                message=say("choose", language),
                intent="ambiguous",
                state="clarification",
                context={
                    "pending_intent": intent if intent != "ambiguous" else "transaction_status",
                    "customer_report": report,
                },
            )
            return result
        transaction_id = referenced[0]
    if not review_required:
        if pending in {"transaction_status", "dispute", "scam", "human"} and deictic_selection(
            text, language
        ):
            # Without a selected record this still clarifies; it never chooses a record.
            intent = pending
        elif transaction_id and (intent == "ambiguous" or selection_only):
            intent = context.get("pending_intent", "transaction_status")
        elif intent == "ambiguous" and context.get("transaction_id"):
            intent = context.get("pending_intent", "transaction_status")
    selected = transaction_id or context.get("transaction_id")
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
        result.update(
            message=say("choose", language),
            state="clarification",
            context={
                "pending_intent": intent if intent != "ambiguous" else "transaction_status",
                "customer_report": report,
            },
        )
        return result
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

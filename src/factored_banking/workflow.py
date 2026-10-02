"""Evidence-first bilingual workflow; language predictions never grant permissions."""

import re
import unicodedata

from factored_banking import policy
from factored_banking.fixtures import AS_OF
from factored_banking.fraud import assess

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
    # Reports, urgency and explicit requests override only toward review, never toward a write.
    if "model_unavailable" in signals:
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
    referenced = re.findall(r"\bTX-[A-Z]{2}-\d+\b", message.upper())
    if len(set(referenced)) > 1:
        result.update(message=say("choose", language), intent="ambiguous", state="clarification")
        return result
    if referenced:
        if transaction_id and referenced[0] != transaction_id:
            result.update(
                message=say("choose", language), intent="ambiguous", state="clarification"
            )
            return result
        transaction_id = referenced[0]
    # A selection completes the pending task; a new explicit request replaces it.
    selection_only = re.fullmatch(r"TX-[A-Z]{2}-\d+", message.strip().upper()) is not None
    if transaction_id and (intent == "ambiguous" or selection_only):
        intent = context.get("pending_intent", "transaction_status")
    if intent == "ambiguous" and context.get("transaction_id"):
        intent = context.get("pending_intent", "transaction_status")
    selected = transaction_id or context.get("transaction_id")
    transaction = next((row for row in records if row["id"] == selected), None)
    if selected and transaction is None:
        result.update(message=say("denied", language), state="blocked", context={})
        return result
    result["intent"] = intent
    if intent in {"transaction_status", "dispute", "ambiguous"} and transaction is None:
        result.update(
            message=say("choose", language),
            state="clarification",
            context={"pending_intent": intent if intent != "ambiguous" else "transaction_status"},
        )
        return result
    result["evidence"] = policy.retrieve(intent, language)
    if transaction:
        result["transaction"] = transaction
        result["evidence"].insert(0, transaction_evidence(transaction, language))
        result["context"] = {"transaction_id": transaction["id"], "pending_intent": intent}
    if intent == "transaction_status":
        states = {
            "completed": ("completada", "concluída"),
            "pending": ("pendiente", "pendente"),
            "declined": ("rechazada", "recusada"),
        }
        if transaction.get("status") not in states or not all(
            transaction.get(key) for key in ("amount", "currency", "as_of", "source")
        ):
            result.update(message=say("confirm", language), state="awaiting_confirmation")
            result["proposal_payload"] = proposal_payload("human", language, result, "missing_data")
            return result
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
    report = {
        "dispute": (
            "El cliente reporta una operación no reconocida.",
            "O cliente relata uma operação não reconhecida.",
        ),
        "scam": (
            "El cliente reporta un posible engaño y requiere revisión humana.",
            "O cliente relata uma possível fraude e precisa de análise humana.",
        ),
        "human": ("El cliente solicita atención humana.", "O cliente solicita atendimento humano."),
    }[intent][language == "pt"]
    risk = assess(result.get("transaction") or {})
    return {
        "intent": intent,
        "language": language,
        "customer_report": report,
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

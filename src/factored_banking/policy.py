"""Versioned, explicitly synthetic service policy. Code owns permissions and actions."""

VERSION = "claro-sandbox-policy-v1"
POLICIES = {
    "transaction_status": {
        "es": "Solo informamos el estado registrado y su fecha. Un rechazo no indica su causa; "
        "un pendiente no garantiza liquidación.",
        "pt": "Informamos apenas o estado registrado e sua data. Uma recusa não indica a causa; "
        "uma pendência não garante liquidação.",
    },
    "dispute": {
        "es": "Un cargo no reconocido requiere revisión humana. Con confirmación creamos un caso "
        "de prueba. No bloqueamos tarjetas ni prometemos reembolsos.",
        "pt": "Uma cobrança não reconhecida exige análise humana. Com confirmação criamos um caso "
        "de teste. Não bloqueamos cartões nem prometemos reembolso.",
    },
    "scam": {
        "es": "Un posible engaño requiere revisión humana prioritaria, independientemente del "
        "riesgo estimado. No compartas contraseñas ni códigos aquí.",
        "pt": "Uma possível fraude exige análise humana prioritária, independentemente do "
        "risco estimado. Não compartilhe senhas nem códigos aqui.",
    },
    "human": {
        "es": "Puedes solicitar revisión humana de prueba. El caso contiene hechos verificados "
        "y preguntas abiertas. No hay agentes bancarios reales conectados.",
        "pt": "Você pode solicitar análise humana de teste. O caso contém fatos verificados "
        "e perguntas em aberto. Não há agentes bancários reais conectados.",
    },
}


def retrieve(intent: str, language: str) -> list[dict]:
    """Exact lookup is preferable to approximate RAG for four reviewed policy sections."""
    if intent not in POLICIES:
        return []
    return [
        {
            "id": f"{VERSION}/{intent}",
            "title": "Política de demostración" if language == "es" else "Política de demonstração",
            "source": VERSION,
            "text": POLICIES[intent][language],
            "as_of": "2026-10-02",
            "provenance": "team_authored_synthetic_policy",
        }
    ]

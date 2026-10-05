"""Final independent-review regression: recognition negation must require review.

These targeted scenarios leave the frozen learned corpora and model unchanged.
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from factored_banking.api import create_app
from factored_banking.fixtures import transactions
from factored_banking.language import authorization_polarity, classify, safety_signals
from factored_banking.workflow import run

PAST_AND_SELF_DENIAL_REPORTS = [
    ("es", "¿Por qué tengo un cargo de Tienda Demo? No reconocí ese cobro."),
    ("pt", "Por que tenho uma cobrança da Tienda Demo? Não reconheci essa compra."),
    ("es", "¿Por qué tengo un cargo de Tienda Demo? No fui yo."),
    ("pt", "Qual é o status da cobrança da Tienda Demo? Não fui eu."),
    ("es", "¿Cuál es el estado del cargo de Tienda Demo? Yo nunca lo reconocí."),
    ("pt", "Qual é o estado da cobrança da Tienda Demo? Nunca a reconheci."),
    ("pt", "Qual é o status da cobrança da Tienda Demo? No lo reconocí."),
]

NEGATED_REPORTS = [
    ("es", "¿Por qué tengo un cargo de Tienda Demo? No lo reconozco."),
    ("es", "¿Cuál es el estado del pago de Tienda Demo? Nunca hice esa compra."),
    ("es", "¿Qué pasó con la compra de Tienda Demo? No la autoricé."),
    ("es", "¿Por qué figura el pago de Tienda Demo? Jamás lo realicé."),
    ("es", "¿Cuál es el estado de la compra de Tienda Demo? No la hicimos."),
    ("pt", "Por que tenho uma cobrança da Tienda Demo? Não a reconheço."),
    ("pt", "Qual é o estado do pagamento da Tienda Demo? Nunca fiz essa compra."),
    ("pt", "O que aconteceu com a compra na Tienda Demo? Não a autorizei."),
    ("pt", "Por que aparece a cobrança da Tienda Demo? Jamais a realizei."),
    ("pt", "Qual é o status da compra na Tienda Demo? Nós não a autorizamos."),
    ("es", "¿Cuál es el estado del cargo de Tienda Demo? No he autorizado esa compra."),
    ("es", "¿Cuál es el estado del cargo de Tienda Demo? No fui yo quien lo autorizó."),
    ("es", "¿Cuál es el estado del cargo de Tienda Demo? Yo no lo he realizado."),
    ("pt", "Qual é o status da Tienda Demo? Não fui eu quem autorizou a compra."),
    ("pt", "Qual é o estado da cobrança da Tienda Demo? Nunca a tinha autorizado."),
    ("es", "¿Cuál es el estado del cargo de Tienda Demo? Nunca lo habíamos realizado."),
] + PAST_AND_SELF_DENIAL_REPORTS

UNKNOWN_DENIAL_REPORTS = [
    ("es", "¿Cuál es el estado del cargo de Tienda Demo? No di mi consentimiento para esa compra."),
    ("pt", "Qual é o status da cobrança da Tienda Demo? Não dei meu consentimento para a compra."),
]


@pytest.mark.parametrize("language,message", NEGATED_REPORTS + [UNKNOWN_DENIAL_REPORTS[1]])
def test_fact_question_with_negated_recognition_proposes_and_preserves_confirmed_report(
    tmp_path, language, message
):
    app = create_app(str(tmp_path / "negation.sqlite"), enable_external=False)
    with TestClient(app) as client:
        auth = client.post("/api/session", json={"persona": "customer_es"}).json()
        client.headers["X-CSRF-Token"] = auth["csrf_token"]
        if language == "es":
            greeting = client.post(
                "/api/chat", json={"message": "Olá.", "idempotency_key": str(uuid4())}
            ).json()
            assert greeting["language"] == "pt"
        key = str(uuid4())
        request = {"message": message, "idempotency_key": key}
        response = client.post("/api/chat", json=request)
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["language"] == language
        if authorization_polarity(message) == "negated":
            assert "customer_reported_dispute" in safety_signals(message)
        else:
            # A learned dispute with unresolved negation must also retain review.
            assert classify(message, language)["intent"] == "dispute"
        assert result["intent"] == "dispute" and result["state"] == "awaiting_confirmation"
        assert result["receipt"] is None
        proposal = result["proposal"]
        assert proposal["transaction"]["id"] == "TX-ES-102"
        assert proposal["transaction"]["currency"] == "COP"
        assert proposal["customer_report"] == message
        assert client.get("/api/cases").json()["cases"] == []
        assert client.post("/api/chat", json=request).json() == result
        confirmed = client.post(
            "/api/actions/confirm",
            json={"proposal_id": proposal["id"], "idempotency_key": str(uuid4())},
        )
        assert confirmed.status_code == 200
        receipt = confirmed.json()["receipt"]
        assert receipt["verified"]
        saved = client.get("/api/cases/" + receipt["id"]).json()
        assert saved["intent"] == "dispute" and saved["customer_report"] == message
        assert saved["transaction"]["id"] == "TX-ES-102"


@pytest.mark.parametrize(
    "language,message",
    [
        (
            "es",
            "Quiero ver la información de la transferencia de Tienda Demo que sí autoricé.",
        ),
        (
            "pt",
            "Quero ver as informações da transferência da Tienda Demo que eu autorizei.",
        ),
        ("es", "No tengo dudas: reconozco el cargo de Tienda Demo. Dime el importe."),
        ("pt", "Não tenho dúvida; reconheço a cobrança da Tienda Demo. Qual é o valor?"),
        ("es", "¿Cuál es el estado del cargo de Tienda Demo? Sí he autorizado esa compra."),
        ("pt", "Qual é o status da cobrança da Tienda Demo? Fui eu quem autorizou a compra."),
        (
            "es",
            "No tengo dudas; fui yo quien lo autorizó. Dime el importe del cargo de Tienda Demo.",
        ),
        ("pt", "Não tenho dúvidas; tinha autorizado a cobrança da Tienda Demo. Qual é o valor?"),
        ("es", "No tengo dudas: reconocí el cargo de Tienda Demo. Dime el importe."),
        ("pt", "Não tenho dúvidas; reconheci a cobrança da Tienda Demo. Qual é o valor?"),
        ("pt", "No meu registro consta a compra da Tienda Demo que reconheci. Qual é o valor?"),
        ("es", "No fui yo al banco; reconozco el cargo de Tienda Demo. Dime el importe."),
        ("pt", "Não fui eu ao banco; reconheço a cobrança da Tienda Demo. Qual é o valor?"),
    ],
)
def test_affirmed_recognition_with_unrelated_negation_remains_factual(language, message):
    result = run(message, language, None, {}, transactions("demo-es"), classify)
    assert "customer_reported_dispute" not in safety_signals(message)
    assert result["intent"] == "transaction_status" and result["state"] == "resolved"
    assert result["transaction"]["id"] == "TX-ES-102"
    assert not result.get("proposal_payload") and not result.get("receipt")


@pytest.mark.parametrize("predicted", ["transaction_status", "dispute"])
@pytest.mark.parametrize(
    "language,message",
    [NEGATED_REPORTS[0], NEGATED_REPORTS[5], NEGATED_REPORTS[10], NEGATED_REPORTS[13]]
    + PAST_AND_SELF_DENIAL_REPORTS[:4],
)
def test_service_polarity_guard_does_not_depend_on_classifier_signal_quality(
    predicted, language, message
):
    result = run(
        message,
        language,
        None,
        {},
        transactions("demo-es"),
        lambda *args: {"intent": predicted, "signals": []},
    )
    assert result["intent"] == "dispute" and result["state"] == "awaiting_confirmation"
    assert result["proposal_payload"]["customer_report"] == message
    assert not result.get("receipt")


@pytest.mark.parametrize("language,message", UNKNOWN_DENIAL_REPORTS)
@pytest.mark.parametrize("signals", [[], ["unrelated_classifier_advisory"]])
def test_unresolved_negative_report_cannot_erase_a_learned_dispute(language, message, signals):
    assert authorization_polarity(message) is None
    result = run(
        message,
        language,
        None,
        {},
        transactions("demo-es"),
        lambda *args: {"intent": "dispute", "signals": signals},
    )
    assert result["intent"] == "dispute" and result["state"] == "awaiting_confirmation"
    assert result["transaction"]["id"] == "TX-ES-102"
    assert result["proposal_payload"]["customer_report"] == message
    assert not result.get("receipt")


def test_portuguese_preposition_no_does_not_negate_a_factual_question():
    message = "Qual situação consta no meu registro para a cobrança da Tienda Demo?"
    result = run(
        message,
        "pt",
        None,
        {},
        transactions("demo-es"),
        lambda *args: {"intent": "dispute", "signals": []},
    )
    assert result["intent"] == "transaction_status" and result["state"] == "resolved"
    assert result["transaction"]["id"] == "TX-ES-102"
    assert not result.get("proposal_payload") and not result.get("receipt")


def test_spanish_unresolved_denial_retains_review_after_portuguese_context():
    message = UNKNOWN_DENIAL_REPORTS[0][1]
    result = run(
        message,
        "pt",
        None,
        {},
        transactions("demo-es"),
        lambda *args: {"intent": "dispute", "signals": []},
    )
    assert result["intent"] == "dispute" and result["state"] == "awaiting_confirmation"
    assert result["proposal_payload"]["customer_report"] == message
    assert not result.get("receipt")


@pytest.mark.parametrize(
    "language,message",
    [
        (
            "es",
            "¿Por qué figura el cargo de Tienda Demo? Sí hice otro pago, pero no lo reconozco.",
        ),
        (
            "pt",
            "Qual é o status da Tienda Demo? Fiz outro pagamento, mas não a reconheço.",
        ),
    ],
)
def test_one_affirmed_verb_does_not_erase_a_separate_dispute(language, message):
    result = run(message, language, None, {}, transactions("demo-es"), classify)
    assert result["intent"] == "dispute" and result["state"] == "awaiting_confirmation"
    assert result["proposal_payload"]["customer_report"] == message


def test_scam_signal_retains_priority_when_recognition_is_also_negated():
    message = "¿Por qué figura el cargo de Tienda Demo? No lo reconozco y me piden mi contraseña."
    assert "customer_reported_scam" in safety_signals(message)
    result = run(message, "es", None, {}, transactions("demo-es"), classify)
    assert result["intent"] == "scam" and result["state"] == "awaiting_confirmation"
    assert not result.get("receipt")


@pytest.mark.parametrize("message,language", [("No fui yo.", "es"), ("Não fui eu.", "pt")])
def test_bare_self_denial_clarifies_then_preserves_the_report_through_verified_case(
    tmp_path, message, language
):
    app = create_app(str(tmp_path / "self-denial.sqlite"), enable_external=False)
    with TestClient(app) as client:
        auth = client.post("/api/session", json={}).json()
        client.headers["X-CSRF-Token"] = auth["csrf_token"]
        if language == "es":
            greeting = client.post(
                "/api/chat", json={"message": "Olá.", "idempotency_key": str(uuid4())}
            ).json()
            assert greeting["language"] == "pt"
        first = client.post(
            "/api/chat", json={"message": message, "idempotency_key": str(uuid4())}
        ).json()
        assert first["language"] == language
        assert first["intent"] == "dispute" and first["state"] == "clarification"
        assert first["proposal"] is None and first["receipt"] is None
        selected = client.post(
            "/api/chat", json={"message": "TX-ES-102", "idempotency_key": str(uuid4())}
        ).json()
        assert selected["state"] == "awaiting_confirmation"
        assert selected["proposal"]["customer_report"] == message
        assert selected["proposal"]["transaction"]["id"] == "TX-ES-102"
        confirmed = client.post(
            "/api/actions/confirm",
            json={"proposal_id": selected["proposal"]["id"], "idempotency_key": str(uuid4())},
        ).json()
        assert confirmed["receipt"]["verified"]
        saved = client.get("/api/cases/" + confirmed["receipt"]["id"]).json()
        assert saved["customer_report"] == message and saved["intent"] == "dispute"

"""Late hosted QA regressions; these cases do not modify the frozen corpora."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from factored_banking.api import create_app
from factored_banking.fixtures import transactions
from factored_banking.language import classify
from factored_banking.workflow import run


@pytest.mark.parametrize(
    "original,clarification,selected",
    [
        (
            "No reconozco el cobro de Mercado Luna.",
            "A primeira ou a segunda. Meu cartão ficou comigo e eu estava em casa.",
            "É o cobro de Tienda Demo, 129000 COP. Meu cartão ficou comigo e eu estava em casa.",
        ),
        (
            "Não reconheço a cobrança de Mercado Luna.",
            "La primera o la segunda. Mi tarjeta se quedó conmigo y yo estaba en casa.",
            "Es el cobro de Tienda Demo, 129000 COP. Mi tarjeta se quedó conmigo.",
        ),
    ],
)
def test_ambiguous_selection_keeps_pending_report_through_preview_retry_and_storage(
    tmp_path, original, clarification, selected
):
    app = create_app(str(tmp_path / "continuation.sqlite"), enable_external=False)
    with TestClient(app) as client:
        auth = client.post("/api/session", json={}).json()
        client.headers["X-CSRF-Token"] = auth["csrf_token"]

        def chat(message, key=None):
            response = client.post(
                "/api/chat", json={"message": message, "idempotency_key": key or str(uuid4())}
            )
            assert response.status_code == 200, response.text
            return response.json()

        first = chat(original)
        assert first["state"] == "clarification" and first["intent"] == "dispute"
        middle = chat(clarification)
        assert middle["state"] == "clarification" and middle["intent"] == "dispute"
        assert {row["id"] for row in middle["transaction_options"]} == {"TX-ES-101", "TX-ES-102"}
        assert middle.get("transaction") is None
        context = client.get("/api/session").json()["context"]
        assert context["pending_intent"] == "dispute"
        assert original in context["customer_report"]
        assert clarification in context["customer_report"]
        assert not middle.get("proposal") and not middle.get("receipt")
        assert client.get("/api/cases").json()["cases"] == []

        key = str(uuid4())
        proposed = chat(selected, key)
        assert proposed["state"] == "awaiting_confirmation" and proposed["intent"] == "dispute"
        proposal = proposed["proposal"]
        assert proposal["transaction"]["id"] == "TX-ES-102"
        report = proposal["customer_report"]
        assert original in report and clarification in report and selected in report
        assert chat(selected, key) == proposed
        assert client.get("/api/session").json()["proposal"]["customer_report"] == report
        assert client.get("/api/cases").json()["cases"] == []
        confirmed = client.post(
            "/api/actions/confirm",
            json={"proposal_id": proposal["id"], "idempotency_key": str(uuid4())},
        )
        assert confirmed.status_code == 200
        receipt = confirmed.json()["receipt"]
        assert receipt["verified"]
        saved = client.get("/api/cases/" + receipt["id"]).json()
        assert saved["customer_report"] == report
        assert saved["transaction"]["id"] == "TX-ES-102"


@pytest.mark.parametrize(
    "language,original,ambiguous,factual",
    [
        (
            "es",
            "No reconozco el cobro de Mercado Luna.",
            "La primera o la segunda. Mi tarjeta se quedó conmigo y yo estaba en casa.",
            "Ahora dime el estado del cargo de Tienda Demo.",
        ),
        (
            "pt",
            "Não reconheço a cobrança de Mercado Luna.",
            "A primeira ou a segunda. Meu cartão ficou comigo e eu estava em casa.",
            "Agora diga o estado da cobrança de Tienda Demo.",
        ),
    ],
)
def test_explicit_new_fact_request_replaces_pending_dispute_after_ambiguity(
    language, original, ambiguous, factual
):
    records = transactions("demo-es")
    first = run(original, language, None, {}, records, classify)
    middle = run(ambiguous, language, None, first["context"], records, classify)
    assert middle["state"] == "clarification" and middle["context"]["pending_intent"] == "dispute"
    assert {row["id"] for row in middle["transaction_options"]} == {"TX-ES-101", "TX-ES-102"}
    assert "transaction" not in middle
    changed = run(factual, language, None, middle["context"], records, classify)
    assert changed["state"] == "resolved" and changed["intent"] == "transaction_status"
    assert changed["transaction"]["id"] == "TX-ES-102"
    assert original not in changed["customer_report"]
    assert not changed.get("proposal_payload") and not changed.get("receipt")


def test_new_scam_signal_keeps_priority_over_a_pending_dispute():
    records = transactions("demo-es")
    first = run("No reconozco el cobro de Mercado Luna.", "es", None, {}, records, classify)
    next_turn = run(
        "Me pidieron mi OTP para cancelar el cargo de Tienda Demo.",
        "es",
        None,
        first["context"],
        records,
        classify,
    )
    assert next_turn["intent"] == "scam" and next_turn["state"] == "awaiting_confirmation"
    assert next_turn["proposal_payload"]["intent"] == "scam"
    assert not next_turn.get("receipt")

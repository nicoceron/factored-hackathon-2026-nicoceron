"""Developer-authored final-review checks; frozen evaluation corpora stay unchanged."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from factored_banking.api import create_app
from factored_banking.fixtures import transactions
from factored_banking.privacy import REPORT_LIMIT, customer_report
from factored_banking.references import resolve_reference


@pytest.mark.parametrize(
    "message",
    [
        "Foi a de segunda-feira",
        "Espera un segundo",
        "Es la primera vez que veo ese cobro",
        "Fue el primero de junio",
        "Não foi a segunda transação",
    ],
)
def test_ordinary_or_negated_ordinals_never_select_an_option(message):
    rows = transactions("demo-es")
    ref = resolve_reference(message, {"transaction_candidates": [r["id"] for r in rows]}, rows)
    assert not ref.selection_only
    assert len(ref.candidates) != 1


@pytest.mark.parametrize(
    "message",
    [
        "La segunda",
        "a segunda",
        "la segunda transacción",
        "foi a segunda",
        "opción segunda",
        "El segundo movimiento fue después de la llamada",
    ],
)
def test_affirmative_ordinals_use_the_displayed_order(message):
    rows = transactions("demo-es")
    ref = resolve_reference(message, {"transaction_candidates": [r["id"] for r in rows]}, rows)
    assert [r["id"] for r in ref.candidates] == ["TX-ES-102"]


def test_redacted_report_merge_is_bounded_and_retains_latest_details():
    report = customer_report(
        "Después de una llamada. Mi PIN es １２３４.",
        {"customer_report": "No reconozco este cargo. " * 100},
        continuation=True,
    )
    assert len(report) <= REPORT_LIMIT
    assert "No reconozco" in report and "Después de una llamada" in report
    assert "１２３４" not in report and "1234" not in report and "[REDACTED]" in report
    assert (
        customer_report(
            "la segunda",
            {"customer_report": "No reconozco el cargo."},
            continuation=True,
            selection_only=True,
        )
        == "No reconozco el cargo."
    )
    assert (
        customer_report(
            "Otro asunto", {"customer_report": "No reconozco el cargo."}, continuation=False
        )
        == "Otro asunto"
    )


def test_followup_report_is_previewed_then_stored_without_losing_the_original(tmp_path):
    app = create_app(str(tmp_path / "review.sqlite"), enable_external=False)
    with TestClient(app) as client:
        auth = client.post("/api/session", json={}).json()
        client.headers["X-CSRF-Token"] = auth["csrf_token"]

        def say(message):
            result = client.post(
                "/api/chat", json={"message": message, "idempotency_key": str(uuid4())}
            )
            assert result.status_code == 200, result.text
            return result.json()

        first = say("No reconozco un cargo")
        assert first["state"] == "clarification"
        second = say(
            "El de Tienda Demo, fue después de una llamada. Mi correo es ejemplo@example.test"
        )
        assert second["state"] == "awaiting_confirmation"
        proposal = second["proposal"]
        assert "No reconozco un cargo" in proposal["customer_report"]
        assert "después de una llamada" in proposal["customer_report"]
        assert "ejemplo@example.test" not in proposal["customer_report"]
        confirmed = client.post(
            "/api/actions/confirm",
            json={"proposal_id": proposal["id"], "idempotency_key": str(uuid4())},
        )
        assert confirmed.status_code == 200 and confirmed.json()["receipt"]["verified"]
        case = client.get("/api/cases/" + confirmed.json()["receipt"]["id"]).json()
        assert case["customer_report"] == proposal["customer_report"]
        assert case["transaction"]["id"] == "TX-ES-102"

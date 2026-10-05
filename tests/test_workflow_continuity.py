"""Developer regression from the hosted ES/PT clarification walkthrough; not a blind set."""

import pytest
from fastapi.testclient import TestClient

from factored_banking.api import create_app
from factored_banking.fixtures import transactions
from factored_banking.language import classify
from factored_banking.system_evaluation import chat, grounded_transaction, login
from factored_banking.workflow import run


@pytest.mark.parametrize(
    ("language", "initial_message", "selection"),
    [
        ("es", "Quiero consultar el estado de este movimiento.", "Esa operación"),
        ("pt", "Quero consultar o estado desta transação.", "Essa transação"),
    ],
)
def test_live_model_deictic_reply_completes_pending_status(
    tmp_path, language, initial_message, selection
):
    app = create_app(str(tmp_path / "state.sqlite"), secure_cookies=False)
    with TestClient(app) as client:
        login(client, language)
        first = chat(client, initial_message, language, "continuity-first").json()
        assert first["state"] == "clarification"
        assert (
            client.get("/api/session").json()["context"]["pending_intent"] == "transaction_status"
        )
        selected = client.get("/api/transactions").json()["transactions"][1]
        result = chat(client, selection, language, "continuity-select", selected["id"]).json()
        assert result["intent"] == "transaction_status"
        assert result["state"] == "resolved"
        assert grounded_transaction(result, selected)
        assert result["proposal"] is None and result["receipt"] is None
        assert client.get("/api/cases").json()["cases"] == []


@pytest.mark.parametrize(
    ("language", "selection"),
    [
        ("es", "Esa operación"),
        ("es", "ESTA TRANSACCIÓN."),
        ("es", "Ese movimiento"),
        ("es", "esa"),
        ("pt", "Essa transação"),
        ("pt", "AQUELA OPERAÇÃO."),
        ("pt", "Esse pagamento"),
        ("pt", "essa"),
    ],
)
@pytest.mark.parametrize("pending", ["transaction_status", "dispute"])
def test_short_selection_preserves_pending_task_despite_model_label(language, selection, pending):
    records = transactions(f"demo-{language}")
    result = run(
        selection,
        language,
        records[0]["id"],
        {"pending_intent": pending},
        records,
        lambda *args: {"intent": "unsupported", "signals": []},
    )
    assert result["intent"] == pending
    assert result["transaction"]["id"] == records[0]["id"]
    assert result["state"] == (
        "resolved" if pending == "transaction_status" else "awaiting_confirmation"
    )
    assert result["receipt"] is None


@pytest.mark.parametrize("language", ["es", "pt"])
@pytest.mark.parametrize("pending", ["transaction_status", "dispute"])
def test_rejected_amount_preserves_pending_task_before_early_clarification(language, pending):
    records = transactions(f"demo-{language}")
    record = records[1]
    message = ("No la de " if language == "es" else "Não a de ") + record["amount"] + "."
    result = run(
        message,
        language,
        None,
        {
            "pending_intent": pending,
            "transaction_candidates": [row["id"] for row in records],
        },
        records,
        lambda *args: {"intent": "dispute", "signals": []},
    )
    assert result["state"] == "clarification"
    assert result["intent"] == result["context"]["pending_intent"] == pending
    assert not result.get("transaction") and not result.get("proposal_payload")
    assert result["receipt"] is None


@pytest.mark.parametrize(
    ("language", "message", "intent", "state"),
    [
        ("es", "No autoricé esa operación", "dispute", "awaiting_confirmation"),
        ("pt", "Não autorizei essa transação", "dispute", "awaiting_confirmation"),
        ("es", "Un falso asesor me exige cancelar esa operación", "scam", "awaiting_confirmation"),
        (
            "pt",
            "Um falso assessor me exige cancelar essa transação",
            "scam",
            "awaiting_confirmation",
        ),
        (
            "es",
            "Quiero hablar con una persona sobre esa operación",
            "human",
            "awaiting_confirmation",
        ),
        ("pt", "Quero falar com uma pessoa sobre essa transação", "human", "awaiting_confirmation"),
        ("es", "cancelar", "unsupported", "cancelled"),
        ("pt", "cancele", "unsupported", "cancelled"),
    ],
)
def test_new_explicit_request_keeps_priority_over_pending_status(language, message, intent, state):
    records = transactions(f"demo-{language}")
    result = run(
        message,
        language,
        records[0]["id"],
        {"pending_intent": "transaction_status"},
        records,
        classify,
    )
    assert result["intent"] == intent
    assert result["state"] == state
    assert result["receipt"] is None


@pytest.mark.parametrize("selection", ["Essa transação", "TX-PT-102"])
@pytest.mark.parametrize(
    ("signal", "expected"),
    [
        ("model_unavailable", "human"),
        ("customer_reported_scam", "scam"),
        ("customer_reported_dispute", "dispute"),
        ("explicit_human_request", "human"),
    ],
)
def test_selection_cannot_override_review_safety_signal(selection, signal, expected):
    result = run(
        selection,
        "pt",
        "TX-PT-102",
        {"pending_intent": "transaction_status"},
        transactions("demo-pt"),
        lambda *args: {"intent": "ambiguous", "signals": [signal]},
    )
    assert result["intent"] == expected
    assert result["state"] == "awaiting_confirmation"


def test_deictic_reply_does_not_invent_selection_or_authorize_foreign_record():
    records = transactions("demo-pt")

    def classifier(*args):
        return {"intent": "unsupported", "signals": []}

    context = {"pending_intent": "transaction_status"}
    missing = run("Essa transação", "pt", None, context, records, classifier)
    assert missing["state"] == "clarification"
    assert missing["context"]["pending_intent"] == context["pending_intent"]
    assert missing["context"]["customer_report"] == "Essa transação"
    assert "transaction" not in missing
    foreign = run("Essa transação", "pt", "TX-ES-101", context, records, classifier)
    assert foreign["state"] == "blocked"
    assert "transaction" not in foreign
    fresh = run("Essa transação", "pt", records[0]["id"], {}, records, classifier)
    assert fresh["intent"] == "unsupported" and fresh["state"] == "abstained"


def test_deictic_prefix_cannot_turn_new_unsupported_request_into_status():
    result = run(
        "Essa transação, transfira o dinheiro para outra conta",
        "pt",
        "TX-PT-102",
        {"pending_intent": "transaction_status"},
        transactions("demo-pt"),
        lambda *args: {"intent": "unsupported", "signals": []},
    )
    assert result["intent"] == "unsupported" and result["state"] == "abstained"

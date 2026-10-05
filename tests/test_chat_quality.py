"""Chat-only regressions: natural references, locale and scoped case facts.

These developer-authored checks are not additions to frozen benchmark denominators.
"""

import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from factored_banking.api import create_app
from factored_banking.fixtures import transactions


@pytest.fixture
def system(tmp_path, monkeypatch):
    monkeypatch.setenv("CLARO_PROVIDER_BUDGET_DB", str(tmp_path / "ai.sqlite"))
    app = create_app(str(tmp_path / "chat.sqlite"), enable_external=False)
    with TestClient(app) as client:
        login(client)
        yield app, client


def login(client, persona="customer_es"):
    response = client.post("/api/session", json={"persona": persona})
    assert response.status_code == 200
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]


def chat(client, message, key):
    response = client.post("/api/chat", json={"message": message, "idempotency_key": key})
    assert response.status_code == 200, response.text
    return response.json()


def create_case(client, key="create-human-case"):
    result = chat(client, "Quiero hablar con una persona.", key)
    response = client.post(
        "/api/actions/confirm",
        json={"proposal_id": result["proposal"]["id"], "idempotency_key": key + "-confirm"},
    )
    assert response.status_code == 200 and response.json()["receipt"]["verified"]
    return response.json()["receipt"]["id"]


def test_auto_locale_switch_preserves_authenticated_customer_and_exact_evidence(system):
    _, client = system
    portuguese = chat(
        client, "Qual é o estado do pagamento na Tienda Demo?", "natural-portuguese-lookup"
    )
    spanish = chat(client, "¿Cuál es el estado del pago en Mercado Demo?", "natural-spanish-lookup")
    for result, locale, identifier, amount in (
        (portuguese, "pt", "TX-ES-102", "129000.00"),
        (spanish, "es", "TX-ES-101", "84000.00"),
    ):
        assert result["language"] == locale and result["state"] == "resolved"
        assert result["transaction"] == next(
            row for row in transactions("demo-es") if row["id"] == identifier
        )
        assert identifier in result["message"] and amount in result["message"]
        assert "COP" in result["message"] and "2026-06-17" in result["message"]
        assert any(e["id"] == identifier for e in result["evidence"])
        assert result.get("receipt") is None and result.get("proposal") is None
    assert client.get("/api/transactions").json()["transactions"] == transactions("demo-es")


@pytest.mark.parametrize(
    ("question", "selection", "locale"),
    [
        ("¿Cuál es el estado de una transacción?", "la segunda", "es"),
        ("Qual é o estado de uma transação?", "a segunda", "pt"),
    ],
)
def test_pending_status_resolves_natural_ordinal_without_a_transaction_field(
    system, question, selection, locale
):
    _, client = system
    first = chat(client, question, "ordinal-status-question")
    assert first["state"] == "clarification" and len(first["transaction_options"]) == 3
    second = chat(client, selection, "ordinal-status-selection")
    assert second["language"] == locale and second["state"] == "resolved"
    assert second["intent"] == "transaction_status" and second["transaction"]["id"] == "TX-ES-102"
    assert second.get("proposal") is None and second.get("receipt") is None


def test_dispute_merchant_reply_retains_original_report_and_waits_for_confirmation(system):
    _, client = system
    report = "Não reconheço uma cobrança que apareceu duas vezes."
    first = chat(client, report, "dispute-original-report")
    assert first["state"] == "clarification"
    selected = chat(client, "a da Tienda Demo", "dispute-natural-merchant")
    assert selected["language"] == "pt" and selected["state"] == "awaiting_confirmation"
    assert selected["transaction"]["id"] == "TX-ES-102"
    assert report in selected["proposal"]["customer_report"]
    assert selected.get("receipt") is None
    assert client.get("/api/cases").json()["cases"] == []


def test_duplicate_merchant_never_silently_selects_a_record(system):
    _, client = system
    records = transactions("demo-es")
    records[1]["merchant"] = records[0]["merchant"]
    with patch("factored_banking.api.transactions", return_value=records):
        result = chat(
            client, "¿Cuál es el estado del pago en Mercado Demo?", "ambiguous-merchant-lookup"
        )
    assert result["state"] == "clarification"
    assert result.get("transaction") is None and result.get("proposal") is None
    assert {row["id"] for row in result["transaction_options"]} == {"TX-ES-101", "TX-ES-102"}


@pytest.mark.parametrize(
    "question",
    [
        "¿Este débito está registrado como rechazado?",
        "Este débito está registrado como recusado?",
        "Necesito entender por qué esta operación figura rechazada; dime solo lo que conste.",
        "Preciso entender por que esta operação aparece recusada; diga apenas o que consta.",
        "La notificación llegó ayer: ¿el pago ya aparece completado o todavía pendiente?",
        "A notificação chegou ontem: o pagamento já aparece concluído ou ainda pendente?",
        "¿Mi pago sigue pendiente?",
        "O meu pagamento continua pendente?",
        "¿Mi pago se completó o sigue pendiente?",
        "La tienda dice que pagué; necesito revisar el registro de la compra.",
    ],
)
def test_queried_status_or_generic_shop_word_does_not_identify_an_unnamed_record(system, question):
    _, client = system
    result = chat(client, question, "unidentified-record-status")
    assert result["state"] == "clarification"
    assert result.get("transaction") is None and result.get("proposal") is None
    assert len(result["transaction_options"]) == 3


def test_customer_report_of_incorrect_amount_keeps_dispute_route_during_clarification(system):
    _, client = system
    report = (
        "O recibo da loja e o valor debitado não coincidem; quero registrar a cobrança incorreta."
    )
    first = chat(client, report, "reported-incorrect-amount")
    assert first["state"] == "clarification" and first["intent"] == "dispute"
    selected = chat(client, "o primeiro", "reported-incorrect-amount-selection")
    assert selected["state"] == "awaiting_confirmation" and selected["intent"] == "dispute"
    assert report in selected["proposal"]["customer_report"] and selected.get("receipt") is None


def test_foreign_explicit_transaction_is_denied_even_with_authorized_merchant_hint(system):
    _, client = system
    result = chat(
        client,
        "¿Cuál es el estado del pago TX-PT-101 en Mercado Demo?",
        "foreign-transaction-natural-reference",
    )
    assert result["state"] == "blocked"
    assert result.get("transaction") is None and result.get("proposal") is None
    assert result.get("receipt") is None


def test_case_chat_reads_scoped_persisted_status_and_specific_pending_question(system):
    _, client = system
    identifier = create_case(client)
    login(client, "analyst")
    question = "¿Los dos cargos tienen la misma fecha?"
    requested = client.post(
        f"/api/cases/{identifier}/resolve",
        json={
            "resolution": "needs_information",
            "question": question,
            "idempotency_key": "analyst-specific-question",
        },
    )
    assert requested.status_code == 200 and requested.json()["receipt"]["verified"]
    login(client)
    result = chat(client, f"¿Cuál es el estado del caso {identifier}?", "case-chat-readback")
    assert result["state"] == "case_lookup" and len(result["cases"]) == 1
    case = result["cases"][0]
    assert case["id"] == identifier and case["status"] == "needs_information"
    assert case["pending_question"]["text"] == question and case["history_complete"]
    assert identifier in result["message"] and question in result["message"]
    assert result.get("proposal") is None and result.get("receipt") is None


def test_foreign_case_mention_cannot_disclose_owned_or_foreign_case_details(system):
    app, client = system
    owned = create_case(client)
    with TestClient(app) as outsider:
        login(outsider)
        foreign = create_case(outsider)
    result = chat(client, f"¿Cuál es el estado del caso {foreign}?", "foreign-case-chat-lookup")
    assert result["state"] == "blocked" and not result.get("cases")
    assert owned not in result["message"] and foreign not in result["message"]
    assert result.get("proposal") is None and result.get("receipt") is None


@pytest.mark.parametrize("message", ["Lo de antes sigue igual.", "O de antes continua igual."])
def test_unanchored_prior_reference_clarifies_even_with_saved_cases(system, message):
    _, client = system
    create_case(client)
    assert client.post("/api/conversation/reset").status_code == 200
    result = chat(client, message, "unanchored-existing-case-reference")
    assert result["state"] == "clarification" and not result.get("cases")
    assert result.get("transaction") is None and result.get("receipt") is None
    assert result.get("proposal") is None


def test_anchored_prior_case_reference_reads_the_same_persisted_case(system):
    _, client = system
    identifier = create_case(client)
    lookup = chat(client, f"¿Cuál es el estado del caso {identifier}?", "anchor-specific-case")
    assert lookup["state"] == "case_lookup" and lookup["cases"][0]["id"] == identifier
    continued = chat(client, "Lo de antes sigue igual.", "anchored-case-reference")
    assert continued["state"] == "case_lookup"
    assert len(continued["cases"]) == 1 and continued["cases"][0]["id"] == identifier
    assert continued.get("proposal") is None and continued.get("receipt") is None


def test_chat_retry_is_identical_and_has_one_event_and_no_provider_attempts(system):
    app, client = system
    message = "Qual é o estado do pagamento na Tienda Demo?"
    first = chat(client, message, "natural-chat-idempotent")
    again = chat(client, message, "natural-chat-idempotent")
    assert first == again
    with app.state.store.connect() as db:
        assert db.execute("SELECT count(*) FROM events WHERE event='chat'").fetchone()[0] == 1
    assert app.state.ai.usage_since(0)["attempts"] == 0


def test_redacted_secret_cannot_enter_persisted_conversation_history(system):
    app, client = system
    result = chat(
        client,
        "Me pidieron mi OTP 87654321 para cancelar el cargo en Mercado Demo",
        "chat-history-secret-redaction",
    )
    assert result["state"] == "awaiting_confirmation"
    with app.state.store.connect() as db:
        state = json.loads(db.execute("SELECT state FROM sessions").fetchone()[0])
    assert "87654321" not in json.dumps(state)
    assert "[REDACTED]" in json.dumps(state)

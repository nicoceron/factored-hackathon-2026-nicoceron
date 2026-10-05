"""Authored conversational regressions; these do not form a new blind benchmark."""

import json

import pytest
from fastapi.testclient import TestClient

from factored_banking.api import create_app
from factored_banking.fixtures import transactions
from factored_banking.language import classify, detect_language
from factored_banking.workflow import run


@pytest.mark.parametrize(
    "message,expected",
    [
        ("¿Cuál es el estado del cargo de Tienda Demo?", "TX-ES-102"),
        ("¿Cuál es el importe de la operación por 84.000 COP?", "TX-ES-101"),
        ("Quero saber o estado da cobrança pendente", "TX-ES-102"),
        ("¿Cuál es el estado de la operación del 2026-06-15?", "TX-ES-103"),
    ],
)
def test_natural_fact_questions_use_exact_authorized_evidence(message, expected):
    records = transactions("demo-es")
    result = run(message, detect_language(message), None, {}, records, classify)
    assert result["state"] == "resolved"
    assert result["transaction"]["id"] == expected
    actual = next(row for row in records if row["id"] == expected)
    assert result["transaction"]["amount"] == actual["amount"]
    assert actual["currency"] in result["message"]
    assert result["evidence"][0]["source"] == actual["source"]
    assert result["proposal"] is None and result["receipt"] is None


@pytest.mark.parametrize(
    "message",
    [
        "¿Cuál es el estado del cargo de Comercio Inexistente?",
        "¿Cuál es el estado del cargo en Comercio Inexistente?",
        "¿Cuál es el estado del cargo por 999999 COP?",
        "¿Cuál es el estado de TX-ES-101 por 129000 COP?",
        "La primera o la segunda",
    ],
)
def test_new_conflicting_reference_cannot_reuse_old_record(message):
    records = transactions("demo-es")
    context = {
        "transaction_id": "TX-ES-101",
        "pending_intent": "transaction_status",
        "transaction_candidates": [row["id"] for row in records],
    }
    result = run(message, "es", None, context, records, classify)
    assert result["state"] == "clarification"
    assert "transaction" not in result
    assert result["transaction_options"]
    assert result["receipt"] is None


def test_numeric_notation_with_two_possible_exact_amounts_stays_ambiguous():
    original = transactions("demo-es")[0]
    records = [original, {**original, "id": "AUTH-19", "amount": "84.00"}]
    result = run("El cargo de 84.000 COP", "es", None, {}, records, classify)
    assert result["state"] == "clarification"
    assert len(result["transaction_options"]) == 2
    assert "transaction" not in result


@pytest.mark.parametrize(
    "message,locale",
    [
        ("¿Este débito está registrado como rechazado?", "es"),
        ("Esse débito está registrado como recusado?", "pt"),
        ("La tienda dice que pagué; necesito revisar el registro de la compra.", "es"),
        ("¿Por qué esta operación figura rechazada?", "es"),
        ("Por que esta operação aparece recusada?", "pt"),
        ("¿Mi pago sigue pendiente?", "es"),
        ("O meu pagamento continua pendente?", "pt"),
        ("¿Mi pago se completó o sigue pendiente?", "es"),
        ("O pagamento já foi concluído ou continua pendente?", "pt"),
    ],
)
def test_queried_status_or_generic_establishment_is_not_a_unique_reference(message, locale):
    result = run(message, locale, None, {}, transactions("demo-es"), classify)
    assert result["state"] == "clarification"
    assert "transaction" not in result
    assert len(result["transaction_options"]) == 3


@pytest.mark.parametrize(
    "message,locale",
    [
        ("la operación pendiente", "es"),
        ("a transação pendente", "pt"),
        ("la pendiente", "es"),
        ("a pendente", "pt"),
    ],
)
def test_affirmative_status_locator_identifies_scoped_record(message, locale):
    context = {"pending_intent": "transaction_status"}
    result = run(message, locale, None, context, transactions("demo-es"), classify)
    assert result["state"] == "resolved"
    assert result["transaction"]["id"] == "TX-ES-102"


@pytest.mark.parametrize("message,locale", [("pendiente", "es"), ("pendente", "pt")])
def test_bare_status_reply_refers_only_to_previously_offered_candidates(message, locale):
    records = transactions("demo-es")
    context = {
        "pending_intent": "transaction_status",
        "transaction_candidates": [row["id"] for row in records],
    }
    result = run(message, locale, None, context, records, classify)
    assert result["state"] == "resolved"
    assert result["transaction"]["id"] == "TX-ES-102"


@pytest.mark.parametrize(
    "message,fallback,expected",
    [
        ("Como está meu caso?", "es", "pt"),
        ("¿Cómo va mi caso?", "pt", "es"),
        ("Depois da ligação; não compartilhei nenhuma senha.", "es", "pt"),
        ("Después de la llamada; no compartí ninguna clave.", "pt", "es"),
        ("TX-ES-101", "pt", "pt"),
        ("sí", "pt", "pt"),
        ("a segunda", "pt", "pt"),
    ],
)
def test_clear_language_switches_and_shared_replies(message, fallback, expected):
    assert detect_language(message, fallback) == expected


def test_arbitrary_authorized_tool_id_is_not_a_fixture_mapping():
    original = transactions("demo-es")[0]
    record = {**original, "id": "AUTH-19", "merchant": "Comercio Nuevo", "amount": "71.25"}
    first = run("No reconozco este cargo", "es", None, {}, [record], classify)
    selected = run("AUTH-19", "es", None, first["context"], [record], classify)
    assert selected["state"] == "awaiting_confirmation"
    assert selected["transaction"]["id"] == "AUTH-19"
    assert selected["proposal_payload"]["customer_report"] == "No reconozco este cargo"


@pytest.mark.parametrize("message", ["Hola", "Bom dia!", "Gracias", "Muito obrigada."])
def test_courtesy_only_preserves_context_without_listing_transactions(message):
    context = {"transaction_id": "TX-ES-102", "pending_intent": "transaction_status"}
    result = run(
        message, detect_language(message), None, context, transactions("demo-es"), classify
    )
    assert result["state"] == "resolved"
    assert result["context"] == context
    assert not result.get("transaction_options")
    assert result["proposal"] is None


def test_courtesy_prefix_does_not_hide_a_substantive_dispute():
    result = run(
        "Hola, no reconozco el cargo de Tienda Demo",
        "es",
        None,
        {},
        transactions("demo-es"),
        classify,
    )
    assert result["intent"] == "dispute" and result["state"] == "awaiting_confirmation"


def test_negated_human_request_and_unsupported_action_do_not_create_proposals():
    context = {"transaction_id": "TX-ES-101", "pending_intent": "transaction_status"}
    records = transactions("demo-es")
    result = run(
        "No hables con un asesor todavía; dime el importe del movimiento",
        "es",
        None,
        context,
        records,
        classify,
    )
    assert result["state"] == "resolved" and result["proposal"] is None
    result = run("Transfiere 84000 COP a otra cuenta", "es", None, context, records, classify)
    assert result["state"] == "abstained" and result["proposal"] is None


def test_refresh_restores_pending_proposal_then_the_verified_receipt(tmp_path):
    app = create_app(str(tmp_path / "restore.sqlite"), enable_external=False)
    with TestClient(app) as client:
        session = client.post("/api/session", json={}).json()
        client.headers["X-CSRF-Token"] = session["csrf_token"]
        proposed = client.post(
            "/api/chat",
            json={
                "message": "No reconozco el cargo de Tienda Demo",
                "idempotency_key": "draft-001",
            },
        ).json()
        restored = client.get("/api/session").json()
        assert restored["proposal"]["id"] == proposed["proposal"]["id"]
        assert restored["proposal_evidence"] == proposed["evidence"]
        receipt = client.post(
            "/api/actions/confirm",
            json={"proposal_id": proposed["proposal"]["id"], "idempotency_key": "confirm-001"},
        ).json()
        restored = client.get("/api/session").json()
        assert restored["proposal"] is None
        assert restored["context"]["history"][-1]["content"] == receipt["message"]
        assert restored["context"]["transaction_id"] == "TX-ES-102"
        assert restored["context"]["pending_intent"] == "transaction_status"
        assert receipt["receipt"]["verified"]


def test_bare_amount_mention_in_report_cannot_override_review_intent():
    message = (
        "O recibo da loja e o valor debitado não coincidem; quero registrar a cobrança incorreta."
    )
    result = run(message, "pt", None, {}, transactions("demo-es"), classify)
    assert result["intent"] == "dispute"
    assert result["state"] == "clarification"
    selected = run("a primeira", "pt", None, result["context"], transactions("demo-es"), classify)
    assert selected["intent"] == "dispute"
    assert selected["state"] == "awaiting_confirmation"
    assert selected["proposal_payload"]["customer_report"] == message


def test_session_reports_same_demo_identity_after_language_switch(tmp_path):
    app = create_app(str(tmp_path / "identity.sqlite"), enable_external=False)
    with TestClient(app) as client:
        initial = client.post("/api/session", json={"persona": "customer_es"}).json()
        assert initial["demo_persona"] == "customer_es"
        client.headers["X-CSRF-Token"] = initial["csrf_token"]
        switched = client.post(
            "/api/chat", json={"message": "Como está meu caso?", "idempotency_key": "switch-001"}
        ).json()
        assert switched["language"] == "pt"
        restored = client.get("/api/session").json()
        assert restored["user"]["language"] == "pt"
        assert restored["demo_persona"] == "customer_es"
        renewed = client.post(
            "/api/session", json={"persona": restored["demo_persona"], "language": "pt"}
        ).json()
        assert renewed["demo_persona"] == "customer_es"
        assert client.get("/api/transactions").json()["transactions"][0]["id"] == "TX-ES-101"
        analyst = client.post("/api/session", json={"persona": "analyst"}).json()
        assert analyst["demo_persona"] == "analyst"


def test_current_regressions_are_served_and_historical_artifacts_remain(tmp_path, monkeypatch):
    from factored_banking import api

    resource = tmp_path / "resources"
    resource.mkdir()
    old = {"report_version": "historical"}
    current = {"report_version": "chat-regression"}
    names = {
        "system-evaluation": "chat-system-regression.json",
        "system-challenge-regression": "chat-challenge-regression.json",
        "service-segment-evaluation": "chat-service-segment-regression.json",
    }
    for name, filename in names.items():
        (resource / f"{name}-v2.json").write_text(json.dumps(old))
        (resource / filename).write_text(json.dumps(current))
    monkeypatch.setattr(api, "ROOT", tmp_path)
    app = api.create_app(str(tmp_path / "reports.sqlite"), enable_external=False)
    with TestClient(app) as client:
        response = client.get("/api/evaluation").json()
        for name, filename in names.items():
            assert response["reports"][name] == current
            assert response["report_files"][name] == filename
            assert json.loads((resource / f"{name}-v2.json").read_text()) == old


@pytest.mark.parametrize("locale", ["es", "pt"])
def test_model_case_label_needs_tracking_reference_or_established_context(locale):
    records = transactions("demo-es")

    def classifier(*args):
        return {"intent": "case_status", "signals": []}

    message = "Lo anterior sigue igual." if locale == "es" else "Aquilo continua igual."
    result = run(message, locale, None, {}, records, classifier)
    assert result["intent"] == "ambiguous" and result["state"] == "clarification"
    assert result["proposal"] is None and result["receipt"] is None
    contextual = run(
        message, locale, None, {"last_case_id": "CASE-123456789ABC"}, records, classifier
    )
    assert contextual["state"] == "case_lookup"
    assert contextual["case_context_id"] == "CASE-123456789ABC"


@pytest.mark.parametrize(
    "message,locale",
    [
        ("Consulta la referencia de soporte que me dieron.", "es"),
        ("Mostre o acompanhamento do processo anterior.", "pt"),
        ("¿Se actualizó la revisión de mi disputa existente?", "es"),
        ("Minha solicitação anterior já está com um analista?", "pt"),
    ],
)
def test_legitimate_existing_request_tracking_does_not_need_saved_chat_context(message, locale):
    result = run(
        message,
        locale,
        None,
        {},
        transactions("demo-es"),
        lambda *args: {"intent": "case_status", "signals": []},
    )
    assert result["state"] == "case_lookup"


@pytest.mark.parametrize(
    "message,locale",
    [
        ("Não fale com um atendente ainda; diga o valor do lançamento.", "pt"),
        ("Quiero ver la información de una transferencia que sí autoricé.", "es"),
        ("Quero ver as informações de uma transferência que eu autorizei.", "pt"),
        (
            "A loja afirma que a compra continua em espera; qual situação consta no meu registro?",
            "pt",
        ),
    ],
)
def test_explicit_facts_and_affirmed_authorization_do_not_propose_false_disputes(message, locale):
    result = run(message, locale, None, {}, transactions("demo-es"), classify)
    assert result["intent"] == "transaction_status"
    assert result["state"] == "clarification"
    assert result["proposal"] is None

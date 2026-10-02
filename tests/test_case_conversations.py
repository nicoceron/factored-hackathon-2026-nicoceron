"""Behavioral contracts for specific handoffs and persisted two-way review."""

import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from fastapi.testclient import TestClient

from factored_banking.api import create_app
from factored_banking.privacy import redact_text


def login(client, persona="customer_es", language="es"):
    result = client.post("/api/session", json={"persona": persona, "language": language})
    assert result.status_code == 200
    client.headers["X-CSRF-Token"] = result.json()["csrf_token"]


def chat(client, text, key="chat-first-0001", tx=None):
    return client.post(
        "/api/chat",
        json={"message": text, "transaction_id": tx, "language": "es", "idempotency_key": key},
    )


@pytest.fixture
def system(tmp_path):
    app = create_app(str(tmp_path / "cases.sqlite"), enable_external=False)
    app.state.classifier = lambda *args: {
        "intent": "dispute",
        "signals": [],
        "model_version": "test-only",
    }
    with TestClient(app) as client:
        login(client)
        yield app, client


def create_case(client):
    first = chat(client, "Me cobraron dos veces ayer; necesito revisar el segundo cargo.")
    assert first.json()["state"] == "clarification"
    selected = chat(client, "Esa operación", "chat-select-0002", "TX-ES-101").json()
    assert "dos veces ayer" in selected["proposal"]["customer_report"]
    reply = client.post(
        "/api/actions/confirm",
        json={"proposal_id": selected["proposal"]["id"], "idempotency_key": "create-case-0001"},
    )
    assert reply.status_code == 200
    return reply.json()["receipt"]["id"]


def ask(client, case, key="question-0001"):
    return client.post(
        f"/api/cases/{case}/resolve",
        json={
            "resolution": "needs_information",
            "question": "¿Los dos cargos tienen la misma fecha?",
            "idempotency_key": key,
        },
    )


def answer(client, case, key="answer-question-0001"):
    detail = client.get(f"/api/cases/{case}").json()
    question = next(
        (
            event
            for event in reversed(detail.get("timeline", []))
            if event["type"] == "question_requested"
        ),
        {"id": "EVT-" + "0" * 24},
    )
    return client.post(
        f"/api/cases/{case}/messages",
        json={
            "message": "Sí, ambos aparecen con fecha de ayer.",
            "question_id": question["id"],
            "idempotency_key": key,
        },
    )


def test_specific_report_and_complete_persisted_followup(system):
    app, client = system
    case = create_case(client)
    login(client, "analyst")
    asked = ask(client, case)
    assert asked.status_code == 200
    assert asked.json()["receipt"]["verified"]
    assert asked.json()["pending_question"]["text"] == "¿Los dos cargos tienen la misma fecha?"
    assert ask(client, case).json() == asked.json()
    assert ask(client, case, "different-request").status_code == 409
    login(client)
    assert client.get(f"/api/cases/{case}").json()["status"] == "needs_information"
    replied = answer(client, case)
    assert replied.status_code == 200
    assert replied.json()["status"] == "open" and replied.json()["pending_question"] is None
    assert answer(client, case).json() == replied.json()
    assert answer(client, case, "extra-answer-request").status_code == 409
    login(client, "analyst")
    closed = client.post(
        f"/api/cases/{case}/resolve",
        json={"resolution": "reviewed_closed", "idempotency_key": "close-review-0001"},
    )
    assert closed.status_code == 200
    assert [e["type"] for e in closed.json()["timeline"]] == [
        "case_created",
        "question_requested",
        "customer_reply",
        "review_closed",
    ]
    assert "dos veces ayer" in closed.json()["customer_report"]
    assert closed.json()["history_complete"]
    restarted = create_app(app.state.store.path, enable_external=False)
    with TestClient(restarted) as browser:
        browser.cookies.update(client.cookies)
        history = browser.get(f"/api/cases/{case}").json()["timeline"]
        assert history == closed.json()["timeline"]
    assert ask(client, case, "ask-after-close").status_code == 409


def test_followup_roles_ownership_and_required_question(system):
    app, client = system
    case = create_case(client)
    assert ask(client, case).status_code == 403
    login(client, "analyst")
    assert answer(client, case).status_code == 403
    assert (
        client.post(
            f"/api/cases/{case}/resolve",
            json={"resolution": "needs_information", "idempotency_key": "missing-question"},
        ).status_code
        == 422
    )
    ask(client, case)
    login(client, "customer_pt", "pt")
    assert answer(client, case).status_code == 404
    with TestClient(app) as stranger:
        login(stranger, "analyst")
        assert ask(stranger, case).status_code == 404
    login(client)
    client.headers.pop("X-CSRF-Token")
    assert answer(client, case).status_code == 403


def test_followup_readback_failure_retry_and_fingerprint(system, monkeypatch):
    app, client = system
    case = create_case(client)
    login(client, "analyst")
    verify = app.state.store.verify_case_event
    monkeypatch.setattr(app.state.store, "verify_case_event", lambda *args: None)
    assert ask(client, case).status_code == 503
    assert (
        client.post(
            f"/api/cases/{case}/resolve",
            json={"resolution": "reviewed_closed", "idempotency_key": "question-0001"},
        ).status_code
        == 409
    )
    monkeypatch.setattr(app.state.store, "verify_case_event", verify)
    assert ask(client, case).json()["receipt"]["verified"]
    history = client.get(f"/api/cases/{case}").json()["timeline"]
    assert len(history) == 2
    assert client.delete("/api/workspace").status_code == 200
    with app.state.store.connect() as db:
        assert db.execute("SELECT count(*) FROM case_events").fetchone()[0] == 0


def test_redaction_preserves_meaning_without_contact_or_credentials(system):
    app, client = system
    text = "Me cobraron dos veces. Mi correo es demo@example.test y mi contraseña es demo123."
    response = chat(client, text, tx="TX-ES-101").json()
    report = response["proposal"]["customer_report"]
    assert "Me cobraron dos veces" in report
    assert "demo@example.test" not in report and "demo123" not in report
    assert "[REDACTED]" in report
    with app.state.store.connect() as db:
        stored = json.dumps([dict(x) for x in db.execute("SELECT * FROM proposals")])
        assert "demo@example.test" not in stored and "demo123" not in stored
    assert redact_text("Teléfono +57 300 123 4567") == "Teléfono [REDACTED]"
    assert redact_text("Pasó el 2026-06-17 a las 12:45") == "Pasó el 2026-06-17 a las 12:45"


def test_slow_inference_does_not_lock_storage_and_reset_discards_stale_result(system):
    app, client = system
    started, release = Event(), Event()

    def slow(*args):
        started.set()
        assert release.wait(5)
        return {"intent": "human", "signals": [], "model_version": "slow-test"}

    app.state.classifier = slow
    with ThreadPoolExecutor() as pool:
        result = pool.submit(chat, client, "Necesito una persona")
        assert started.wait(5)
        reset = client.post("/api/conversation/reset")
        assert reset.status_code == 200
        release.set()
        assert result.result().status_code == 409
    assert client.get("/api/cases").json()["cases"] == []
    with app.state.store.connect() as db:
        assert db.execute("SELECT count(*) FROM proposals").fetchone()[0] == 0


def test_duplicate_inflight_chat_does_not_run_classifier_twice(system):
    app, client = system
    started, release = Event(), Event()
    calls = []

    def slow(*args):
        calls.append(1)
        started.set()
        assert release.wait(5)
        return {"intent": "human", "signals": [], "model_version": "slow-test"}

    app.state.classifier = slow
    with ThreadPoolExecutor() as pool:
        result = pool.submit(chat, client, "Necesito una persona")
        assert started.wait(5)
        assert chat(client, "Necesito una persona").status_code == 409
        release.set()
        assert result.result().status_code == 200
    assert len(calls) == 1


def test_discarded_provider_attempt_remains_in_scoped_cost_accounting(system, tmp_path):
    import httpx

    from factored_banking.providers import ProviderConfig, ProviderRuntime

    app, client = system
    started, release = Event(), Event()
    calls = []

    def unavailable(request):
        calls.append(request)
        started.set()
        assert release.wait(5)
        return httpx.Response(503, json={"error": "mock-unavailable"})

    app.state.ai.close()
    runtime = ProviderRuntime(
        ProviderConfig(
            enabled=True,
            jev_key="mock-key-never-transmitted",
            budget_usd=1,
            max_attempts=1,
            budget_path=str(tmp_path / "isolated-usage.sqlite"),
        ),
        transport=httpx.MockTransport(unavailable),
    )
    app.state.ai = runtime
    app.state.classifier = runtime.classify
    app.state.composer = runtime.compose
    assert client.get("/readyz").status_code == 200
    assert calls == []  # Readiness must never incur inference.
    with ThreadPoolExecutor() as pool:
        result = pool.submit(chat, client, "Necesito una persona")
        assert started.wait(5)
        assert client.post("/api/conversation/reset").status_code == 200
        release.set()
        assert result.result().status_code == 409
    login(client, "analyst")
    usage = client.get("/api/analytics").json()
    assert usage["total_requests"] == 0
    assert usage["provider_attempts"] == usage["unknown_cost_attempts"] == 1
    assert usage["model_api_cost_usd"] is None
    assert usage["estimated_model_api_cost_usd"] is None
    with TestClient(app) as stranger:
        login(stranger, "analyst")
        assert stranger.get("/api/analytics").json()["provider_attempts"] == 0
    assert client.delete("/api/workspace").status_code == 200
    # Erasure cannot reset the shared spending cap; the ledger has no conversation content.
    assert runtime.usage_since()["attempts"] == 1


@pytest.mark.parametrize("selected", [None, "TX-ES-103"])
def test_multiple_or_conflicting_references_preserve_dispute_through_selection(system, selected):
    app, client = system
    report = (
        "Me cobraron dos veces en TX-ES-101 y TX-ES-102; quiero revisar ambos."
        if selected is None
        else "No autoricé TX-ES-101; quiero revisarlo."
    )
    first = chat(client, report, tx=selected).json()
    assert first["state"] == "clarification"
    assert client.get("/api/session").json()["context"]["pending_intent"] == "dispute"
    app.state.classifier = lambda *args: {"intent": "ambiguous", "signals": []}
    following = chat(client, "TX-ES-101", "select-after-conflict", "TX-ES-101").json()
    assert following["intent"] == "dispute"
    assert following["state"] == "awaiting_confirmation"
    assert following["proposal"]["customer_report"] == report


def test_explicit_human_request_replaces_previous_pending_task(system):
    app, client = system
    chat(client, "No reconozco este cargo")
    app.state.classifier = lambda *args: {"intent": "human", "signals": ["explicit_human_request"]}
    request = "Necesito una persona que revise mi situación."
    assert chat(client, request, "human-next-request").json()["intent"] == "human"
    assert client.get("/api/session").json()["context"]["pending_intent"] == "human"
    app.state.classifier = lambda *args: {"intent": "ambiguous", "signals": []}
    selected = chat(client, "Esa operación", "select-human-context", "TX-ES-101").json()
    assert selected["intent"] == "human"
    assert selected["proposal"]["customer_report"] == request


def test_uncertain_provider_cannot_complete_a_pending_status_automatically(system):
    app, client = system
    app.state.classifier = lambda *args: {"intent": "transaction_status", "signals": []}
    assert chat(client, "Quiero consultar el estado").json()["state"] == "clarification"
    app.state.classifier = lambda *args: {"intent": "human", "signals": ["provider_uncertain"]}
    result = chat(client, "Esa operación", "uncertain-selection", "TX-ES-101").json()
    assert result["state"] == "awaiting_confirmation" and result["intent"] == "human"


def test_expired_inflight_reservations_do_not_block_new_requests(system):
    import time

    from factored_banking.store import digest, encode

    app, client = system
    session_hash = digest(client.cookies.get("claro_session"))
    with app.state.store.connect() as db:
        for index in range(2):
            db.execute(
                "INSERT INTO requests VALUES(?,?,?,?,?)",
                (
                    session_hash,
                    f"abandoned-request-{index}",
                    "fingerprint",
                    encode({"_pending": True, "started": time.time() - 120}),
                    time.time() - 120,
                ),
            )
    assert chat(client, "Necesito revisar un cargo").status_code == 200


def test_session_revoked_before_chat_transaction_returns_401(system, monkeypatch):
    from contextlib import contextmanager

    app, client = system
    connect = app.state.store.connect
    counter = 0

    @contextmanager
    def racing_connect():
        nonlocal counter
        counter += 1
        with connect() as db:
            if counter == 2:
                db.execute("DELETE FROM sessions")
                db.commit()
            yield db

    monkeypatch.setattr(app.state.store, "connect", racing_connect)
    assert chat(client, "Necesito ayuda").status_code == 401

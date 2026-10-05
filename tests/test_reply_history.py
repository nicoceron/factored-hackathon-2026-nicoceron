"""Verified same-composer replies survive session recovery without duplicate history."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from fastapi.testclient import TestClient

from factored_banking.api import create_app
from factored_banking.privacy import redact_text
from factored_banking.store import digest, encode


@pytest.fixture
def system(tmp_path):
    app = create_app(str(tmp_path / "reply-history.sqlite"), enable_external=False)
    with TestClient(app) as client:
        client.headers["X-Claro-Role"] = "customer"
        customer = client.post("/api/session", json={}).json()
        client.headers["X-CSRF-Token"] = customer["csrf_token"]
        proposed = client.post(
            "/api/chat",
            json={
                "message": "No reconozco el cargo de Tienda Demo.",
                "idempotency_key": "history-proposal-0001",
            },
        ).json()["proposal"]
        confirmed = client.post(
            "/api/actions/confirm",
            json={"proposal_id": proposed["id"], "idempotency_key": "history-confirm-0001"},
        )
        case = confirmed.json()["receipt"]["id"]
        client.headers["X-Claro-Role"] = "analyst"
        analyst = client.post("/api/session", json={"persona": "analyst"}).json()
        client.headers["X-CSRF-Token"] = analyst["csrf_token"]
        question = client.post(
            f"/api/cases/{case}/resolve",
            json={
                "resolution": "needs_information",
                "question": "¿El cargo fue antes o después de la llamada?",
                "idempotency_key": "history-question-0001",
            },
        ).json()["pending_question"]["id"]
        client.headers["X-Claro-Role"] = "customer"
        client.headers["X-CSRF-Token"] = customer["csrf_token"]
        lookup = client.post(
            "/api/chat",
            json={"message": "Como está meu caso?", "idempotency_key": "history-lookup-0001"},
        )
        assert lookup.status_code == 200 and lookup.json()["state"] == "case_lookup"
        body = {
            "message": "Foi depois da chamada. Meu PIN é 1234.",
            "question_id": question,
            "idempotency_key": "history-reply-0001",
        }
        yield app, client, case, body


@pytest.mark.parametrize(
    "message,language,ack",
    [
        ("Foi depois da chamada. Meu PIN é 1234.", "pt", "Resposta salva e verificada."),
        ("Fue después de la llamada. Mi OTP es 876543.", "es", "Respuesta guardada y verificada."),
    ],
)
def test_verified_reply_and_localized_ack_survive_reload_and_same_key_retry(
    system, message, language, ack
):
    app, client, case, body = system
    body = {**body, "message": message}
    before = client.get("/api/session").json()["context"]
    response = client.post(f"/api/cases/{case}/messages", json=body)
    assert response.status_code == 200
    result = response.json()
    assert result["receipt"]["verified"] and result["message"] == ack
    assert result["response_language"] == language
    assert result["language"] == "es"
    restored = client.get("/api/session").json()
    history = restored["context"]["history"]
    assert history[:-2] == before["history"]
    assert history[-2:] == [
        {"role": "user", "content": redact_text(message)},
        {"role": "assistant", "content": ack},
    ]
    assert restored["user"]["language"] == language
    assert "1234" not in encode(history) and "876543" not in encode(history)
    assert client.post(f"/api/cases/{case}/messages", json=body).json() == result
    assert client.get("/api/session").json()["context"]["history"] == history
    assert len(client.get(f"/api/cases/{case}").json()["timeline"]) == 3
    with TestClient(create_app(app.state.store.path, enable_external=False)) as restarted:
        restarted.cookies.update(client.cookies)
        restarted.headers["X-Claro-Role"] = "customer"
        assert restarted.get("/api/session").json()["context"]["history"] == history


def test_verified_reply_preserves_other_current_context_and_bounded_redacted_history(system):
    app, client, case, body = system
    token = digest(client.cookies.get("claro_customer_session"))
    context = {
        "last_case_id": case,
        "pending_intent": "dispute",
        "transaction_id": "TX-ES-101",
        "customer_report": "No reconozco otra operación.",
        "history": [
            {"role": "user" if index % 2 == 0 else "assistant", "content": "Detalle " * 400}
            for index in range(20)
        ],
    }
    with app.state.store.connect() as db:
        db.execute("UPDATE sessions SET state=? WHERE token_hash=?", (encode(context), token))
        revision = db.execute(
            "SELECT revision FROM sessions WHERE token_hash=?", (token,)
        ).fetchone()[0]
    assert client.post(f"/api/cases/{case}/messages", json=body).status_code == 200
    restored = client.get("/api/session").json()["context"]
    assert {k: v for k, v in restored.items() if k != "history"} == {
        k: v for k, v in context.items() if k != "history"
    }
    assert len(restored["history"]) <= 12
    assert sum(len(entry["content"]) for entry in restored["history"]) <= 12000
    assert restored["history"][-2]["content"] == redact_text(body["message"])
    with app.state.store.connect() as db:
        assert (
            db.execute("SELECT revision FROM sessions WHERE token_hash=?", (token,)).fetchone()[0]
            == revision + 1
        )


def test_failed_reply_readback_logs_no_success_and_reconciliation_appends_once(system, monkeypatch):
    app, client, case, body = system
    before = client.get("/api/session").json()["context"]["history"]
    verify = app.state.store.verify_case_event
    monkeypatch.setattr(app.state.store, "verify_case_event", lambda *args: None)
    assert client.post(f"/api/cases/{case}/messages", json=body).status_code == 503
    assert client.get("/api/session").json()["context"]["history"] == before
    assert len(client.get(f"/api/cases/{case}").json()["timeline"]) == 3
    monkeypatch.setattr(app.state.store, "verify_case_event", verify)
    recovered = client.post(f"/api/cases/{case}/messages", json=body)
    assert recovered.status_code == 200 and recovered.json()["receipt"]["verified"]
    after = client.get("/api/session").json()["context"]["history"]
    assert after[:-2] == before
    assert client.post(f"/api/cases/{case}/messages", json=body).json() == recovered.json()
    assert client.get("/api/session").json()["context"]["history"] == after
    assert len(client.get(f"/api/cases/{case}").json()["timeline"]) == 3


def test_history_and_retry_response_roll_back_together_if_final_transaction_fails(system):
    app, client, case, body = system
    before = client.get("/api/session").json()["context"]["history"]
    with app.state.store.connect() as db:
        db.execute(
            "CREATE TRIGGER fail_reply_audit BEFORE INSERT ON events "
            "WHEN NEW.event='case_reply' BEGIN SELECT RAISE(ABORT,'authored fault'); END"
        )
    assert client.post(f"/api/cases/{case}/messages", json=body).status_code == 503
    assert client.get("/api/session").json()["context"]["history"] == before
    token = digest(client.cookies.get("claro_customer_session"))
    with app.state.store.connect() as db:
        row = db.execute(
            "SELECT response FROM requests WHERE session_hash=? AND request_key=?",
            (token, body["idempotency_key"]),
        ).fetchone()
        assert json.loads(row["response"]) is None
        db.execute("DROP TRIGGER fail_reply_audit")
    recovered = client.post(f"/api/cases/{case}/messages", json=body)
    assert recovered.status_code == 200 and recovered.json()["receipt"]["verified"]
    history = client.get("/api/session").json()["context"]["history"]
    assert history[:-2] == before
    assert client.post(f"/api/cases/{case}/messages", json=body).json() == recovered.json()
    assert client.get("/api/session").json()["context"]["history"] == history
    assert len(client.get(f"/api/cases/{case}").json()["timeline"]) == 3


@pytest.mark.parametrize("invalidate", ["expire", "revoke"])
def test_session_invalidated_after_event_readback_cannot_log_a_verified_reply(
    system, monkeypatch, invalidate
):
    app, client, case, body = system
    token = digest(client.cookies.get("claro_customer_session"))
    before = client.get("/api/session").json()["context"]
    verify = app.state.store.verify_case_event

    def invalidate_after_readback(*args):
        verified = verify(*args)
        with app.state.store.connect() as db:
            if invalidate == "expire":
                db.execute(
                    "UPDATE sessions SET expires=? WHERE token_hash=?", (time.time() - 1, token)
                )
            else:
                db.execute("DELETE FROM sessions WHERE token_hash=?", (token,))
        return verified

    monkeypatch.setattr(app.state.store, "verify_case_event", invalidate_after_readback)
    assert client.post(f"/api/cases/{case}/messages", json=body).status_code == 401
    with app.state.store.connect() as db:
        pending = db.execute(
            "SELECT response FROM requests WHERE session_hash=? AND request_key=?",
            (token, body["idempotency_key"]),
        ).fetchone()
        assert pending is None or json.loads(pending["response"]) is None
        if invalidate == "expire":
            state = db.execute("SELECT state FROM sessions WHERE token_hash=?", (token,)).fetchone()
            assert json.loads(state["state"]) == before


def test_verified_reply_invalidates_inflight_chat_instead_of_losing_history(system):
    app, client, case, body = system
    started, release = Event(), Event()

    def slow(*args):
        started.set()
        assert release.wait(5)
        return {"intent": "ambiguous", "signals": [], "model_version": "delayed-test"}

    app.state.classifier = slow
    with ThreadPoolExecutor() as pool:
        inflight = pool.submit(
            client.post,
            "/api/chat",
            json={"message": "Reviso esta operación", "idempotency_key": "inflight-after-reply"},
        )
        assert started.wait(5)
        try:
            assert client.post(f"/api/cases/{case}/messages", json=body).status_code == 200
        finally:
            release.set()
        assert inflight.result().status_code == 409
    history = client.get("/api/session").json()["context"]["history"]
    assert history[-2]["content"] == redact_text(body["message"])
    assert history[-1]["content"] == "Resposta salva e verificada."
    assert all(entry["content"] != "Reviso esta operación" for entry in history)

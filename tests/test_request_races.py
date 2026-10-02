"""Races at request ownership, session validity and analyst-question boundaries."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Event, Lock

import pytest
from fastapi.testclient import TestClient

from factored_banking.api import create_app
from factored_banking.store import encode


def login(client, persona="customer_es"):
    response = client.post("/api/session", json={"persona": persona, "language": "es"})
    assert response.status_code == 200
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]


@pytest.fixture
def system(tmp_path):
    app = create_app(str(tmp_path / "races.sqlite"), enable_external=False)
    app.state.classifier = lambda *args: {
        "intent": "dispute",
        "signals": [],
        "model_version": "test-only",
    }
    with TestClient(app) as client:
        login(client)
        yield app, client


def propose(client):
    response = client.post(
        "/api/chat",
        json={
            "message": "Necesito revisar un cargo duplicado.",
            "transaction_id": "TX-ES-101",
            "idempotency_key": "proposal-0001",
        },
    )
    assert response.status_code == 200
    return response.json()["proposal"]["id"]


def create_case(client):
    response = client.post(
        "/api/actions/confirm",
        json={"proposal_id": propose(client), "idempotency_key": "confirm-0001"},
    )
    assert response.status_code == 200
    return response.json()["receipt"]["id"]


def question(client, case, key="question-0001"):
    response = client.post(
        f"/api/cases/{case}/resolve",
        json={
            "resolution": "needs_information",
            "question": "¿Cuándo viste el cargo por primera vez?",
            "idempotency_key": key,
        },
    )
    assert response.status_code == 200
    return response.json()["pending_question"]["id"]


@pytest.mark.parametrize("replace_by", ["reset", "expired_claim"])
def test_stale_request_cannot_commit_or_delete_a_replacement_claim(system, replace_by):
    app, client = system
    entered = [Event(), Event()]
    release = [Event(), Event()]
    calls = []
    counter_lock = Lock()

    def blocking_classifier(*args):
        with counter_lock:
            index = len(calls)
            calls.append(index)
        assert index < 2, "Duplicate in-flight request must never run inference"
        entered[index].set()
        assert release[index].wait(5)
        return {"intent": "human", "signals": [], "model_version": "test-only"}

    app.state.classifier = blocking_classifier
    request = {"message": "Necesito una persona.", "idempotency_key": "same-request-0001"}
    with ThreadPoolExecutor(2) as pool:
        try:
            original = pool.submit(client.post, "/api/chat", json=request)
            assert entered[0].wait(5)
            if replace_by == "reset":
                assert client.post("/api/conversation/reset").status_code == 200
            else:
                with app.state.store.connect() as db:
                    row = db.execute("SELECT response FROM requests").fetchone()
                    claim = json.loads(row["response"])
                    claim["started"] = time.time() - 120
                    db.execute(
                        "UPDATE requests SET response=?,created=?",
                        (encode(claim), time.time() - 120),
                    )
            replacement = pool.submit(client.post, "/api/chat", json=request)
            assert entered[1].wait(5)
            release[0].set()
            assert original.result(timeout=5).status_code == 409
            # Original cleanup must preserve the new owner, even though its key
            # and fingerprint match. Another same-key retry remains in flight.
            assert client.post("/api/chat", json=request).status_code == 409
            assert len(calls) == 2
            release[1].set()
            accepted = replacement.result(timeout=5)
            assert accepted.status_code == 200
            assert client.post("/api/chat", json=request).json() == accepted.json()
            with app.state.store.connect() as db:
                assert db.execute("SELECT count(*) FROM proposals").fetchone()[0] == 1
        finally:
            for event in release:
                event.set()


def test_stale_answer_cannot_satisfy_a_newer_analyst_question(system):
    _, client = system
    case = create_case(client)
    login(client, "analyst")
    first_question = question(client, case)
    login(client)
    first_answer = {
        "message": "Lo vi ayer por la tarde.",
        "question_id": first_question,
        "idempotency_key": "reply-0001",
    }
    assert client.post(f"/api/cases/{case}/messages", json=first_answer).status_code == 200
    login(client, "analyst")
    second_question = question(client, case, "question-0002")
    login(client)
    stale_answer = {**first_answer, "idempotency_key": "stale-reply-0002"}
    assert client.post(f"/api/cases/{case}/messages", json=stale_answer).status_code == 409
    detail = client.get(f"/api/cases/{case}").json()
    assert detail["status"] == "needs_information"
    assert detail["pending_question"]["id"] == second_question
    assert len(detail["timeline"]) == 4
    current_answer = {**stale_answer, "question_id": second_question}
    accepted = client.post(f"/api/cases/{case}/messages", json=current_answer)
    assert accepted.status_code == 200
    assert client.post(f"/api/cases/{case}/messages", json=current_answer).json() == accepted.json()
    assert client.post(f"/api/cases/{case}/messages", json=stale_answer).status_code == 409


def test_question_id_is_required_and_two_answers_cannot_consume_same_question(system):
    _, client = system
    case = create_case(client)
    login(client, "analyst")
    question_id = question(client, case)
    login(client)
    answer = {"message": "Lo vi ayer.", "idempotency_key": "reply-0001"}
    assert client.post(f"/api/cases/{case}/messages", json=answer).status_code == 422
    with ThreadPoolExecutor(2) as pool:
        responses = list(
            pool.map(
                lambda key: client.post(
                    f"/api/cases/{case}/messages",
                    json={**answer, "question_id": question_id, "idempotency_key": key},
                ),
                ("concurrent-reply-0001", "concurrent-reply-0002"),
            )
        )
    assert sorted(response.status_code for response in responses) == [200, 409]
    history = client.get(f"/api/cases/{case}").json()["timeline"]
    assert [event["type"] for event in history].count("customer_reply") == 1


@pytest.mark.parametrize("operation", ["confirm", "review", "reply"])
@pytest.mark.parametrize("cached", [False, True])
def test_expiry_while_waiting_for_mutation_lock_rejects_write_and_cached_response(
    system, monkeypatch, operation, cached
):
    app, client = system
    if operation == "confirm":
        path = "/api/actions/confirm"
        body = {"proposal_id": propose(client), "idempotency_key": "confirm-0001"}
    else:
        case = create_case(client)
        login(client, "analyst")
        if operation == "review":
            path = f"/api/cases/{case}/resolve"
            body = {
                "resolution": "needs_information",
                "question": "¿Cuándo viste el cargo?",
                "idempotency_key": "question-0001",
            }
        else:
            question_id = question(client, case)
            login(client)
            path = f"/api/cases/{case}/messages"
            body = {
                "message": "Lo vi ayer.",
                "question_id": question_id,
                "idempotency_key": "reply-0001",
            }
    if cached:
        assert client.post(path, json=body).status_code == 200
    with app.state.store.connect() as db:
        cases_before = [dict(row) for row in db.execute("SELECT * FROM cases")]
        events_before = [dict(row) for row in db.execute("SELECT * FROM case_events")]
    connect = app.state.store.connect
    counter = 0

    @contextmanager
    def expire_between_auth_and_lock():
        nonlocal counter
        counter += 1
        with connect() as db:
            if counter == 2:
                # The first connection performed session authentication. This
                # boundary models expiry before the mutation acquires its lock.
                db.execute("UPDATE sessions SET expires=?", (time.time() - 1,))
                db.commit()
            yield db

    monkeypatch.setattr(app.state.store, "connect", expire_between_auth_and_lock)
    assert client.post(path, json=body).status_code == 401
    with connect() as db:
        assert [dict(row) for row in db.execute("SELECT * FROM cases")] == cases_before
        assert [dict(row) for row in db.execute("SELECT * FROM case_events")] == events_before


@pytest.mark.parametrize(
    "method,path",
    [
        ("DELETE", "/api/session"),
        ("DELETE", "/api/workspace"),
        ("POST", "/api/conversation/reset"),
    ],
)
@pytest.mark.parametrize("invalidate", ["expire", "revoke"])
def test_reset_and_erasure_recheck_live_session_under_their_lock(
    system, monkeypatch, method, path, invalidate
):
    app, client = system
    create_case(client)
    connect = app.state.store.connect

    def snapshot():
        with connect() as db:
            return {
                table: [dict(row) for row in db.execute("SELECT * FROM " + table)]
                for table in ("workspaces", "proposals", "cases", "case_events")
            }

    before = snapshot()
    counter = 0

    @contextmanager
    def invalidate_between_auth_and_lock():
        nonlocal counter
        counter += 1
        with connect() as db:
            if counter == 2:
                if invalidate == "expire":
                    db.execute("UPDATE sessions SET expires=?", (time.time() - 1,))
                else:
                    db.execute("DELETE FROM sessions")
                db.commit()
            yield db

    monkeypatch.setattr(app.state.store, "connect", invalidate_between_auth_and_lock)
    assert client.request(method, path).status_code == 401
    assert snapshot() == before

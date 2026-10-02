"""Regression cases from independent concurrency and failure-path review."""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from factored_banking.api import create_app
from factored_banking.fixtures import transactions
from factored_banking.workflow import run


@pytest.mark.parametrize(
    ("signal", "expected"),
    [
        ("model_unavailable", "human"),
        ("customer_reported_scam", "scam"),
        ("customer_reported_dispute", "dispute"),
        ("explicit_human_request", "human"),
    ],
)
def test_independent_safety_signal_cannot_be_resolved_as_status(signal, expected):
    result = run(
        "support request",
        "es",
        "TX-ES-101",
        {},
        transactions("demo-es"),
        lambda *args: {
            "intent": "ambiguous",
            "signals": [signal],
            "model_version": "unavailable" if signal == "model_unavailable" else "test",
        },
    )
    assert result["intent"] == expected
    assert result["state"] == "awaiting_confirmation"
    assert result["proposal_payload"]["intent"] == expected


def test_readiness_detects_structured_model_failure(tmp_path):
    app = create_app(str(tmp_path / "state.sqlite"))
    app.state.classifier = lambda *args: {
        "intent": "ambiguous",
        "signals": ["model_unavailable"],
        "model_version": "language-unavailable-v1",
    }
    with TestClient(app) as client:
        assert client.get("/readyz").status_code == 503


def test_key_is_bound_before_committed_write_readback_window(tmp_path):
    app = create_app(str(tmp_path / "state.sqlite"))
    app.state.classifier = lambda *args: {
        "intent": "dispute",
        "signals": [],
        "model_version": "test",
    }
    with TestClient(app) as client:
        login = client.post("/api/session", json={"persona": "customer_es"}).json()
        client.headers["X-CSRF-Token"] = login["csrf_token"]

        def proposal(key):
            response = client.post(
                "/api/chat",
                json={"message": "dispute", "transaction_id": "TX-ES-101", "idempotency_key": key},
            )
            assert response.status_code == 200
            return response.json()["proposal"]["id"]

        first_proposal = proposal("prepare-first")
        entered, release = threading.Event(), threading.Event()
        original = app.state.store.verify_case
        calls = 0

        def delayed_first_readback(*args):
            nonlocal calls
            calls += 1
            if calls == 1:
                entered.set()
                assert release.wait(10), "Test must release readback promptly"
            return original(*args)

        app.state.store.verify_case = delayed_first_readback
        with ThreadPoolExecutor() as pool:
            first = pool.submit(
                client.post,
                "/api/actions/confirm",
                json={"proposal_id": first_proposal, "idempotency_key": "same-confirm-key"},
            )
            try:
                assert entered.wait(5)
                second_proposal = proposal("prepare-second")
                second = client.post(
                    "/api/actions/confirm",
                    json={"proposal_id": second_proposal, "idempotency_key": "same-confirm-key"},
                )
                assert second.status_code == 409
            finally:
                release.set()
            assert first.result().status_code == 200
        assert len(client.get("/api/cases").json()["cases"]) == 1

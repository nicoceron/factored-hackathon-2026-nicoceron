"""Informed confirmation and independent customer/reviewer browser sessions.

These authored integration checks do not change benchmark denominators.
"""

import time

import pytest
from fastapi.testclient import TestClient

from factored_banking.api import create_app
from factored_banking.fixtures import transactions
from factored_banking.store import digest


@pytest.fixture
def app(tmp_path):
    value = create_app(str(tmp_path / "roles.sqlite"), enable_external=False)
    value.state.classifier = lambda message, language: {
        "intent": {"dispute": "dispute", "human": "human", "explain": "transaction_status"}.get(
            message, "ambiguous"
        ),
        "confidence": 1.0,
        "model_version": "session-contract-stub",
        "signals": [],
    }
    return value


def login(client, persona="customer_es", **fields):
    response = client.post("/api/session", json={"persona": persona, **fields})
    assert response.status_code == 200, response.text
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    return response.json()


def chat(client, message="dispute", transaction="TX-ES-101", key="role-chat-0001"):
    body = {"message": message, "idempotency_key": key}
    if transaction:
        body["transaction_id"] = transaction
    response = client.post("/api/chat", json=body)
    assert response.status_code == 200, response.text
    return response.json()


def confirm(client, proposal, key="role-confirm-0001"):
    return client.post(
        "/api/actions/confirm", json={"proposal_id": proposal, "idempotency_key": key}
    )


def test_proposal_names_the_immutable_validated_record_in_chat_and_session(app):
    with TestClient(app) as client:
        login(client)
        proposed = chat(client)
        record = transactions("demo-es")[0]
        fields = {"id", "merchant", "amount", "currency", "status", "date", "as_of", "source"}
        snapshot = proposed["proposal"]["transaction"]
        assert fields <= snapshot.keys()
        assert snapshot == {key: record[key] for key in fields | {"provenance"}}
        assert "channel" not in snapshot and "customer" not in snapshot
        chat(client, "explain", "TX-ES-102", "different-record-query")
        restored = client.get("/api/session").json()["proposal"]
        assert restored["id"] == proposed["proposal"]["id"]
        assert restored["transaction"] == snapshot
        receipt = confirm(client, restored["id"]).json()["receipt"]
        stored = client.get("/api/cases/" + receipt["id"]).json()
        assert stored["transaction"]["id"] == snapshot["id"]
        assert stored["transaction"]["amount"] == snapshot["amount"]


def test_unattached_human_proposal_explicitly_has_no_record(app):
    with TestClient(app) as client:
        login(client)
        result = chat(client, "human", None)
        assert result["state"] == "awaiting_confirmation"
        assert result["proposal"]["transaction"] is None
        assert client.get("/api/session").json()["proposal"]["transaction"] is None


def test_two_tabs_share_browser_cookies_without_losing_customer_proposal_or_retry(app):
    with TestClient(app) as customer, TestClient(app) as reviewer:
        customer.headers["X-Claro-Role"] = "customer"
        customer_session = login(customer)
        reviewer.cookies.jar = customer.cookies.jar
        reviewer.headers["X-Claro-Role"] = "analyst"
        proposed = chat(customer)
        customer_token = customer.cookies.get("claro_customer_session")
        analyst_session = login(reviewer, "analyst")
        analyst_token = reviewer.cookies.get("claro_analyst_session")
        assert customer_token != analyst_token
        assert customer_session["csrf_token"] != analyst_session["csrf_token"]
        assert customer.get("/api/session").json()["context"]["history"]
        assert customer.get("/api/session").json()["proposal"]["id"] == proposed["proposal"]["id"]
        assert chat(customer) == proposed
        assert reviewer.get("/api/session").json()["user"]["role"] == "analyst"
        restored = login(customer)
        assert customer.cookies.get("claro_customer_session") == customer_token
        assert restored["csrf_token"] == customer_session["csrf_token"]
        assert restored["proposal"]["id"] == proposed["proposal"]["id"]
        assert reviewer.get("/api/session").json()["user"]["role"] == "analyst"
        first = confirm(customer, proposed["proposal"]["id"])
        assert first.status_code == 200 and first.json()["receipt"]["verified"]
        assert confirm(customer, proposed["proposal"]["id"]).json() == first.json()
        assert len(reviewer.get("/api/cases").json()["cases"]) == 1
        with app.state.store.connect() as db:
            assert db.execute("SELECT count(*) FROM sessions").fetchone()[0] == 2
            assert db.execute("SELECT count(*) FROM cases").fetchone()[0] == 1


def test_no_header_keeps_active_legacy_role_and_hint_never_grants_a_role(app):
    with TestClient(app) as client:
        login(client)
        login(client, "analyst")
        assert client.get("/api/session").json()["user"]["role"] == "analyst"
        assert client.get("/api/transactions").status_code == 403
        assert (
            client.get("/api/transactions", headers={"X-Claro-Role": "customer"}).status_code == 200
        )
        assert client.get("/api/analytics", headers={"X-Claro-Role": "customer"}).status_code == 403
        assert client.get("/api/session", headers={"X-Claro-Role": "admin"}).status_code == 400
    with TestClient(app) as only_customer:
        login(only_customer)
        # Without a reviewer cookie, a hint may use legacy only when its actual role matches.
        assert (
            only_customer.get("/api/analytics", headers={"X-Claro-Role": "analyst"}).status_code
            == 403
        )


def test_cross_role_csrf_and_cross_workspace_session_cookies_are_rejected(app):
    with TestClient(app) as customer, TestClient(app) as reviewer, TestClient(app) as stranger:
        customer.headers["X-Claro-Role"] = "customer"
        customer_session = login(customer)
        reviewer.cookies.jar = customer.cookies.jar
        reviewer.headers["X-Claro-Role"] = "analyst"
        proposed = chat(customer)
        case_id = confirm(customer, proposed["proposal"]["id"]).json()["receipt"]["id"]
        analyst_session = login(reviewer, "analyst")
        body = {
            "resolution": "needs_information",
            "question": "¿Cuándo viste el cargo?",
            "idempotency_key": "role-question-0001",
        }
        response = reviewer.post(
            f"/api/cases/{case_id}/resolve",
            json=body,
            headers={"X-CSRF-Token": customer_session["csrf_token"]},
        )
        assert response.status_code == 403
        requested = reviewer.post(f"/api/cases/{case_id}/resolve", json=body)
        assert requested.status_code == 200 and requested.json()["receipt"]["verified"]
        reply = {
            "message": "Lo vi ayer por la tarde.",
            "question_id": requested.json()["pending_question"]["id"],
            "idempotency_key": "role-reply-0001",
        }
        assert (
            customer.post(
                f"/api/cases/{case_id}/messages",
                json=reply,
                headers={"X-CSRF-Token": analyst_session["csrf_token"]},
            ).status_code
            == 403
        )
        assert customer.post(f"/api/cases/{case_id}/messages", json=reply).json()["receipt"][
            "verified"
        ]
        login(stranger, "analyst")
        assert stranger.get(f"/api/cases/{case_id}").status_code == 404
        foreign_workspace = stranger.cookies.get("claro_workspace")
        stranger.cookies.jar = customer.cookies.jar
        assert (
            stranger.get(
                "/api/session",
                headers={
                    "Cookie": f"claro_session={customer.cookies.get('claro_session')}; "
                    f"claro_workspace={foreign_workspace}",
                },
            ).status_code
            == 401
        )


@pytest.mark.parametrize("role", ["customer", "analyst"])
def test_logout_revokes_only_selected_role_and_keeps_other_tab_usable(app, role):
    with TestClient(app) as client:
        customer = login(client)
        analyst = login(client, "analyst")
        credentials = {"customer": customer, "analyst": analyst}
        other = "analyst" if role == "customer" else "customer"
        token = client.cookies.get(f"claro_{role}_session")
        response = client.delete(
            "/api/session",
            headers={
                "X-Claro-Role": role,
                "X-CSRF-Token": credentials[role]["csrf_token"],
            },
        )
        assert response.status_code == 200
        assert client.cookies.get(f"claro_{role}_session") is None
        assert (
            client.get("/api/session", headers={"X-Claro-Role": other}).json()["user"]["role"]
            == other
        )
        assert client.get("/api/session", headers={"X-Claro-Role": role}).status_code in {401, 403}
        with app.state.store.connect() as db:
            assert (
                db.execute("SELECT * FROM sessions WHERE token_hash=?", (digest(token),)).fetchone()
                is None
            )
            assert db.execute("SELECT count(*) FROM sessions").fetchone()[0] == 1


def test_legacy_only_session_migrates_before_reviewer_alias_changes(app):
    with TestClient(app) as client:
        original = login(client)
        proposed = chat(client)
        token = client.cookies.get("claro_session")
        client.cookies.delete("claro_customer_session")
        login(client, "analyst")
        assert client.cookies.get("claro_customer_session") == token
        restored = client.get("/api/session", headers={"X-Claro-Role": "customer"}).json()
        assert restored["csrf_token"] == original["csrf_token"]
        assert restored["proposal"]["id"] == proposed["proposal"]["id"]


def test_identity_switch_and_workspace_deletion_keep_scope_authoritative(app):
    with TestClient(app) as client:
        login(client)
        customer_token = client.cookies.get("claro_customer_session")
        proposal = chat(client)["proposal"]["id"]
        analyst = login(client, "analyst")
        reviewer_token = client.cookies.get("claro_analyst_session")
        switched = login(client, "customer_pt")
        assert switched["demo_persona"] == "customer_pt" and switched["proposal"] is None
        assert client.cookies.get("claro_analyst_session") == reviewer_token
        assert confirm(client, proposal).status_code == 404
        with app.state.store.connect() as db:
            assert (
                db.execute(
                    "SELECT * FROM sessions WHERE token_hash=?", (digest(customer_token),)
                ).fetchone()
                is None
            )
        assert client.get("/api/transactions").json()["transactions"] == transactions("demo-pt")
        response = client.delete(
            "/api/workspace",
            headers={
                "X-Claro-Role": "analyst",
                "X-CSRF-Token": analyst["csrf_token"],
            },
        )
        assert response.status_code == 200
        for name in (
            "claro_workspace",
            "claro_session",
            "claro_customer_session",
            "claro_analyst_session",
        ):
            assert client.cookies.get(name) is None
        with app.state.store.connect() as db:
            assert db.execute("SELECT count(*) FROM sessions").fetchone()[0] == 0


def test_session_refresh_retains_inferred_locale_and_expired_role_cannot_fallback(app):
    with TestClient(app) as client:
        login(client)
        chat(client, "Qual é o estado da Tienda Demo?", None)
        assert login(client)["user"]["language"] == "pt"
        login(client, "analyst")
        token = client.cookies.get("claro_customer_session")
        with app.state.store.connect() as db:
            db.execute(
                "UPDATE sessions SET expires=? WHERE token_hash=?", (time.time() - 1, digest(token))
            )
        assert client.get("/api/session", headers={"X-Claro-Role": "customer"}).status_code == 401
        assert client.get("/api/session", headers={"X-Claro-Role": "analyst"}).status_code == 200


def test_role_cookies_have_same_secure_transport_controls_as_legacy_cookie(app):
    secure_app = create_app(app.state.store.path, secure_cookies=True, enable_external=False)
    with TestClient(secure_app, base_url="https://testserver") as client:
        login(client)
        response = client.post("/api/session", json={"persona": "analyst"})
        cookies = response.headers.get_list("set-cookie")
        for name in ("claro_session", "claro_analyst_session", "claro_workspace"):
            value = next(item for item in cookies if item.startswith(name + "="))
            assert "HttpOnly" in value and "Secure" in value and "SameSite=strict" in value
        assert client.get("/api/session", headers={"X-Claro-Role": "customer"}).status_code == 200

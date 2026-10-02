"""Faulty tool records must never become verified monetary facts or handoff evidence."""

import json

import pytest
from fastapi.testclient import TestClient

from factored_banking import api
from factored_banking.fixtures import transactions
from factored_banking.system_evaluation import chat, confirm, login


@pytest.mark.parametrize("language", ["es", "pt"])
@pytest.mark.parametrize(
    ("field", "bad_value", "remove"),
    [
        ("amount", None, True),
        ("currency", None, True),
        ("source", None, True),
        ("as_of", None, True),
        ("provenance", None, True),
        ("amount", None, False),
        ("amount", "NaN", False),
        ("amount", "Infinity", False),
        ("amount", "-1.00", False),
        ("amount", 500, False),
        ("currency", "XYZ", False),
        ("status", "not_verified", False),
        ("source", " ", False),
        ("as_of", "2026-02-30", False),
        ("merchant", {"injection": "unsafe"}, False),
    ],
)
def test_invalid_tool_fields_never_become_financial_facts(
    tmp_path, monkeypatch, language, field, bad_value, remove
):
    row = transactions(f"demo-{language}")[0]
    if remove:
        row.pop(field)
    else:
        row[field] = bad_value
    monkeypatch.setattr(api, "transactions", lambda customer: [row])
    app = api.create_app(str(tmp_path / "sandbox.sqlite"), secure_cookies=False)
    with TestClient(app) as client:
        login(client, language)
        message = (
            "Quiero consultar el estado del pago"
            if language == "es"
            else "Quero consultar o estado do pagamento"
        )
        response = chat(client, message, language, "bad-evidence-0001", row["id"])
        assert response.status_code == 200
        result = response.json()
        assert result["state"] == "awaiting_confirmation"
        assert result["intent"] == "human"
        assert "transaction" not in result
        assert result["receipt"] is None
        assert not any(e["id"] == row["id"] for e in result["evidence"])
        assert client.get("/api/cases").json() == {"cases": []}
        created = confirm(client, result["proposal"]["id"], "bad-evidence-confirm").json()
        assert created["receipt"]["verified"]
        case = client.get(f"/api/cases/{created['receipt']['id']}").json()
        assert case["reason"] == "invalid_transaction_evidence"
        assert case["transaction"] is None
        assert case["unverified_transaction_reference"] == row["id"]
        assert case["risk"]["probability"] is None
        assert case["open_questions"]


def test_extra_tool_fields_are_not_projected_into_customer_or_handoff(tmp_path, monkeypatch):
    row = transactions("demo-es")[0]
    row.update(is_fraud=True, fraud_score=99, customer_secret="not-for-serving")
    monkeypatch.setattr(api, "transactions", lambda customer: [row])
    app = api.create_app(str(tmp_path / "sandbox.sqlite"), secure_cookies=False)
    with TestClient(app) as client:
        login(client, "es")
        result = chat(
            client, "Quiero consultar el estado del pago", "es", "extra-fields-0001", row["id"]
        ).json()
        assert result["state"] == "resolved"
        assert not {"is_fraud", "fraud_score", "customer_secret"} & result["transaction"].keys()
        assert "not-for-serving" not in json.dumps(result)
        assert result["transaction"]["amount"] == row["amount"]


def test_conflicting_tool_rows_are_not_arbitrarily_selected(tmp_path, monkeypatch):
    row = transactions("demo-es")[0]
    monkeypatch.setattr(api, "transactions", lambda customer: [row, {**row, "amount": "1.00"}])
    app = api.create_app(str(tmp_path / "sandbox.sqlite"), secure_cookies=False)
    with TestClient(app) as client:
        login(client, "es")
        result = chat(
            client, "Quiero consultar el estado del pago", "es", "duplicate-0001", row["id"]
        ).json()
        assert result["state"] == "awaiting_confirmation"
        assert "transaction" not in result


def test_unidentifiable_tool_row_cannot_be_selected_from_empty_context(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "transactions", lambda customer: [{}, None])
    app = api.create_app(str(tmp_path / "sandbox.sqlite"), secure_cookies=False)
    with TestClient(app) as client:
        login(client, "es")
        result = chat(client, "Quiero consultar el estado del pago", "es", "missing-id-0001").json()
        assert result["state"] == "clarification"
        assert "transaction" not in result

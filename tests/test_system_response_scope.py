"""Distinguish the wrong owned transaction from an actual permission violation."""

import httpx
import pytest

from factored_banking import system_evaluation
from factored_banking.api import create_app
from factored_banking.fixtures import transactions
from factored_banking.system_evaluation import scenario


@pytest.mark.parametrize("foreign", [False, True])
def test_scoped_unauthorized_metric_does_not_confuse_owned_record_routing_with_access(
    tmp_path, monkeypatch, foreign
):
    app = create_app(str(tmp_path / "scope.sqlite"), enable_external=False)
    app.state.classifier = lambda *args: {
        "intent": "transaction_status",
        "confidence": 1.0,
        "model_version": "response-scope-test",
        "signals": [],
    }
    replacement = transactions("demo-pt")[0] if foreign else transactions("demo-es")[2]
    original = system_evaluation.chat

    def wrong_record(*args, **kwargs):
        response = original(*args, **kwargs)
        result = response.json()
        if result.get("state") == "resolved":
            result["transaction"] = replacement
            result["message"] = (
                f"{replacement['id']}: {replacement['amount']} {replacement['currency']}; "
                f"registro al {replacement['as_of']}."
            )
            result["evidence"] = [{"id": replacement["id"], "source": replacement["source"]}]
            return httpx.Response(200, json=result, request=response.request)
        return response

    monkeypatch.setattr(system_evaluation, "chat", wrong_record)
    result = scenario(
        app,
        {
            "id": "wrong-target-scope-check",
            "semantic_group": "wrong-target-scope-check",
            "language": "es",
            "intent": "transaction_status",
            "text": "Quiero consultar el estado del pago.",
        },
    )
    assert not result["correct_outcome"] and result["materially_wrong_outcome"]
    assert result["unauthorized_disclosure_or_action"] == foreign

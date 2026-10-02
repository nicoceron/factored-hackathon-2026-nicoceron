"""Verify the benchmark rejects false completion and evaluates actual case receipts."""

from fastapi.testclient import TestClient

from factored_banking.api import create_app
from factored_banking.language import classify
from factored_banking.system_evaluation import scenario, summarize


def test_false_handoff_is_not_confirmed_or_counted_as_success(tmp_path):
    app = create_app(str(tmp_path / "eval.sqlite"), secure_cookies=False)
    app.state.classifier = lambda *args: {
        "intent": "human",
        "confidence": 1.0,
        "model_version": "deliberately_wrong",
        "signals": [],
    }
    result = scenario(
        app,
        {
            "id": "test-benchmark-wrong-route",
            "semantic_group": "benchmark-check",
            "text": "Consulta el pago",
            "language": "es",
            "intent": "transaction_status",
        },
    )
    assert not result["correct_outcome"]
    assert not result["verified_handoff"]
    assert result["unnecessary_handoff_proposed"]
    with app.state.store.connect() as db:
        assert db.execute("SELECT count(*) FROM cases").fetchone()[0] == 0


def test_report_requires_real_case_verification_and_grounded_resolution(tmp_path):
    app = create_app(str(tmp_path / "eval.sqlite"), secure_cookies=False)
    app.state.classifier = classify
    results = [
        scenario(app, row)
        for row in [
            {
                "id": "test-benchmark-dispute",
                "semantic_group": "benchmark-dispute",
                "text": "Não reconheço essa cobrança.",
                "language": "pt",
                "intent": "dispute",
            },
            {
                "id": "test-benchmark-status",
                "semantic_group": "benchmark-status",
                "text": "Quiero consultar el estado de mi pago.",
                "language": "es",
                "intent": "transaction_status",
            },
        ]
    ]
    assert all(r["correct_outcome"] for r in results)
    assert results[0]["state_sequence"] == ["clarification", "awaiting_confirmation", "escalated"]
    aggregate = summarize(results)
    assert aggregate["verified_handoffs"] == 1
    assert aggregate["safe_automated_resolutions"] == 1
    assert aggregate["safe_automated_resolution_rate_all_in_scope"] == 0.5
    assert aggregate["containment_no_verified_transfer"] == 0.5
    assert aggregate["unauthorized_disclosure_or_action"] == 0
    # Evaluator does not change the application's default classifier or public metrics.
    with TestClient(app) as client:
        assert client.get("/healthz").status_code == 200


def test_zero_success_cost_denominator_is_undefined(tmp_path):
    app = create_app(str(tmp_path / "eval.sqlite"), secure_cookies=False)
    app.state.classifier = classify
    result = scenario(
        app,
        {
            "id": "test-benchmark-ambiguous",
            "semantic_group": "ambiguous",
            "text": "¿Ya salió?",
            "language": "es",
            "intent": "ambiguous",
        },
    )
    summary = summarize([result])
    assert summary["correct_outcomes"] == 1
    assert summary["safe_automated_resolutions"] == 0
    assert summary["model_api_cost_per_successful_automated_resolution_usd"] is None

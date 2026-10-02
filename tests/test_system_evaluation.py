"""Verify the benchmark rejects false completion and evaluates actual case receipts."""

from fastapi.testclient import TestClient

from factored_banking.api import create_app
from factored_banking.language import classify
from factored_banking.system_evaluation import (
    handoff_quality,
    load_challenge,
    run_workload,
    scenario,
    summarize,
)


def test_false_handoff_is_not_confirmed_or_counted_as_success(tmp_path):
    app = create_app(str(tmp_path / "eval.sqlite"), secure_cookies=False, enable_external=False)
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
    app = create_app(str(tmp_path / "eval.sqlite"), secure_cookies=False, enable_external=False)
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
    app = create_app(str(tmp_path / "eval.sqlite"), secure_cookies=False, enable_external=False)
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


def test_handoff_quality_rejects_generic_and_changed_customer_meaning():
    report = "Hice una sola compra y me cobraron dos veces; revisen el segundo cargo."
    packet = {
        "customer_report": "El cliente solicita revisar una operación.",
        "report_provenance": "customer_allegation_redacted_not_verified",
        "evidence": [{"source": "fixture"}],
        "open_questions": ["¿Tiene el comprobante?"],
        "actions_taken": [],
        "risk": {"status": "out_of_domain"},
        "policy_version": "test",
        "intent": "dispute",
        "priority": "normal",
        "transaction": {"id": "TX-ES-101"},
    }
    quality = handoff_quality(packet, "dispute", packet["transaction"], report)
    assert quality["required_fields_present"]
    assert not quality["reference_request_preserved"]
    assert not quality["appropriate_for_reference_intent"]
    packet["customer_report"] = "El cliente niega haber hecho la compra y exige un reembolso."
    assert not handoff_quality(packet, "dispute", packet["transaction"], report)[
        "reference_request_preserved"
    ]
    packet["customer_report"] = "Relato del cliente, sin verificar: " + report
    assert handoff_quality(packet, "dispute", packet["transaction"], report)[
        "appropriate_for_reference_intent"
    ]


def test_handoff_preserves_specific_request_after_transaction_selection(tmp_path):
    app = create_app(str(tmp_path / "details.sqlite"), secure_cookies=False, enable_external=False)
    app.state.classifier = lambda *args: {
        "intent": "dispute",
        "confidence": 1.0,
        "model_version": "test_reference",
        "signals": [],
    }
    result = scenario(
        app,
        {
            "id": "specific-duplicate-request",
            "semantic_group": "specific-duplicate",
            "text": "Compré una vez el martes y aparecen dos cargos; necesito revisar el segundo.",
            "language": "es",
            "intent": "dispute",
        },
    )
    assert result["verified_handoff"]
    assert result["handoff_packet"]["reference_request_preserved"]
    assert result["correct_outcome"]


def test_provider_cost_is_usage_estimate_not_invoice_and_unknown_is_not_zero():
    case = {
        "expected_intent": "transaction_status",
        "correct_outcome": True,
        "successful_automated_resolution": True,
        "final_state": "resolved",
        "latency_ms": 12.0,
        "unauthorized_disclosure_or_action": False,
        "provider_usage": {
            "attempts": 2,
            "input_tokens": 150,
            "output_tokens": 20,
            "estimated_cost_usd": 0.001,
            "unknown_cost_attempts": 0,
            "reserved_budget_usd": 0.001,
        },
    }
    summary = summarize([case])
    assert summary["model_api_spend_usd"] is None
    assert summary["model_api_cost_per_attempt_usd"] is None
    assert summary["estimated_model_api_cost_per_attempt_usd"] == 0.001
    assert summary["estimated_model_api_cost_per_successful_automated_resolution_usd"] == 0.001
    case["provider_usage"].update(unknown_cost_attempts=1, estimated_cost_usd=None)
    summary = summarize([case])
    assert summary["provider_usage"]["attempts"] == 2
    assert summary["estimated_model_api_cost_per_attempt_usd"] is None
    assert summary["estimated_model_api_cost_per_successful_automated_resolution_usd"] is None


def test_offline_workload_disables_external_provider_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CLARO_EXTERNAL_AI_ENABLED", "1")
    shared_ledger = tmp_path / "developer-shared-ledger.sqlite"
    monkeypatch.setenv("CLARO_PROVIDER_BUDGET_DB", str(shared_ledger))

    def unexpected_network(*args, **kwargs):
        raise AssertionError("Offline evaluation attempted external network")

    import httpx

    # TestClient supplies a separate in-process transport; ordinary provider HTTP is forbidden.
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", unexpected_network)
    rows = [
        {
            "id": "offline-ambiguity",
            "semantic_group": "offline",
            "text": "¿Ya salió?",
            "language": "es",
            "intent": "ambiguous",
        }
    ]
    aggregate, _ = run_workload(rows, classify, run_faults=False)
    assert aggregate["provider_usage"]["attempts"] == 0
    assert aggregate["all_run_usage_including_setup_warmup_faults"]["attempts"] == 0
    assert not shared_ledger.exists()


def test_prospective_corpus_is_frozen_unique_and_balanced():
    from pathlib import Path

    from factored_banking.evaluation import RESOURCE

    rows = load_challenge(Path(str(RESOURCE.joinpath("system_prospective_test.json"))))
    assert len(rows) == 70
    assert {row["review_status"] for row in rows} == {"not_independently_human_reviewed"}


def test_initial_http_failure_counts_required_handoff_as_missed(tmp_path, monkeypatch):
    import httpx

    from factored_banking import system_evaluation

    app = create_app(str(tmp_path / "http-failure.sqlite"), enable_external=False)
    monkeypatch.setattr(system_evaluation, "chat", lambda *args: httpx.Response(503))
    result = scenario(
        app,
        {
            "id": "unavailable-human",
            "semantic_group": "unavailable-human",
            "language": "es",
            "intent": "human",
            "text": "Necesito una persona.",
        },
    )
    summary = summarize([result])
    assert summary["correct_outcomes"] == 0
    assert summary["required_handoffs"] == 1
    assert summary["verified_handoffs"] == 0
    assert summary["missed_required_handoffs"] == 1


def test_provider_meter_separates_warmup_from_measured_cases():
    class Meter:
        def __init__(self):
            self.calls = 0

        def snapshot(self):
            return self.calls

        def usage_since(self, cursor):
            count = self.calls - cursor
            return {
                "attempts": count,
                "input_tokens": count * 100,
                "output_tokens": count * 10,
                "estimated_cost_usd": count * 0.001,
                "unknown_cost_attempts": 0,
                "reserved_budget_usd": count * 0.002,
                "model_ids": ["test-usage-model"],
                "by_provider": {},
            }

        def classify(self, *args):
            self.calls += 1
            return {
                "intent": "ambiguous",
                "confidence": 0.1,
                "model_version": "synthetic-meter-check",
                "signals": [],
            }

    meter = Meter()
    rows = [
        {
            "id": "meter-scope",
            "semantic_group": "meter-scope",
            "language": "es",
            "text": "No sé cuál es.",
            "intent": "ambiguous",
        }
    ]
    report, _ = run_workload(rows, meter.classify, usage_meter=meter, run_faults=False)
    assert report["provider_usage"]["attempts"] == 1
    assert report["all_run_usage_including_setup_warmup_faults"]["attempts"] == 2
    assert report["provider_usage"]["input_tokens"] == 100
    assert report["provider_usage"]["model_ids"] == ["test-usage-model"]
    assert report["estimated_model_api_cost_per_attempt_usd"] == 0.001
    assert report["model_api_spend_usd"] is None


def test_first_pass_receipt_cannot_be_overwritten_as_regression(tmp_path):
    import pytest

    from factored_banking.system_evaluation import ensure_report_replaceable

    first = tmp_path / "system-challenge-evaluation.json"
    first.write_text('{"workload_status":"new authored challenge; frozen before first scoring"}')
    before = first.read_bytes()
    with pytest.raises(ValueError, match="Preserve first-pass"):
        ensure_report_replaceable(first)
    assert first.read_bytes() == before
    regression = tmp_path / "system-challenge-regression.json"
    regression.write_text('{"workload_status":"challenge regression"}')
    ensure_report_replaceable(regression)

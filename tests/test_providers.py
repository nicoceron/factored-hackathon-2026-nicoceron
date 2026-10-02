"""Provider boundary contracts with mock HTTP only; never perform paid inference."""

import copy
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import httpx
import pytest

from factored_banking.language import INTENTS
from factored_banking.providers import (
    DEEPSEEK_MODEL,
    DEEPSEEK_URL,
    JEV_MODEL,
    JEV_URL,
    ProviderConfig,
    ProviderRuntime,
)


def jev_response(intent="transaction_status", *, nouls=None, probability=0.94):
    return {
        "model": JEV_MODEL,
        "answers": {
            "intent": {
                "type": "choice",
                "choice": intent,
                "probabilities": {
                    label: probability if label == intent else (1 - probability) / 6
                    for label in INTENTS
                },
                "confidence": (probability - 1 / 7) / (1 - 1 / 7),
            },
            **{
                name: {"type": "noul", "noul": (nouls or {}).get(name, 0.02)}
                for name in ("scam_report", "disputed_transaction", "wants_human")
            },
        },
        "usage": {"input_tokens": 100, "output_tokens": 40},
    }


def deepseek_response(language="es", **changes):
    output = {
        "language": language,
        "acknowledgement": "Entiendo tu preocupación."
        if language == "es"
        else "Entendo sua dúvida.",
        "question": "",
        "evidence_ids": ["TX-ES-101"],
        **changes,
    }
    return {
        "model": DEEPSEEK_MODEL,
        "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(output)}}],
        "usage": {"prompt_tokens": 200, "completion_tokens": 60},
    }


@pytest.fixture
def runtime_factory(tmp_path):
    runtimes = []

    def factory(handler, **overrides):
        config = ProviderConfig(
            **{
                "enabled": True,
                "jev_key": "unit-test-jev-placeholder",
                "deepseek_key": "unit-test-deepseek-placeholder",
                "budget_usd": 1,
                "budget_path": str(tmp_path / "budget.sqlite"),
                **overrides,
            }
        )
        delays = []
        runtime = ProviderRuntime(
            config, transport=httpx.MockTransport(handler), sleep=delays.append
        )
        runtime.test_delays = delays
        runtimes.append(runtime)
        return runtime

    yield factory
    for runtime in runtimes:
        runtime.close()


@pytest.fixture
def workflow_result():
    return {
        "state": "resolved",
        "intent": "transaction_status",
        "message": "Registro TX-ES-101: COP 42.000. Estado registrado: completada.",
        "evidence": [
            {"id": "TX-ES-101", "text": "Sandbox fixture", "provenance": "team_authored_synthetic"}
        ],
        "transaction": {"id": "TX-ES-101", "provenance": "team_authored_synthetic"},
    }


def test_jev_batches_choice_and_independent_nouls_in_one_redacted_request(runtime_factory):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=jev_response("scam", nouls={"scam_report": 0.98}))

    runtime = runtime_factory(handler)
    result = runtime.classify(
        "Me engañaron. Correo persona@example.test y contraseña: testingsecret.",
        context={"pending_intent": "transaction_status", "customer_id": "private-customer"},
    )
    assert len(calls) == 1
    assert str(calls[0].url) == JEV_URL
    payload = json.loads(calls[0].content)
    assert payload["model"] == JEV_MODEL
    assert payload["questions"]["intent"]["type"] == "choice"
    assert len(payload["questions"]) == 4
    assert {item["type"] for item in payload["questions"].values()} == {"choice", "noul"}
    assert payload["state"]["context"] == {"pending_intent": "transaction_status"}
    assert (
        payload["state"]["illustrative_example"]["provenance"]
        == "team_authored_development_example"
    )
    assert "persona@example.test" not in calls[0].content.decode()
    assert "testingsecret" not in calls[0].content.decode()
    assert "private-customer" not in calls[0].content.decode()
    assert result["intent"] == "scam"
    assert result["signals"] == ["customer_reported_scam"]
    assert result["provider_meta"]["status"] == "ok"
    assert result["provider_meta"]["input_tokens"] == 100
    assert result["provider_meta"]["output_tokens"] == 40
    assert result["provider_meta"]["estimated_cost_usd"] == pytest.approx(100 * 0.042 / 1e6)
    assert result["provider_meta"]["cost_complete"]


def test_healthy_jev_semantic_negatives_are_not_overridden_by_lexical_flags(runtime_factory):
    runtime = runtime_factory(lambda request: httpx.Response(200, json=jev_response()))
    result = runtime.classify(
        "No quiero hablar con humano; no denuncio fraude ni disputo el cargo."
    )
    assert result["intent"] == "transaction_status"
    assert result["signals"] == []


@pytest.mark.parametrize(
    "response",
    [jev_response(probability=0.5), jev_response(nouls={"scam_report": 0.5})],
)
def test_uncertainty_abstains_without_claiming_calibrated_confidence(runtime_factory, response):
    runtime = runtime_factory(lambda request: httpx.Response(200, json=response))
    result = runtime.classify("Tengo una inquietud.")
    assert result["intent"] == "human"
    assert result["signals"] == ["provider_uncertain"]
    assert result["provider_meta"]["status"] == "uncertain"


def test_noul_threshold_boundaries_use_documented_inclusive_decisions(runtime_factory):
    runtime = runtime_factory(
        lambda request: httpx.Response(
            200, json=jev_response(nouls={"scam_report": 0.2, "wants_human": 0.8})
        )
    )
    result = runtime.classify("Consulta.")
    assert result["provider_meta"]["status"] == "ok"
    assert result["signals"] == ["explicit_human_request"]
    assert result["noul_probabilities"]["scam_report"] == 0.2


@pytest.mark.parametrize(
    "mutate",
    [
        lambda body: body["answers"]["intent"].update(choice="do_payment"),
        lambda body: body["answers"]["intent"].update(confidence=0.1),
        lambda body: body["answers"]["intent"]["probabilities"].update(dispute=0.9),
        lambda body: body["answers"]["intent"]["probabilities"].pop("human"),
        lambda body: body["answers"]["scam_report"].update(noul=True),
        lambda body: body["answers"].update(hidden_reasoning="Do not retain this"),
        lambda body: body.update(model="jev-unknown"),
    ],
)
def test_invalid_jev_schema_fails_closed_but_records_valid_usage(runtime_factory, mutate):
    body = jev_response()
    mutate(body)
    runtime = runtime_factory(lambda request: httpx.Response(200, json=body))
    result = runtime.classify("Consulta de estado.")
    assert result["intent"] == "human"
    assert result["signals"] == ["model_unavailable"]
    assert result["provider_meta"]["status"] == "invalid_response"
    assert result["provider_meta"]["attempts"] == 1
    assert result["provider_meta"]["input_tokens"] == 100
    assert "Do not retain this" not in json.dumps(result)


@pytest.mark.parametrize("body", [[], None, {"usage": []}, {"usage": {"input_tokens": True}}])
def test_malformed_envelope_is_controlled_failure(runtime_factory, body):
    runtime = runtime_factory(lambda request: httpx.Response(200, json=body))
    result = runtime.classify("Consulta.")
    assert result["intent"] == "human"
    assert result["provider_meta"]["status"] == "invalid_response"
    assert result["provider_meta"]["unknown_cost_attempts"] == 1
    assert not result["provider_meta"]["cost_complete"]


def no_http(request):
    pytest.fail("This path must not contact a provider")


@pytest.mark.parametrize(
    "overrides,status",
    [({"budget_usd": 0}, "budget_not_authorized"), ({"jev_key": ""}, "missing_key")],
)
def test_provider_configuration_gates_before_network(runtime_factory, overrides, status):
    runtime = runtime_factory(no_http, **overrides)
    assert runtime.status()["classifier"]["status"] == status
    result = runtime.classify("Consulta.")
    assert result["intent"] == "human"
    assert result["provider_meta"]["status"] == status
    assert runtime.usage_since()["attempts"] == 0


def test_disabled_and_readiness_configuration_never_call_provider(runtime_factory, workflow_result):
    runtime = runtime_factory(no_http, enabled=False)
    assert runtime.status()["classifier"]["status"] == "disabled"
    assert runtime.classify("Estado de mi transferencia.")["provider_meta"]["provider"] == "local"
    assert runtime.compose("Hola", "es", workflow_result)["message"] == workflow_result["message"]
    enabled = runtime_factory(no_http)
    assert enabled.status()["classifier"]["status"] == "configured_not_probed"
    assert "unit-test" not in repr(enabled.config)
    assert "unit-test" not in json.dumps(enabled.status())


def test_explicit_false_override_ignores_external_enabled_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("CLARO_EXTERNAL_AI_ENABLED", "1")
    runtime = ProviderRuntime.from_env(enabled=False, budget_path=str(tmp_path / "forced.sqlite"))
    try:
        assert runtime.config.enabled is False
        assert runtime.status()["external_enabled"] is False
    finally:
        runtime.close()


def test_retry_backoff_is_bounded_and_all_attempts_are_reserved(runtime_factory):
    calls = []

    def handler(request):
        calls.append(request)
        return (
            httpx.Response(429, headers={"retry-after": "1"})
            if len(calls) == 1
            else httpx.Response(200, json=jev_response())
        )

    runtime = runtime_factory(handler)
    result = runtime.classify("Consulta.")
    assert result["provider_meta"]["status"] == "ok"
    assert len(calls) == 2
    assert runtime.test_delays == [1]
    assert result["provider_meta"]["attempts"] == 2
    assert result["provider_meta"]["unknown_cost_attempts"] == 1
    assert result["provider_meta"]["reserved_budget_usd"] > 0


@pytest.mark.parametrize(
    "response,status",
    [
        (httpx.Response(401, text="raw secret error"), "rejected_http"),
        (httpx.Response(302, headers={"Location": "https://evil.example/"}), "rejected_http"),
        (httpx.Response(429, headers={"retry-after": "99"}), "retry_deferred"),
    ],
)
def test_no_retry_for_auth_redirect_or_long_retry_after(runtime_factory, response, status):
    runtime = runtime_factory(lambda request: response)
    result = runtime.classify("Consulta.")
    assert result["provider_meta"]["status"] == status
    assert result["provider_meta"]["attempts"] == 1
    assert runtime.test_delays == []
    assert "raw secret" not in json.dumps(result)


def test_timeout_exhausts_only_configured_attempts_and_returns_human(runtime_factory):
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("sensitive provider response should never escape", request=request)

    runtime = runtime_factory(handler)
    result = runtime.classify("Consulta.")
    assert result["intent"] == "human"
    assert len(calls) == 2
    assert runtime.test_delays == [0.25]
    assert result["provider_meta"]["status"] == "transport_unavailable"
    assert result["provider_meta"]["unknown_cost_attempts"] == 2
    assert "sensitive provider response" not in json.dumps(result)


def test_oversized_response_is_rejected(runtime_factory):
    runtime = runtime_factory(lambda request: httpx.Response(200, content=b" " * 64_001))
    result = runtime.classify("Consulta.")
    assert result["provider_meta"]["status"] == "response_limit"
    assert result["provider_meta"]["attempts"] == 1


def test_usage_exceeding_reservation_invalidates_output_and_is_not_lost(runtime_factory):
    body = jev_response()
    body["usage"]["input_tokens"] = 100_000
    runtime = runtime_factory(lambda request: httpx.Response(200, json=body))
    result = runtime.classify("Consulta.")
    assert result["intent"] == "human"
    assert result["provider_meta"]["status"] == "usage_bound_exceeded"
    assert result["provider_meta"]["input_tokens"] == 100_000
    assert (
        result["provider_meta"]["estimated_cost_usd"]
        > result["provider_meta"]["reserved_budget_usd"]
    )


def test_preflight_budget_rejects_without_network(runtime_factory):
    runtime = runtime_factory(no_http, budget_usd=0.000000001)
    result = runtime.classify("Consulta.")
    assert result["provider_meta"]["status"] == "budget_exhausted"
    assert result["provider_meta"]["attempts"] == 0


def test_request_cap_survives_runtime_restart(runtime_factory):
    runtime = runtime_factory(
        lambda request: httpx.Response(200, json=jev_response()), max_requests=1
    )
    assert runtime.classify("Consulta.")["provider_meta"]["status"] == "ok"
    restarted = runtime_factory(no_http, max_requests=1)
    assert restarted.classify("Otra consulta.")["provider_meta"]["status"] == "budget_exhausted"
    assert restarted.usage_since()["attempts"] == 1


def test_atomic_reservation_prevents_concurrent_budget_oversubscription(runtime_factory):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=jev_response())

    first = runtime_factory(handler, max_requests=1)
    second = runtime_factory(handler, max_requests=1)
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda runtime: runtime.classify("Consulta."), (first, second)))
    assert len(calls) == 1
    assert sorted(result["provider_meta"]["status"] for result in results) == [
        "budget_exhausted",
        "ok",
    ]


def test_call_metadata_does_not_count_concurrent_unrelated_invocation(runtime_factory):
    nested_result = []
    entered = False

    def handler(request):
        nonlocal entered
        if not entered:
            entered = True
            nested_result.append(runtime.classify("Concurrent other workspace"))
        return httpx.Response(200, json=jev_response())

    runtime = runtime_factory(handler)
    outer = runtime.classify("Outer workspace")
    assert runtime.usage_since()["attempts"] == 2
    assert outer["provider_meta"]["attempts"] == nested_result[0]["provider_meta"]["attempts"] == 1
    assert outer["provider_meta"]["input_tokens"] == 100


def test_concurrent_workspace_scopes_include_failed_calls_without_mixing(runtime_factory):
    barrier = Barrier(2)
    first_scope, second_scope = "a" * 32, "b" * 32

    def handler(request):
        barrier.wait(timeout=5)
        text = json.loads(request.content)["state"]["message"]
        return (
            httpx.Response(200, json=jev_response())
            if text == "First workspace"
            else httpx.Response(503)
        )

    runtime = runtime_factory(handler, max_attempts=1)

    def invoke(task):
        scope_id, text = task
        with runtime.scope(scope_id):
            return runtime.classify(text)

    with ThreadPoolExecutor(2) as pool:
        results = list(
            pool.map(invoke, [(first_scope, "First workspace"), (second_scope, "Second workspace")])
        )
    assert [result["provider_meta"]["attempts"] for result in results] == [1, 1]
    first, second = (runtime.usage_for_scope(value) for value in (first_scope, second_scope))
    assert first["attempts"] == second["attempts"] == 1
    assert first["input_tokens"] == 100
    assert first["unknown_cost_attempts"] == 0
    assert second["input_tokens"] == 0
    assert second["unknown_cost_attempts"] == 1
    assert second["cost_complete"] is False
    assert second["reserved_budget_usd"] > 0
    assert runtime.usage_since()["attempts"] == 2
    assert first_scope not in json.dumps(first)
    assert second_scope not in json.dumps(second)


def test_scope_restores_parent_and_clears_after_exception(runtime_factory):
    runtime = runtime_factory(lambda request: httpx.Response(200, json=jev_response()))
    first_scope, second_scope = "a" * 32, "b" * 32
    with runtime.scope(first_scope):
        runtime.classify("Parent")
        with pytest.raises(RuntimeError, match="cancelled after inference"):
            with runtime.scope(second_scope):
                runtime.classify("Nested")
                raise RuntimeError("cancelled after inference")
        runtime.classify("Parent again")
    runtime.classify("Unscoped benchmark")
    assert runtime.usage_for_scope(first_scope)["attempts"] == 2
    assert runtime.usage_for_scope(second_scope)["attempts"] == 1
    assert runtime.usage_since()["attempts"] == 4
    with runtime.ledger.connect() as db:
        assert (
            db.execute("SELECT count(*) FROM provider_attempts WHERE scope_id IS NULL").fetchone()[
                0
            ]
            == 1
        )


def test_scope_attribution_survives_restart_but_does_not_reset_global_cap(runtime_factory):
    runtime = runtime_factory(
        lambda request: httpx.Response(200, json=jev_response()), max_requests=1
    )
    with runtime.scope("a" * 32):
        runtime.classify("Call eventually discarded by application revision check")
    restarted = runtime_factory(no_http, max_requests=1)
    assert restarted.usage_for_scope("a" * 32)["attempts"] == 1
    with restarted.scope("b" * 32):
        result = restarted.classify("Other workspace")
    assert result["provider_meta"]["status"] == "budget_exhausted"
    assert restarted.usage_for_scope("b" * 32)["attempts"] == 0
    assert restarted.usage_since()["attempts"] == 1


def test_scope_schema_upgrade_preserves_unattributed_legacy_budget(runtime_factory):
    runtime = runtime_factory(lambda request: httpx.Response(200, json=jev_response()))
    runtime.classify("Legacy unscoped call")
    with runtime.ledger.connect() as db:
        db.execute("DROP INDEX provider_scope")
        db.execute("ALTER TABLE provider_attempts DROP COLUMN scope_id")
    restarted = runtime_factory(lambda request: httpx.Response(200, json=jev_response()))
    assert restarted.usage_since()["attempts"] == 1
    assert restarted.usage_for_scope("a" * 32)["attempts"] == 0
    with restarted.scope("a" * 32):
        restarted.classify("Attributed call")
    assert restarted.usage_since()["attempts"] == 2
    assert restarted.usage_for_scope("a" * 32)["attempts"] == 1


@pytest.mark.parametrize("invalid", ["customer@example.test", "customer-123", "", None])
def test_scope_accepts_only_opaque_server_workspace_id(runtime_factory, invalid):
    runtime = runtime_factory(no_http)
    with pytest.raises(ValueError, match="opaque sandbox workspace"):
        with runtime.scope(invalid):
            pytest.fail("Invalid scope must not be entered")
    with pytest.raises(ValueError, match="opaque sandbox workspace"):
        runtime.usage_for_scope(invalid)


def test_ledger_failure_does_not_turn_safe_fallback_into_500(runtime_factory, monkeypatch):
    runtime = runtime_factory(no_http)

    def unavailable(*args, **kwargs):
        raise sqlite3.OperationalError("sensitive filesystem path")

    monkeypatch.setattr(runtime.ledger, "snapshot", unavailable)
    monkeypatch.setattr(runtime.ledger, "reserve", unavailable)
    monkeypatch.setattr(runtime.ledger, "usage_since", unavailable)
    result = runtime.classify("Consulta.")
    assert result["intent"] == "human"
    assert result["provider_meta"]["status"] == "budget_store_unavailable"
    assert result["provider_meta"]["estimated_cost_usd"] is None
    assert not result["provider_meta"]["cost_complete"]
    assert "sensitive filesystem path" not in json.dumps(result)


def test_broken_ledger_after_outbound_explicitly_reports_unknown_attempt(
    runtime_factory, monkeypatch
):
    runtime = runtime_factory(lambda request: httpx.Response(200, json=jev_response()))

    def unavailable(*args, **kwargs):
        raise sqlite3.OperationalError("Sensitive detail")

    monkeypatch.setattr(runtime.ledger, "finish", unavailable)
    monkeypatch.setattr(runtime.ledger, "usage_since", unavailable)
    result = runtime.classify("Consulta")
    assert result["provider_meta"]["attempts"] == 1
    assert result["provider_meta"]["unknown_cost_attempts"] == 1
    assert result["provider_meta"]["estimated_cost_usd"] is None
    assert result["provider_meta"]["cost_complete"] is False


@pytest.mark.parametrize("language", ["es", "pt"])
def test_deepseek_adds_wording_around_immutable_facts_without_tool_authority(
    runtime_factory, workflow_result, language
):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=deepseek_response(language))

    runtime = runtime_factory(handler)
    original = copy.deepcopy(workflow_result)
    result = runtime.compose(
        "Ayuda. Mi email es persona@example.test.",
        language,
        workflow_result,
        history=[{"role": "user", "content": "contraseña: testingsecret"}],
    )
    assert str(calls[0].url) == DEEPSEEK_URL
    payload = json.loads(calls[0].content)
    assert payload["model"] == "deepseek-flash"
    assert payload["thinking"] == {"type": "disabled"}
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["max_tokens"] == 384
    assert "tools" not in payload
    assert "persona@example.test" not in calls[0].content.decode()
    assert "testingsecret" not in calls[0].content.decode()
    assert result["used_provider"]
    assert workflow_result["message"] in result["message"]
    assert workflow_result == original
    assert result["provider_meta"]["status"] == "ok"
    assert result["provider_meta"]["estimated_cost_usd"] == pytest.approx(
        (200 * 0.30 + 60 * 1.20) / 1e6
    )


@pytest.mark.parametrize(
    "generated",
    [
        "Su reembolso será de 30 pesos.",
        "O pagamento foi aprovado.",
        "La operación está pendiente.",
        "Ya fue creado el caso.",
        "I refunded your payment.",
        "I approved your request.",
        "Me diga sua senha.",
        "Indica tu nombre.",
        "Escribe tu documento.",
        "https://evil.example",
    ],
)
def test_generated_financial_claims_or_sensitive_requests_rejected(
    runtime_factory, workflow_result, generated
):
    runtime = runtime_factory(
        lambda request: httpx.Response(200, json=deepseek_response(acknowledgement=generated))
    )
    result = runtime.compose("Consulta.", "es", workflow_result)
    assert result["message"] == workflow_result["message"]
    assert not result["used_provider"]
    assert result["provider_meta"]["status"] == "invalid_response"
    assert result["provider_meta"]["output_tokens"] == 60


@pytest.mark.parametrize(
    "changes", [{"language": "pt"}, {"evidence_ids": ["invented-source"]}, {"extra": "forbidden"}]
)
def test_deepseek_schema_and_citations_are_validated(runtime_factory, workflow_result, changes):
    runtime = runtime_factory(
        lambda request: httpx.Response(200, json=deepseek_response(**changes))
    )
    result = runtime.compose("Consulta.", "es", workflow_result)
    assert result["message"] == workflow_result["message"]
    assert result["provider_meta"]["status"] == "invalid_response"


@pytest.mark.parametrize("finish_reason,tool_calls", [("length", None), ("stop", [{"id": "call"}])])
def test_truncation_and_tool_calls_rejected(
    runtime_factory, workflow_result, finish_reason, tool_calls
):
    body = deepseek_response()
    body["choices"][0]["finish_reason"] = finish_reason
    body["choices"][0]["message"]["tool_calls"] = tool_calls
    runtime = runtime_factory(lambda request: httpx.Response(200, json=body))
    result = runtime.compose("Consulta.", "es", workflow_result)
    assert result["message"] == workflow_result["message"]
    assert not result["used_provider"]


@pytest.mark.parametrize(
    "changes,status",
    [
        ({"state": "blocked"}, "deterministic_boundary"),
        ({"evidence": [{"id": "organizer", "provenance": "restricted"}]}, "unapproved_evidence"),
        ({"evidence": [{"provenance": "team_authored_synthetic"}]}, "unapproved_evidence"),
        ({"evidence": None}, "unapproved_evidence"),
        ({"transaction": "bad tool response"}, "unapproved_evidence"),
    ],
)
def test_unapproved_or_malformed_evidence_never_leaves_service(
    runtime_factory, workflow_result, changes, status
):
    workflow_result.update(changes)
    runtime = runtime_factory(no_http)
    result = runtime.compose("Consulta.", "es", workflow_result)
    assert result["message"] == workflow_result["message"]
    assert result["provider_meta"]["status"] == status
    assert result["provider_meta"]["attempts"] == 0


def test_deepseek_outage_preserves_deterministic_response(runtime_factory, workflow_result):
    runtime = runtime_factory(lambda request: httpx.Response(503))
    result = runtime.compose("Consulta.", "es", workflow_result)
    assert result["message"] == workflow_result["message"]
    assert not result["used_provider"]
    assert result["provider_meta"]["attempts"] == 2
    assert result["provider_meta"]["unknown_cost_attempts"] == 2

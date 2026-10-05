"""Reject generic, stale or ungrounded case chat even when case storage works."""

from copy import deepcopy
from datetime import UTC, datetime

import httpx
import pytest

from factored_banking import system_evaluation
from factored_banking.api import create_app
from factored_banking.system_evaluation import grounded_case_lookup, scenario


def case_answer(locale="es"):
    stored = {
        "id": "CASE-0123456789AB",
        "status": "needs_information",
        "updated_at": 1781697600.0,
        "transaction": {"id": "TX-ES-102"},
        "pending_question": {"id": "EVT-0123456789abcdef01234567", "text": "¿Fue un solo pago?"},
        "customer_report": "Aparecen dos cargos para una compra.",
        "timeline": [{"type": "question_requested", "text": "¿Fue un solo pago?"}],
    }
    label = "esperando tu respuesta" if locale == "es" else "aguardando sua resposta"
    as_of = datetime.fromtimestamp(stored["updated_at"], UTC).isoformat(timespec="seconds")
    result = {
        "state": "case_lookup",
        "cases": [deepcopy(stored)],
        "message": f"{stored['id']}: {label}, TX-ES-102. {as_of}. ¿Fue un solo pago?",
        "evidence": [
            {
                "id": stored["id"],
                "source": "sandbox_case_store/" + stored["id"],
                "text": label,
                "as_of": as_of,
                "provenance": "persisted_sandbox_case",
            }
        ],
    }
    return stored, result


@pytest.mark.parametrize("locale", ["es", "pt"])
def test_case_lookup_requires_actual_snapshot_and_localized_record_evidence(locale):
    stored, result = case_answer(locale)
    assert grounded_case_lookup(result, stored, locale)


@pytest.mark.parametrize(
    "defect",
    [
        "generic_message",
        "missing_cases",
        "stale_status",
        "changed_customer_report",
        "missing_question",
        "missing_transaction",
        "wrong_timestamp",
        "wrong_source",
        "wrong_provenance",
        "wrong_language",
        "missing_evidence",
    ],
)
def test_case_lookup_rejects_incomplete_or_changed_conversational_facts(defect):
    stored, result = case_answer()
    if defect == "generic_message":
        result["message"] = "Consulta Mis casos para ver el estado de tus solicitudes."
    elif defect == "missing_cases":
        result.pop("cases")
    elif defect == "stale_status":
        result["cases"][0]["status"] = "open"
    elif defect == "changed_customer_report":
        result["cases"][0]["customer_report"] = "El cliente nunca realizó una compra."
    elif defect == "missing_question":
        result["message"] = result["message"].replace("¿Fue un solo pago?", "")
    elif defect == "missing_transaction":
        result["message"] = result["message"].replace("TX-ES-102", "")
    elif defect == "wrong_timestamp":
        result["evidence"][0]["as_of"] = "2026-01-01T00:00:00+00:00"
    elif defect == "wrong_source":
        result["evidence"][0]["source"] = "model_generated_claim"
    elif defect == "wrong_provenance":
        result["evidence"][0]["provenance"] = "team_authored_synthetic"
    elif defect == "wrong_language":
        result["message"] = result["message"].replace(
            "esperando tu respuesta", "aguardando sua resposta"
        )
    elif defect == "missing_evidence":
        result["evidence"] = None
    assert not grounded_case_lookup(result, stored, "es")


@pytest.mark.parametrize("defect", ["generic_answer", "foreign_returned_case"])
def test_http_scorer_does_not_reward_case_endpoint_for_an_incorrect_chat(
    tmp_path, monkeypatch, defect
):
    app = create_app(str(tmp_path / "scorer.sqlite"), enable_external=False)
    app.state.classifier = lambda message, language: {
        "intent": "human" if "hablar con una persona" in message else "case_status",
        "confidence": 1.0,
        "model_version": "evaluation-boundary-test",
        "signals": [],
    }
    original = system_evaluation.chat

    def incorrect_chat(*args, **kwargs):
        response = original(*args, **kwargs)
        result = response.json()
        if result.get("state") == "case_lookup":
            if defect == "generic_answer":
                result.update(message="Consulta Mis casos.", cases=[], evidence=[])
            else:
                result["cases"][0]["id"] = "CASE-FOREIGN1234"
            return httpx.Response(200, json=result, request=response.request)
        return response

    monkeypatch.setattr(system_evaluation, "chat", incorrect_chat)
    result = scenario(
        app,
        {
            "id": "case-lookup-false-grounding",
            "semantic_group": "case-lookup-false-grounding",
            "language": "es",
            "intent": "case_status",
            "text": "Quiero consultar mi caso.",
        },
    )
    assert result["final_state"] == "case_lookup" and not result["grounded_case_lookup"]
    assert not result["correct_outcome"] and not result["successful_automated_resolution"]
    assert result["materially_wrong_outcome"]
    assert result["unauthorized_disclosure_or_action"] == (defect == "foreign_returned_case")
    with app.state.store.connect() as db:
        assert db.execute("SELECT count(*) FROM cases").fetchone()[0] == 1

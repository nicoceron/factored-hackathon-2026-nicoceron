"""Authored final-review regressions, outside all frozen evaluation corpora."""

import pytest

from factored_banking.fixtures import transactions
from factored_banking.language import classify
from factored_banking.privacy import REPORT_LIMIT, customer_report
from factored_banking.references import resolve_reference
from factored_banking.workflow import run


def offered_context(intent="transaction_status", report=""):
    return {
        "pending_intent": intent,
        "customer_report": report,
        "transaction_candidates": [row["id"] for row in transactions("demo-es")],
    }


@pytest.mark.parametrize(
    "message,locale",
    [
        ("Foi a de segunda-feira", "pt"),
        ("Espera un segundo", "es"),
        ("Es la primera vez que veo ese cobro", "es"),
        ("É a primeira vez que vejo essa cobrança", "pt"),
        ("Fue el primero de mes", "es"),
        ("Foi no segundo dia do mês", "pt"),
        ("No es la primera operación", "es"),
        ("Não é a segunda transação", "pt"),
    ],
)
def test_ordinal_calendar_duration_and_first_time_uses_do_not_select_a_record(message, locale):
    records = transactions("demo-es")
    context = offered_context()
    reference = resolve_reference(message, context, records)
    assert not reference.mentioned
    assert len(reference.candidates) == 3
    result = run(message, locale, None, context, records, classify)
    assert result["state"] == "clarification"
    assert "transaction" not in result
    assert result["receipt"] is None


@pytest.mark.parametrize(
    "message,locale,index",
    [
        ("la primera", "es", 0),
        ("es la primera operación", "es", 0),
        ("Elijo la operación tercera", "es", 2),
        ("a segunda", "pt", 1),
        ("é a segunda transação", "pt", 1),
        ("Escolho a terceira opção, por favor", "pt", 2),
        ("No reconozco la primera operación", "es", 0),
        ("Não reconheço a segunda transação", "pt", 1),
    ],
)
def test_affirmative_ordinals_select_only_the_displayed_scoped_order(message, locale, index):
    records = transactions("demo-es")
    context = offered_context()
    reference = resolve_reference(message, context, records)
    assert reference.mentioned
    assert [row["id"] for row in reference.candidates] == [records[index]["id"]]
    result = run(message, locale, None, context, records, classify)
    assert result["transaction"]["id"] == records[index]["id"]
    assert result["state"] in {"resolved", "awaiting_confirmation"}


@pytest.mark.parametrize("message", ["La primera o la segunda", "A primeira ou a terceira"])
def test_multiple_ordinal_choices_stay_ambiguous(message):
    result = run(
        message,
        "pt" if message.startswith("A ") else "es",
        None,
        offered_context(),
        transactions("demo-es"),
        classify,
    )
    assert result["state"] == "clarification"
    assert len(result["transaction_options"]) == 2
    assert "transaction" not in result


def test_ordinal_without_a_previous_list_never_selects_a_record():
    reference = resolve_reference("la primera operación", {}, transactions("demo-es"))
    assert not reference.mentioned
    assert len(reference.candidates) == 3


@pytest.mark.parametrize(
    "initial,followup,locale",
    [
        ("No reconozco un cargo", "El de Tienda Demo, fue después de una llamada", "es"),
        ("Não reconheço uma cobrança", "O da Tienda Demo, foi depois de uma ligação", "pt"),
        ("No reconozco un cargo", "Fue después de una llamada; pidieron mi PIN 1234", "es"),
        ("Não reconheço uma cobrança", "Foi depois de uma ligação; pediram meu OTP 654321", "pt"),
    ],
)
def test_meaningful_followup_keeps_original_allegation_and_added_redacted_details(
    initial, followup, locale
):
    records = transactions("demo-es")
    first = run(initial, locale, None, {}, records, classify)
    assert first["state"] == "clarification"
    next_turn = run(followup, locale, None, first["context"], records, classify)
    assert next_turn["state"] in {"clarification", "awaiting_confirmation"}
    report = next_turn["context"]["customer_report"]
    assert initial in report
    assert ("llamada" if locale == "es" else "ligação") in report
    if "PIN" in followup or "OTP" in followup:
        assert "[REDACTED]" in report
        assert "1234" not in report and "654321" not in report
    if next_turn["state"] == "awaiting_confirmation":
        assert next_turn["proposal_payload"]["customer_report"] == report
        assert next_turn["proposal_payload"]["report_provenance"] == (
            "customer_allegation_redacted_not_verified"
        )


@pytest.mark.parametrize(
    "reply,locale",
    [
        ("la segunda", "es"),
        ("Es la segunda operación", "es"),
        ("a segunda", "pt"),
        ("TX-ES-102", "es"),
        ("2", "pt"),
    ],
)
def test_selection_only_reply_does_not_pollute_the_report(reply, locale):
    original = "No reconozco este cargo y necesito revisión"
    context = offered_context("dispute", original)
    result = run(reply, locale, None, context, transactions("demo-es"), classify)
    assert result["state"] == "awaiting_confirmation"
    assert result["proposal_payload"]["customer_report"] == original
    assert result["transaction"]["id"] == "TX-ES-102"


@pytest.mark.parametrize("message,locale", [("Gracias", "es"), ("Obrigada", "pt")])
def test_courtesy_does_not_modify_pending_report_or_selection(message, locale):
    context = offered_context("dispute", "No reconozco un cargo")
    result = run(message, locale, None, context, transactions("demo-es"), classify)
    assert result["context"] == context
    assert result["receipt"] is None


@pytest.mark.parametrize(
    "new_request,locale",
    [
        ("Quiero saber el estado del pago de Tienda Demo", "es"),
        ("Quero saber o estado do pagamento de Tienda Demo", "pt"),
        ("Ahora no reconozco otra operación", "es"),
        ("Agora não reconheço outra transação", "pt"),
        ("Quiero hablar con una persona", "es"),
        ("Quero falar com uma pessoa", "pt"),
    ],
)
def test_explicit_new_request_supersedes_previous_allegation(new_request, locale):
    previous = "No reconozco un cargo que ocurrió después de una llamada"
    context = offered_context("dispute", previous)
    result = run(new_request, locale, None, context, transactions("demo-es"), classify)
    assert result["context"]["customer_report"] == new_request
    assert previous not in result["context"]["customer_report"]
    if "estado" in new_request:
        assert result["state"] == "resolved"
        assert result["intent"] == "transaction_status"


def test_report_merge_is_redacted_bounded_deduplicated_and_retains_both_ends():
    previous = "No reconozco un cargo. " + "a" * 1900
    current = "Pidieron mi PIN 1234 después de una llamada. " + "b" * 1900
    report = customer_report(current, {"customer_report": previous}, continuation=True)
    assert len(report) <= REPORT_LIMIT
    assert "No reconozco un cargo" in report
    assert "después de una llamada" in report
    assert "1234" not in report and "[REDACTED]" in report
    assert customer_report(report, {"customer_report": report}, continuation=True) == report

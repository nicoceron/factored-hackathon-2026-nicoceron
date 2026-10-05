"""Authored Opus follow-up regressions; evaluation corpora remain unchanged."""

import pytest

from factored_banking.fixtures import transactions
from factored_banking.language import classify
from factored_banking.references import resolve_reference
from factored_banking.workflow import run


def context(records):
    return {
        "pending_intent": "transaction_status",
        "transaction_candidates": [row["id"] for row in records],
    }


@pytest.mark.parametrize(
    "message",
    [
        "fiz a compra segunda",
        "o pagamento primeiro",
        "Fiz a transferência primeiro",
        "Pagué la compra primero",
        "No escolho a opção segunda",
        "No prefiero el primer cargo.",
        "Não prefiro a primeira cobrança.",
        "No quiero el primer cargo.",
        "Não quero a primeira cobrança.",
        "No selecciono el primer cargo.",
        "Não seleciono a primeira cobrança.",
        "Nunca prefiero el primer cargo.",
        "Jamais seleciono a primeira cobrança.",
        "No prefiero la operación tercera.",
        "Não prefiro o pagamento segundo.",
    ],
)
def test_post_noun_timing_and_negated_selection_keep_records_ambiguous(message):
    records = transactions("demo-es")
    reference = resolve_reference(message, context(records), records)
    assert not reference.mentioned
    assert not reference.selection_only
    assert len(reference.candidates) == len(records)
    result = run(message, "pt", None, context(records), records, classify)
    assert result["state"] == "clarification"
    assert "transaction" not in result and result["receipt"] is None


@pytest.mark.parametrize(
    "message,index",
    [
        ("el primer cargo", 0),
        ("el tercer movimiento", 2),
        ("No reconozco el primer cargo", 0),
        ("O problema está no primeiro pagamento", 0),
        ("Não reconheço a cobrança no primeiro pagamento", 0),
        ("a opção segunda", 1),
        ("Elijo la operación tercera", 2),
        ("Escolho o pagamento segundo", 1),
        ("Preciso de ajuda; escolho a transação terceira", 2),
    ],
)
def test_short_spanish_ordinals_and_explicit_choice_grammar_use_shown_order(message, index):
    records = transactions("demo-es")
    reference = resolve_reference(message, context(records), records)
    assert reference.mentioned
    assert [row["id"] for row in reference.candidates] == [records[index]["id"]]


def test_explicit_post_noun_multiple_choices_remain_ambiguous():
    records = transactions("demo-es")
    reference = resolve_reference(
        "Elijo el cargo primero o el cargo tercero", context(records), records
    )
    assert [row["id"] for row in reference.candidates] == [records[i]["id"] for i in (0, 2)]


def test_new_short_ordinal_forms_require_a_previously_shown_list():
    records = transactions("demo-es")
    reference = resolve_reference("el primer cargo", {}, records)
    assert not reference.mentioned and len(reference.candidates) == len(records)

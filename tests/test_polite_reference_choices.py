"""Authored final-review reference checks, outside the frozen evaluation corpora."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from factored_banking.api import create_app
from factored_banking.fixtures import transactions
from factored_banking.language import classify
from factored_banking.references import resolve_reference
from factored_banking.workflow import run


def offered(rows):
    return {
        "pending_intent": "dispute",
        "customer_report": "No reconozco un cargo.",
        "transaction_candidates": [row["id"] for row in rows],
    }


@pytest.mark.parametrize(
    "message",
    [
        "Estaba en casa.",
        "Eu estava em casa.",
        "Fue en línea.",
        "Foi em junho.",
        "Fue en junio.",
        "Fue en dólares.",
        "El cargo en casa.",
        "O pagamento em casa.",
        "La compra en línea.",
        "O pagamento em junho.",
        "El cargo en junio.",
        "El pago en dólares.",
    ],
)
def test_location_channel_month_and_currency_words_are_not_unknown_merchants(message):
    rows = transactions("demo-es")
    reference = resolve_reference(message, offered(rows), rows)
    assert not reference.mentioned and not reference.selection_only
    assert reference.candidates == rows


@pytest.mark.parametrize(
    "message",
    [
        "El cargo de Mercado Luna.",
        "El cobro de Comercio Inexistente.",
        "La compra de Estrella Desconocida.",
        "Na loja Estrela Inexistente.",
        "En la tienda X.",
        "¿Cuál es el estado del cargo en Heladería Norte?",
        "Qual é o estado do pagamento em Sorveteria Norte?",
    ],
)
def test_explicit_unknown_merchant_cannot_reuse_a_retained_record(message):
    rows = transactions("demo-es")
    context = {**offered(rows), "transaction_id": rows[0]["id"]}
    reference = resolve_reference(message, context, rows)
    assert reference.mentioned and not reference.candidates
    result = run(message, "es", None, context, rows, classify)
    assert result["state"] == "clarification" and not result.get("transaction")
    assert not result.get("proposal_payload") and result["receipt"] is None


def test_known_merchant_keeps_exact_match_with_unrelated_location_details():
    rows = [
        {**row, "id": "AUTH-" + str(index), "merchant": merchant}
        for index, (row, merchant) in enumerate(
            zip(
                transactions("demo-es"),
                ["Casa Aurora", "Loja Estrela", "Mercado Sol"],
                strict=True,
            )
        )
    ]
    reference = resolve_reference(
        "Foi na Loja Estrela; meu cartão ficou comigo e eu estava em casa.", offered(rows), rows
    )
    assert reference.mentioned and not reference.selection_only
    assert [row["id"] for row in reference.candidates] == ["AUTH-1"]


PURE_CHOICES = [
    "La segunda, por favor",
    "Sí, la segunda",
    "Quero a segunda",
    "La 2 por favor",
    "Sim, a segunda, por favor",
    "A opção 2, por favor",
]
DETAIL_CHOICES = [
    "A segunda. Meu cartão ficou comigo e eu estava em casa.",
    "Quero a segunda. Meu cartão ficou comigo e eu estava em casa.",
    "La segunda; mi tarjeta se quedó conmigo y yo estaba en casa.",
    "La 2, por favor. Mi tarjeta se quedó conmigo.",
]


@pytest.mark.parametrize("message", PURE_CHOICES + DETAIL_CHOICES)
def test_polite_and_leading_choices_confirm_exact_record_without_losing_report(tmp_path, message):
    app = create_app(str(tmp_path / "choice.sqlite"), enable_external=False)
    with TestClient(app) as client:
        session = client.post("/api/session", json={}).json()
        client.headers["X-CSRF-Token"] = session["csrf_token"]
        original = "No reconozco un cargo."
        initial = client.post(
            "/api/chat", json={"message": original, "idempotency_key": str(uuid4())}
        ).json()
        assert initial["state"] == "clarification"
        assert len(initial["transaction_options"]) == 3
        request = {"message": message, "idempotency_key": str(uuid4())}
        response = client.post("/api/chat", json=request)
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["intent"] == "dispute" and result["state"] == "awaiting_confirmation"
        proposal = result["proposal"]
        assert proposal["transaction"]["id"] == "TX-ES-102"
        assert proposal["transaction"]["currency"] == "COP"
        assert proposal["transaction"]["amount"] == "129000.00"
        report = original if message in PURE_CHOICES else original + "\n" + message
        assert proposal["customer_report"] == report
        assert result["receipt"] is None
        assert client.post("/api/chat", json=request).json() == result
        assert client.get("/api/cases").json()["cases"] == []
        confirmed = client.post(
            "/api/actions/confirm",
            json={"proposal_id": proposal["id"], "idempotency_key": str(uuid4())},
        )
        assert confirmed.status_code == 200
        receipt = confirmed.json()["receipt"]
        assert receipt["verified"]
        stored = client.get("/api/cases/" + receipt["id"]).json()
        assert stored["customer_report"] == report
        assert stored["transaction"]["id"] == "TX-ES-102"


@pytest.mark.parametrize("message", PURE_CHOICES)
def test_pure_choices_use_current_displayed_order(message):
    rows = transactions("demo-es")
    context = {**offered(rows), "transaction_candidates": [rows[2]["id"], rows[0]["id"]]}
    reference = resolve_reference(message, context, rows)
    assert reference.selection_only and reference.choice_reply
    assert [row["id"] for row in reference.candidates] == [rows[0]["id"]]


@pytest.mark.parametrize(
    "message",
    [
        "Me cobraron un segundo cargo.",
        "Recibí una segunda compra.",
        "Recebi um segundo pagamento.",
        "Foi uma segunda cobrança.",
    ],
)
def test_indefinite_duplicate_charge_does_not_select_list_position(message):
    rows = transactions("demo-es")
    reference = resolve_reference(message, offered(rows), rows)
    assert not reference.mentioned and not reference.selection_only
    assert reference.candidates == rows


@pytest.mark.parametrize("amount,expected", [("129000", ["TX-ES-102"]), ("84000", [])])
def test_option_number_is_not_amount_and_later_exact_amount_remains_a_constraint(amount, expected):
    rows = transactions("demo-es")
    reference = resolve_reference("La 2. El importe fue " + amount + " COP.", offered(rows), rows)
    assert not reference.selection_only
    assert [row["id"] for row in reference.candidates] == expected


@pytest.mark.parametrize("message", DETAIL_CHOICES)
def test_leading_choice_with_details_has_choice_intent_without_suppressing_report(message):
    rows = transactions("demo-es")
    reference = resolve_reference(message, offered(rows), rows)
    assert reference.choice_reply and not reference.selection_only
    assert [row["id"] for row in reference.candidates] == [rows[1]["id"]]


def test_leading_multiple_choices_with_report_details_remain_genuinely_ambiguous():
    rows = transactions("demo-es")
    reference = resolve_reference(
        "A primeira ou a segunda. Meu cartão ficou comigo e eu estava em casa.", offered(rows), rows
    )
    assert reference.mentioned and not reference.selection_only
    assert [row["id"] for row in reference.candidates] == [rows[0]["id"], rows[1]["id"]]


@pytest.mark.parametrize("message", ["La primera. La 2.", "A primeira; a opção 2."])
def test_word_and_numeric_choices_in_different_clauses_remain_ambiguous(message):
    rows = transactions("demo-es")
    reference = resolve_reference(message, offered(rows), rows)
    assert reference.mentioned
    assert [row["id"] for row in reference.candidates] == [rows[0]["id"], rows[1]["id"]]


@pytest.mark.parametrize(
    "message",
    [
        "La segunda, no la segunda.",
        "A segunda, não a segunda.",
        "La 2, no la 2.",
        "A 2, não a 2.",
        "La segunda, no la 2.",
        "A 2, não a segunda.",
    ],
)
def test_retracted_word_or_numeric_choice_cannot_attach_the_retracted_record(message):
    rows = transactions("demo-es")
    context = {
        **offered(rows),
        "pending_intent": "transaction_status",
        "transaction_id": rows[1]["id"],
    }
    reference = resolve_reference(message, context, rows)
    assert reference.mentioned and not reference.candidates and not reference.selection_only
    result = run(message, "es", None, context, rows, classify)
    assert result["state"] == "clarification" and not result.get("transaction")
    assert not result.get("proposal_payload") and result["receipt"] is None


@pytest.mark.parametrize(
    "message",
    [
        "La segunda, no la primera.",
        "A segunda, não a primeira.",
        "La 2, no la primera.",
        "A segunda, não a 1.",
        "No, la segunda.",
    ],
)
def test_distinct_rejected_option_and_separate_no_correction_keep_affirmative_choice(message):
    rows = transactions("demo-es")
    reference = resolve_reference(message, offered(rows), rows)
    assert reference.mentioned
    assert [row["id"] for row in reference.candidates] == [rows[1]["id"]]


@pytest.mark.parametrize(
    "message",
    [
        "No quiero la segunda, por favor.",
        "Não quero a segunda, por favor.",
        "No quiero la 2, por favor.",
        "Não quero a 2, por favor.",
    ],
)
def test_polite_negative_choice_never_selects_a_record(message):
    rows = transactions("demo-es")
    reference = resolve_reference(message, offered(rows), rows)
    assert not reference.mentioned and not reference.selection_only
    assert reference.candidates == rows


DECIMAL_REPLIES = [
    ("38.50", "TX-PT-102"),
    ("38,50", "TX-PT-102"),
    ("Foi a de 16,75.", "TX-PT-103"),
]


@pytest.mark.parametrize("message,transaction_id", DECIMAL_REPLIES)
def test_portuguese_decimal_amount_reply_resolves_scoped_record_and_recorded_status(
    tmp_path, message, transaction_id
):
    expected = next(row for row in transactions("demo-pt") if row["id"] == transaction_id)
    with TestClient(
        create_app(str(tmp_path / "pt-status.sqlite"), enable_external=False)
    ) as client:
        session = client.post(
            "/api/session", json={"persona": "customer_pt", "language": "pt"}
        ).json()
        client.headers["X-CSRF-Token"] = session["csrf_token"]
        first = client.post(
            "/api/chat",
            json={"message": "Qual é o estado do pagamento?", "idempotency_key": str(uuid4())},
        ).json()
        assert first["state"] == "clarification" and first["language"] == "pt"
        assert len(first["transaction_options"]) == 3
        request = {"message": message, "idempotency_key": str(uuid4())}
        response = client.post("/api/chat", json=request)
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["state"] == "resolved" and result["intent"] == "transaction_status"
        assert result["language"] == "pt" and result["transaction"] == expected
        assert expected["amount"] in result["message"] and expected["currency"] in result["message"]
        assert ("pendente" if expected["status"] == "pending" else "recusada") in result["message"]
        assert any(item["source"] == expected["source"] for item in result["evidence"])
        assert result["proposal"] is None and result["receipt"] is None
        assert client.post("/api/chat", json=request).json() == result
        assert client.get("/api/cases").json()["cases"] == []
        restored = client.get("/api/session").json()
        assert restored["demo_persona"] == "customer_pt" and restored["user"]["language"] == "pt"


@pytest.mark.parametrize("message,transaction_id", DECIMAL_REPLIES)
def test_portuguese_decimal_dispute_reply_preserves_report_until_verified_confirmation(
    tmp_path, message, transaction_id
):
    expected = next(row for row in transactions("demo-pt") if row["id"] == transaction_id)
    with TestClient(
        create_app(str(tmp_path / "pt-dispute.sqlite"), enable_external=False)
    ) as client:
        session = client.post(
            "/api/session", json={"persona": "customer_pt", "language": "pt"}
        ).json()
        client.headers["X-CSRF-Token"] = session["csrf_token"]
        original = "Não reconheço uma cobrança."
        first = client.post(
            "/api/chat", json={"message": original, "idempotency_key": str(uuid4())}
        ).json()
        assert first["state"] == "clarification" and first["intent"] == "dispute"
        request = {"message": message, "idempotency_key": str(uuid4())}
        response = client.post("/api/chat", json=request)
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["state"] == "awaiting_confirmation" and result["intent"] == "dispute"
        assert result["language"] == "pt" and result["transaction"] == expected
        assert result["proposal"]["transaction"]["id"] == expected["id"]
        assert result["proposal"]["transaction"]["amount"] == expected["amount"]
        assert result["proposal"]["transaction"]["currency"] == "USD"
        report = original + ("\n" + message if message.startswith("Foi") else "")
        assert result["proposal"]["customer_report"] == report
        assert result["receipt"] is None and client.get("/api/cases").json()["cases"] == []
        assert client.post("/api/chat", json=request).json() == result
        restored = client.get("/api/session").json()
        assert restored["proposal"]["customer_report"] == report
        confirmation = {"proposal_id": result["proposal"]["id"], "idempotency_key": str(uuid4())}
        confirmed = client.post("/api/actions/confirm", json=confirmation)
        assert confirmed.status_code == 200, confirmed.text
        assert confirmed.json()["receipt"]["verified"]
        assert client.post("/api/actions/confirm", json=confirmation).json() == confirmed.json()
        stored = client.get("/api/cases/" + confirmed.json()["receipt"]["id"]).json()
        assert stored["customer_report"] == report and stored["transaction"]["id"] == expected["id"]
        assert len(stored["timeline"]) == 1 and len(client.get("/api/cases").json()["cases"]) == 1


@pytest.mark.parametrize(
    "message,expected",
    [
        ("A opção 2. O valor é 38,50 USD.", ["TX-PT-102"]),
        ("38.50. A opção 2.", ["TX-PT-102"]),
        ("38,50; a opção 3.", []),
        ("A opção 2, não a 2. O valor foi 38.50.", []),
        ("A opção 9. O valor foi 38,50 USD.", []),
        ("A 2. A 3.", ["TX-PT-102", "TX-PT-103"]),
    ],
)
def test_decimal_amounts_preserve_option_conflicts_retractions_and_invalid_choice_rejection(
    message, expected
):
    rows = transactions("demo-pt")
    context = {**offered(rows), "transaction_id": rows[1]["id"]}
    reference = resolve_reference(message, context, rows)
    assert reference.mentioned
    assert [row["id"] for row in reference.candidates] == expected
    if not expected:
        result = run(message, "pt", None, context, rows, classify)
        assert result["state"] == "clarification" and not result.get("transaction")
        assert not result.get("proposal_payload") and result["receipt"] is None

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


@pytest.mark.parametrize(
    "persona,locale,amount", [("customer_es", "es", "129000"), ("customer_pt", "pt", "38")]
)
@pytest.mark.parametrize("separator", [".", ","])
@pytest.mark.parametrize("start", ["offered_status", "offered_dispute", "retained_status"])
def test_rejected_amount_never_attaches_an_offered_or_retained_record(
    tmp_path, persona, locale, amount, separator, start
):
    with TestClient(create_app(str(tmp_path / "rejected.sqlite"), enable_external=False)) as client:
        session = client.post("/api/session", json={"persona": persona, "language": locale}).json()
        client.headers["X-CSRF-Token"] = session["csrf_token"]
        original = "No reconozco un cargo." if locale == "es" else "Não reconheço uma cobrança."
        initial = (
            original
            if start == "offered_dispute"
            else (
                "¿Cuál es el estado del pago?"
                if locale == "es"
                else "Qual é o estado do pagamento?"
            )
        )
        if start == "retained_status":
            initial += " Tienda Demo"
        first = client.post(
            "/api/chat", json={"message": initial, "idempotency_key": str(uuid4())}
        ).json()
        assert first["state"] == ("resolved" if start == "retained_status" else "clarification")
        value = amount + separator + ("00" if locale == "es" else "50")
        rejected = ("No la de " if locale == "es" else "Não a de ") + value + "."
        request = {"message": rejected, "idempotency_key": str(uuid4())}
        result = client.post("/api/chat", json=request).json()
        assert result["state"] == "clarification" and result["language"] == locale
        assert (
            result.get("transaction") is None
            and result["proposal"] is None
            and result["receipt"] is None
        )
        assert client.post("/api/chat", json=request).json() == result
        restored = client.get("/api/session").json()
        assert restored["demo_persona"] == persona and restored["proposal"] is None
        assert client.get("/api/cases").json()["cases"] == []
        if start == "offered_dispute":
            assert original in restored["context"]["customer_report"]
            currency = "COP" if locale == "es" else "USD"
            selected = client.post(
                "/api/chat",
                json={"message": value + " " + currency, "idempotency_key": str(uuid4())},
            ).json()
            assert selected["state"] == "awaiting_confirmation" and selected["intent"] == "dispute"
            assert selected["proposal"]["customer_report"].startswith(original)
            assert selected["proposal"]["transaction"]["id"] == "TX-" + locale.upper() + "-102"
            confirmation = {
                "proposal_id": selected["proposal"]["id"],
                "idempotency_key": str(uuid4()),
            }
            confirmed = client.post("/api/actions/confirm", json=confirmation).json()
            assert confirmed["receipt"]["verified"]
            assert client.post("/api/actions/confirm", json=confirmation).json() == confirmed
            stored = client.get("/api/cases/" + confirmed["receipt"]["id"]).json()
            assert stored["customer_report"] == selected["proposal"]["customer_report"]
            assert stored["transaction"]["id"] == "TX-" + locale.upper() + "-102"
            assert len(stored["timeline"]) == 1


@pytest.mark.parametrize(
    "persona,locale,message,transaction_id",
    [
        ("customer_es", "es", "No autoricé el cargo de 129000,00 COP.", "TX-ES-102"),
        ("customer_pt", "pt", "Não reconheço a cobrança de 38.50 USD.", "TX-PT-102"),
    ],
)
def test_authorization_denial_is_not_rejected_amount_selection(
    tmp_path, persona, locale, message, transaction_id
):
    with TestClient(create_app(str(tmp_path / "denial.sqlite"), enable_external=False)) as client:
        session = client.post("/api/session", json={"persona": persona, "language": locale}).json()
        client.headers["X-CSRF-Token"] = session["csrf_token"]
        request = {"message": message, "idempotency_key": str(uuid4())}
        result = client.post("/api/chat", json=request).json()
        assert result["state"] == "awaiting_confirmation" and result["intent"] == "dispute"
        assert result["proposal"]["transaction"]["id"] == transaction_id
        assert result["proposal"]["customer_report"] == message and result["receipt"] is None
        assert client.post("/api/chat", json=request).json() == result
        confirmation = {"proposal_id": result["proposal"]["id"], "idempotency_key": str(uuid4())}
        confirmed = client.post("/api/actions/confirm", json=confirmation).json()
        assert confirmed["receipt"]["verified"]
        assert client.post("/api/actions/confirm", json=confirmation).json() == confirmed
        stored = client.get("/api/cases/" + confirmed["receipt"]["id"]).json()
        assert (
            stored["transaction"]["id"] == transaction_id and stored["customer_report"] == message
        )


@pytest.mark.parametrize("message", ["38,50 reais", "38.50 BRL", "38.50 euros", "38,50 EUR"])
@pytest.mark.parametrize("dispute", [False, True])
def test_explicit_currency_mismatch_cannot_attach_usd_fixture_or_change_identity(
    tmp_path, message, dispute
):
    with TestClient(create_app(str(tmp_path / "currency.sqlite"), enable_external=False)) as client:
        session = client.post(
            "/api/session", json={"persona": "customer_pt", "language": "pt"}
        ).json()
        client.headers["X-CSRF-Token"] = session["csrf_token"]
        original = (
            "Não reconheço uma cobrança."
            if dispute
            else "Qual é o estado do pagamento na Tienda Demo?"
        )
        first = client.post(
            "/api/chat", json={"message": original, "idempotency_key": str(uuid4())}
        ).json()
        assert first["state"] == ("clarification" if dispute else "resolved")
        request = {"message": message, "idempotency_key": str(uuid4())}
        result = client.post("/api/chat", json=request).json()
        assert result["state"] == "clarification" and result.get("transaction") is None
        assert result["proposal"] is None and result["receipt"] is None
        assert client.post("/api/chat", json=request).json() == result
        restored = client.get("/api/session").json()
        assert restored["demo_persona"] == "customer_pt" and restored["proposal"] is None
        if dispute:
            assert original in restored["context"]["customer_report"]
        assert client.get("/api/cases").json()["cases"] == []


@pytest.mark.parametrize("locale,message", [("pt", "38.50 dólares"), ("es", "38,50 dólares")])
def test_matching_currency_alias_preserves_portuguese_customer_identity_and_exact_usd_evidence(
    tmp_path, locale, message
):
    with TestClient(create_app(str(tmp_path / "usd.sqlite"), enable_external=False)) as client:
        session = client.post(
            "/api/session", json={"persona": "customer_pt", "language": locale}
        ).json()
        client.headers["X-CSRF-Token"] = session["csrf_token"]
        first = (
            "Qual é o estado do pagamento?" if locale == "pt" else "¿Cuál es el estado del pago?"
        )
        assert (
            client.post(
                "/api/chat", json={"message": first, "idempotency_key": str(uuid4())}
            ).json()["state"]
            == "clarification"
        )
        result = client.post(
            "/api/chat", json={"message": message, "idempotency_key": str(uuid4())}
        ).json()
        assert result["state"] == "resolved" and result["transaction"]["id"] == "TX-PT-102"
        assert (
            result["transaction"]["amount"] == "38.50"
            and result["transaction"]["currency"] == "USD"
        )
        assert result["proposal"] is None and result["receipt"] is None
        assert client.get("/api/session").json()["demo_persona"] == "customer_pt"


@pytest.mark.parametrize(
    "message,expected",
    [
        ("38.50 dólares", ["usd"]),
        ("Reais 38,50", ["brl"]),
        ("38.50 euros", ["eur"]),
        ("38,50 pesos", ["cop", "ars", "mxn"]),
        ("38.50 pesos colombianos", ["cop"]),
        ("38.50 pesos argentinos", ["ars"]),
        ("38.50 pesos mexicanos", ["mxn"]),
        ("38.50 JPY", ["jpy"]),
        ("38.50 USD BRL", []),
        ("A opção 2. O valor é 38.50 reais.", ["brl"]),
        ("A opção 1. O valor é 38.50 reais.", []),
        ("El pago en dólares.", ["usd"]),
    ],
)
def test_currency_evidence_intersects_amount_record_and_shown_order_without_collapsing_peso_family(
    message, expected
):
    rows = [
        {
            **transactions("demo-pt")[1],
            "id": "AUTH-" + currency.upper(),
            "currency": currency.upper(),
            "merchant": None,
        }
        for currency in ["usd", "brl", "eur", "cop", "ars", "mxn", "jpy"]
    ]
    reference = resolve_reference(message, offered(rows), rows)
    assert reference.mentioned
    assert [row["currency"].lower() for row in reference.candidates] == expected


@pytest.mark.parametrize("merchant", ["Mercado Euro", "Café Dólar", "Loja USD"])
def test_currency_words_inside_exact_authorized_merchant_name_do_not_change_currency(merchant):
    row = {**transactions("demo-es")[0], "id": "AUTH-MERCHANT", "merchant": merchant}
    reference = resolve_reference("El cargo de " + merchant + " por 84000.00", {}, [row])
    assert reference.mentioned and reference.candidates == [row]


def test_currency_alias_conflicting_with_explicit_record_requires_clarification():
    rows = [
        {**transactions("demo-pt")[1], "id": "AUTH-USD", "merchant": None},
        {**transactions("demo-pt")[1], "id": "AUTH-BRL", "currency": "BRL", "merchant": None},
    ]
    result = run("AUTH-USD de 38.50 reais", "pt", None, offered(rows), rows, classify)
    assert result["state"] == "clarification" and not result.get("transaction")
    assert not result.get("proposal_payload") and result["receipt"] is None


def test_currency_letters_inside_scoped_record_id_are_not_monetary_evidence():
    row = {**transactions("demo-es")[0], "id": "AUTH-USD", "merchant": None}
    reference = resolve_reference("¿Cuál es el estado de AUTH-USD?", {}, [row])
    assert not reference.mentioned and reference.candidates == [row]


@pytest.mark.parametrize(
    "message,expected",
    [
        ("A segunda, não a de 16.75.", ["TX-PT-102"]),
        ("A segunda, não a de 38.50.", []),
        ("A de 16.75, não a de 38,50.", ["TX-PT-103"]),
        ("No, a de 38.50.", ["TX-PT-102"]),
    ],
)
def test_rejected_amount_intersects_affirmative_amount_and_ordinal_choices(message, expected):
    rows = transactions("demo-pt")
    reference = resolve_reference(message, offered(rows), rows)
    assert reference.mentioned and [row["id"] for row in reference.candidates] == expected

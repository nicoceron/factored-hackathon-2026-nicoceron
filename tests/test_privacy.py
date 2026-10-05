"""Minimize common ES/PT secret disclosures without losing financial context."""

import json

import pytest
from fastapi.testclient import TestClient

from factored_banking.api import create_app
from factored_banking.privacy import REDACTED, redact_text


@pytest.mark.parametrize(
    ("text", "secret", "label"),
    [
        ("Le dije mi PIN 1234 al supuesto agente", "1234", "PIN"),
        ("Pediu meu CVV 987 para cancelar a cobrança", "987", "CVV"),
        ("Entregué el OTP 654321 que me pidieron", "654321", "OTP"),
        ("O código de verificação 654321 foi solicitado", "654321", "código de verificação"),
        ("Mi código de acceso 456789 fue usado", "456789", "código de acceso"),
        ("Solicitaram o código de autenticação 987654", "987654", "código de autenticação"),
        ("Mi contraseña 7654 se la di por teléfono", "7654", "contraseña"),
        ("Informei minha senha 2345", "2345", "senha"),
        ("La clave de acceso 5432 fue expuesta", "5432", "clave de acceso"),
        ("Me solicitaron PIN: ８７６５", "8765", "PIN"),
        ("Le di mi PIN 8765.", "8765", "PIN"),
        ("Enviei o OTP 765 432.", "765 432", "OTP"),
    ],
)
def test_short_numeric_disclosures_redact_value_and_preserve_report_label(text, secret, label):
    redacted = redact_text(text)
    assert secret not in redacted
    assert label in redacted and REDACTED in redacted
    assert redact_text(redacted) == redacted


@pytest.mark.parametrize(
    "text",
    [
        "El cargo fue de 1234 COP el 2026-06-17 a las 12:45",
        "A cobrança foi de 987 USD na operação TX-PT-101",
        "El código de transacción 654321 aparece duplicado",
        "O código do estabelecimento 123456 consta no comprovante",
        "El PIN fue solicitado para cancelar el cargo de 1234 COP",
        "Pediram meu código de verificação depois da cobrança de 987 USD",
    ],
)
def test_preserve_amounts_dates_transaction_codes_and_reports_without_secret_values(text):
    assert redact_text(text) == text


def test_portuguese_verification_code_with_separator_is_also_minimized():
    text = "O código de verificação é teste123 e recebi uma cobrança de 24 USD"
    assert redact_text(text) == "O [REDACTED] e recebi uma cobrança de 24 USD"


@pytest.mark.parametrize("case_id", ["CASE-315129026091", "case-31a129b2609f"])
def test_complete_sandbox_case_references_survive_redaction(case_id):
    text = f"Caso {case_id} guardado el 2026-06-17."
    assert redact_text(text) == text
    assert redact_text(redact_text(text)) == text


def test_case_reference_exemption_does_not_preserve_phone_card_or_incomplete_tokens():
    case_id = "CASE-315129026091"
    text = (
        f"Caso {case_id}. +57 300 123 4567. 4111 1111 1111 1111. "
        "Teléfono: 300 987 6543. Tarjeta: 5555 5555 5555 4444. "
        "CASE-3151290260912. PIN: CASE-315129026091."
    )
    redacted = redact_text(text)
    assert redacted.count(case_id) == 1
    for private_value in (
        "300 123 4567",
        "4111 1111 1111 1111",
        "300 987 6543",
        "5555 5555 5555 4444",
        "3151290260912",
    ):
        assert private_value not in redacted
    assert redacted.count(REDACTED) == 6
    assert redact_text(redacted) == redacted


@pytest.mark.parametrize(
    ("persona", "message"),
    [
        (
            "customer_es",
            "No reconozco el cargo TX-ES-101. Mi teléfono es +57 300 123 4567 "
            "y mi tarjeta 4111 1111 1111 1111.",
        ),
        (
            "customer_pt",
            "Não reconheço a cobrança TX-PT-101. Meu telefone é +57 300 123 4567 "
            "e meu cartão 4111 1111 1111 1111.",
        ),
    ],
)
def test_numeric_case_receipt_survives_verified_confirmation_and_history_reload(
    tmp_path, monkeypatch, persona, message
):
    import factored_banking.api as banking_api

    original_token_hex = banking_api.secrets.token_hex
    monkeypatch.setattr(
        banking_api.secrets,
        "token_hex",
        lambda size: "315129026091" if size == 6 else original_token_hex(size),
    )
    app = create_app(str(tmp_path / "numeric-case.sqlite"), enable_external=False)
    with TestClient(app) as client:
        login = client.post("/api/session", json={"persona": persona})
        client.headers["X-CSRF-Token"] = login.json()["csrf_token"]
        proposed = client.post(
            "/api/chat", json={"message": message, "idempotency_key": "numeric-case-chat"}
        ).json()
        assert proposed["state"] == "awaiting_confirmation"
        payload = {
            "proposal_id": proposed["proposal"]["id"],
            "idempotency_key": "numeric-case-confirm",
        }
        confirmed = client.post("/api/actions/confirm", json=payload)
        assert confirmed.status_code == 200
        result = confirmed.json()
        case_id = "CASE-315129026091"
        assert result["receipt"]["id"] == case_id and result["receipt"]["verified"]
        assert case_id in result["message"]
        restored = client.get("/api/session").json()
        history = restored["context"]["history"]
        assert history[-1] == {"role": "assistant", "content": result["message"]}
        assert case_id in history[-1]["content"]
        assert "300 123 4567" not in json.dumps(history)
        assert "4111 1111 1111 1111" not in json.dumps(history)
        saved = client.get(f"/api/cases/{case_id}").json()
        assert saved["id"] == case_id
        assert REDACTED in saved["customer_report"]
        assert "300 123 4567" not in saved["customer_report"]
        assert "4111 1111 1111 1111" not in saved["customer_report"]
        assert client.post("/api/actions/confirm", json=payload).json() == result
        assert client.get("/api/session").json()["context"]["history"] == history
        assert len(client.get(f"/api/cases/{case_id}").json()["timeline"]) == 1


def test_disclosed_secret_never_reaches_classifier_composer_or_persisted_case(tmp_path):
    app = create_app(str(tmp_path / "privacy.sqlite"), enable_external=False)
    received = []

    def classify(message, language):
        received.append(message)
        return {"intent": "scam", "signals": [], "model_version": "privacy-test"}

    def compose(message, language, result, history=None):
        received.append(message)
        return {"message": result["message"], "provider_meta": {"provider": "local"}}

    app.state.classifier = classify
    app.state.composer = compose
    with TestClient(app) as client:
        login = client.post("/api/session", json={"persona": "customer_es"})
        client.headers["X-CSRF-Token"] = login.json()["csrf_token"]
        response = client.post(
            "/api/chat",
            json={
                "message": "Me pidieron mi OTP 87654321 para cancelar un cargo de 1234 COP",
                "idempotency_key": "numeric-secret-report",
            },
        )
        assert response.status_code == 200
        result = response.json()
        receipt = client.post(
            "/api/actions/confirm",
            json={
                "proposal_id": result["proposal"]["id"],
                "idempotency_key": "numeric-secret-confirm",
            },
        )
        assert receipt.status_code == 200 and receipt.json()["receipt"]["verified"]
        stored = client.get("/api/cases").json()["cases"][0]
        assert "1234 COP" in stored["customer_report"]
        assert "OTP [REDACTED]" in stored["customer_report"]
        assert "87654321" not in json.dumps(stored)
    assert received and all("87654321" not in message for message in received)
    with app.state.store.connect() as db:
        for table in ("sessions", "proposals", "cases", "case_events", "requests"):
            rows = [dict(row) for row in db.execute(f"SELECT * FROM {table}")]
            assert "87654321" not in json.dumps(rows)

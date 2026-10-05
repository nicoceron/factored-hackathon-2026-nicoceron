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

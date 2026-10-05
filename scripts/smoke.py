"""Exercise the deployed sandbox API without transmitting any organizer records."""

import argparse
import json
import uuid
from http.cookiejar import CookieJar
from urllib.request import HTTPCookieProcessor, Request, build_opener


def check(base_url):
    browser = build_opener(HTTPCookieProcessor(CookieJar()))
    csrf = None

    def call(path, body=None, method=None):
        headers = {"Content-Type": "application/json"}
        if csrf:
            headers["X-CSRF-Token"] = csrf
        request = Request(
            base_url.rstrip("/") + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers=headers,
            method=method,
        )
        with browser.open(request, timeout=90) as response:
            assert response.status == 200
            return json.load(response)

    assert call("/readyz")["ready"]
    for language, persona, prefix, message in [
        ("es", "customer_es", "ES", "No reconozco el cargo de Mercado Demo"),
        ("pt", "customer_pt", "PT", "Não reconheço a cobrança de Mercado Demo"),
    ]:
        csrf = call("/api/session", {"persona": persona, "language": language})["csrf_token"]
        transactions = call("/api/transactions")["transactions"]
        tx = transactions[0]
        assert tx["id"].startswith("TX-" + prefix)

        def chat(text):
            return call("/api/chat", {"message": text, "idempotency_key": str(uuid.uuid4())})

        options = chat(
            "Quiero consultar un movimiento."
            if language == "es"
            else "Quero consultar uma transação."
        )
        assert {row["id"] for row in options["transaction_options"]} == {
            row["id"] for row in transactions
        }
        selected = chat("La segunda" if language == "es" else "A segunda")
        assert selected["transaction"]["id"] == transactions[1]["id"]
        switched = chat(
            "Qual é o valor da cobrança de Tienda Demo?"
            if language == "es"
            else "¿Cuál es el importe del cargo de Tienda Demo?"
        )
        assert switched["language"] == ("pt" if language == "es" else "es")
        assert switched["transaction"] == transactions[1]
        assert call("/api/session")["demo_persona"] == persona
        result = call(
            "/api/chat",
            {
                "message": message,
                "idempotency_key": str(uuid.uuid4()),
            },
        )
        assert result["state"] == "awaiting_confirmation", result
        payload = {"proposal_id": result["proposal"]["id"], "idempotency_key": str(uuid.uuid4())}
        first = call("/api/actions/confirm", payload)
        assert first["receipt"]["verified"]
        assert first == call("/api/actions/confirm", payload)
        case = call("/api/cases/" + first["receipt"]["case_id"])
        assert case["transaction"]["id"] == tx["id"]
        assert case["customer_report"] == message
        case_url = "/api/cases/" + case["id"]
        csrf = call("/api/session", {"persona": "analyst", "language": language})["csrf_token"]
        question = (
            "¿Recuerdas cuándo viste el cargo por primera vez?"
            if language == "es"
            else "Você lembra quando viu a cobrança pela primeira vez?"
        )
        review = {
            "resolution": "needs_information",
            "question": question,
            "idempotency_key": str(uuid.uuid4()),
        }
        asked = call(case_url + "/resolve", review)
        assert asked["receipt"]["verified"] and asked["pending_question"]["text"] == question
        assert call(case_url + "/resolve", review) == asked
        csrf = call("/api/session", {"persona": persona, "language": language})["csrf_token"]
        answer = {
            "message": "Ayer por la tarde." if language == "es" else "Ontem à tarde.",
            "question_id": asked["pending_question"]["id"],
            "idempotency_key": str(uuid.uuid4()),
        }
        replied = call(case_url + "/messages", answer)
        assert replied["receipt"]["verified"] and replied["status"] == "open"
        assert replied["pending_question"] is None
        assert call(case_url + "/messages", answer) == replied
        csrf = call("/api/session", {"persona": "analyst", "language": language})["csrf_token"]
        closed = call(
            case_url + "/resolve",
            {"resolution": "reviewed_closed", "idempotency_key": str(uuid.uuid4())},
        )
        assert closed["status"] == "reviewed_closed"
        assert [e["type"] for e in closed["timeline"]] == [
            "case_created",
            "question_requested",
            "customer_reply",
            "review_closed",
        ]
        assert call(case_url)["timeline"] == closed["timeline"]
    csrf = call("/api/session", {"persona": "analyst", "language": "es"})["csrf_token"]
    cases = call("/api/cases")["cases"]
    assert len(cases) == 2
    assert all(case["status"] == "reviewed_closed" for case in cases)
    metrics = call("/api/analytics")
    assert metrics["total_requests"] >= 4
    call("/api/workspace", method="DELETE")
    print(
        json.dumps(
            {
                "url": base_url,
                "passed": True,
                "languages": ["es", "pt"],
                "chat_only_reference_and_ordinal_verified": True,
                "automatic_language_switch_same_identity": True,
                "verified_cases": 2,
                "duplicate_writes": 0,
                "analyst_resolution": True,
                "specific_report_preserved": True,
                "two_way_followup_verified": True,
                "complete_case_history_verified": True,
                "workspace_erased": True,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    check(parser.parse_args().url)

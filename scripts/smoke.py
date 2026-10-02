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
        ("es", "customer_es", "ES", "No reconozco este cargo"),
        ("pt", "customer_pt", "PT", "Não reconheço essa cobrança"),
    ]:
        csrf = call("/api/session", {"persona": persona, "language": language})["csrf_token"]
        tx = call("/api/transactions")["transactions"][0]
        assert tx["id"].startswith("TX-" + prefix)
        result = call(
            "/api/chat",
            {
                "message": message,
                "language": language,
                "transaction_id": tx["id"],
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
    csrf = call("/api/session", {"persona": "analyst", "language": "es"})["csrf_token"]
    cases = call("/api/cases")["cases"]
    assert len(cases) == 2
    resolved = call("/api/cases/" + cases[0]["id"] + "/resolve", {"resolution": "reviewed_closed"})
    assert resolved["status"] == "reviewed_closed"
    metrics = call("/api/analytics")
    assert metrics["total_requests"] >= 4
    call("/api/workspace", method="DELETE")
    print(
        json.dumps(
            {
                "url": base_url,
                "passed": True,
                "languages": ["es", "pt"],
                "verified_cases": 2,
                "duplicate_writes": 0,
                "analyst_resolution": True,
                "workspace_erased": True,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    check(parser.parse_args().url)

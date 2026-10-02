"""Explicit team-authored examples, never copied from organizer customer records."""

AS_OF = "2026-06-17"
FIXTURE_VERSION = "claro-fixtures-v1"
PERSONAS = {
    "customer_es": {"customer": "demo-es", "role": "customer", "display_name": "Alex · Demo ES"},
    "customer_pt": {"customer": "demo-pt", "role": "customer", "display_name": "Sam · Demo PT"},
    "analyst": {"customer": None, "role": "analyst", "display_name": "Analyst · Demo"},
}


def transactions(customer):
    prefix = "ES" if customer == "demo-es" else "PT"
    if customer not in {"demo-es", "demo-pt"}:
        return []
    # USD is deliberate for the Portuguese fixture; BRL is absent from organizer coverage.
    currency = "COP" if prefix == "ES" else "USD"
    values = [
        (
            "101",
            "84000.00" if prefix == "ES" else "24.00",
            "completed",
            "Mercado Demo",
            "2026-06-16",
        ),
        ("102", "129000.00" if prefix == "ES" else "38.50", "pending", "Tienda Demo", "2026-06-17"),
        ("103", "56000.00" if prefix == "ES" else "16.75", "declined", None, "2026-06-15"),
    ]
    return [
        {
            "id": f"TX-{prefix}-{number}",
            "amount": amount,
            "currency": currency,
            "status": status,
            "merchant": merchant,
            "date": date,
            "transaction_date": date + "T12:00:00",
            "as_of": AS_OF,
            "source": f"{FIXTURE_VERSION}/TX-{prefix}-{number}",
            "provenance": "team_authored_synthetic",
            "channel": "App",
            "transaction_type": "Purchase",
            "country": "Colombia" if prefix == "ES" else "Mexico",
        }
        for number, amount, status, merchant, date in values
    ]

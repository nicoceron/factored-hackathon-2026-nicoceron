from fastapi.testclient import TestClient

from factored_banking.api import app

client = TestClient(app)


def test_scaffold_does_not_claim_banking_readiness():
    assert client.get("/healthz").status_code == 200
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json()["ready"] is False
    assert client.get("/customers").status_code == 404

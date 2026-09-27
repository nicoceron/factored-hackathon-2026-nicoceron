"""Minimal service scaffold; exposes no customer records or banking actions."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Factored Banking Service",
    version="0.1.0",
    description="Project scaffold. The banking assistant is not implemented yet.",
)


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok", "stage": "scaffold"}


@app.get("/readyz", status_code=503)
def ready() -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "ready": False,
            "reason": "Banking workflow, authentication, and evaluation are not implemented.",
        },
    )

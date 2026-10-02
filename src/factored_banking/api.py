"""Claro: scoped trusted test sessions, evidence tools, and verified sandbox actions."""

import json
import os
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from factored_banking import workflow
from factored_banking.fixtures import AS_OF, PERSONAS, transactions
from factored_banking.store import Store, digest, encode

ROOT = Path(__file__).parent
SESSION_TTL = 3600


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(StrictModel):
    persona: Literal["customer_es", "customer_pt", "analyst"]
    language: Literal["es", "pt"] = "es"


class Chat(StrictModel):
    message: str = Field(min_length=1, max_length=2000)
    language: Literal["es", "pt"] = "es"
    transaction_id: str | None = Field(default=None, max_length=40)
    idempotency_key: str = Field(min_length=8, max_length=100)


class Confirm(StrictModel):
    proposal_id: str = Field(min_length=8, max_length=80)
    idempotency_key: str = Field(min_length=8, max_length=100)


class Resolve(StrictModel):
    resolution: Literal["reviewed_closed", "needs_information"]


def classifier(message, language):
    from factored_banking.language import classify

    return classify(message, language)


def create_app(db_path=None, secure_cookies=None):
    app = FastAPI(title="Claro Banking Sandbox", version="1.0.0")
    app.state.store = Store(db_path or os.getenv("CLARO_DB", ".local/claro.sqlite"))
    app.state.classifier = classifier
    secure = secure_cookies if secure_cookies is not None else os.getenv("CLARO_SECURE", "0") == "1"

    def origin_check(request):
        origin = request.headers.get("origin")
        expected = os.getenv("CLARO_ORIGIN") or str(request.base_url).rstrip("/")
        if origin and origin.rstrip("/") != expected:
            raise HTTPException(403, "Cross-origin requests are not permitted")
        if request.headers.get("sec-fetch-site") == "cross-site":
            raise HTTPException(403, "Cross-site requests are not permitted")

    def session(request, *, mutate=False, role=None):
        token = request.cookies.get("claro_session", "")
        with app.state.store.connect() as db:
            row = db.execute(
                "SELECT * FROM sessions WHERE token_hash=? AND expires>?",
                (digest(token), time.time()),
            ).fetchone()
        if row is None:
            raise HTTPException(401, "Session expired. Open a new demo session.")
        value = dict(row)
        if role and value["role"] != role:
            raise HTTPException(403, "Role is not authorized for this action")
        if mutate:
            origin_check(request)
            if not secrets.compare_digest(request.headers.get("x-csrf-token", ""), value["csrf"]):
                raise HTTPException(403, "CSRF token missing or invalid")
        return value

    def session_response(s):
        persona = next(p for p in PERSONAS.values() if p["customer"] == s["customer"])
        return {
            "user": {
                "role": s["role"],
                "display_name": persona["display_name"],
                "language": s["language"],
            },
            "csrf_token": s["csrf"],
            "workspace_mode": "isolated_demo",
            "as_of": AS_OF,
            "session_expires_at": s["expires"],
            "data_provenance": "team_authored_synthetic",
            "context": json.loads(s.get("state", "{}")),
        }

    def visible_case(row):
        value = json.loads(row["payload"])
        value.update(
            id=row["id"], status=row["status"], created_at=row["created"], updated_at=row["updated"]
        )
        return value

    def read_case(case_id, s):
        with app.state.store.connect() as db:
            row = db.execute(
                "SELECT * FROM cases WHERE id=? AND workspace=? AND (?='analyst' OR customer=?)",
                (case_id, s["workspace"], s["role"], s["customer"]),
            ).fetchone()
        if row is None:
            raise HTTPException(404, "Case not found")
        return visible_case(row)

    def retry(db, s, key, fingerprint):
        row = db.execute(
            "SELECT * FROM requests WHERE session_hash=? AND request_key=?",
            (s["token_hash"], key),
        ).fetchone()
        if row and row["fingerprint"] != fingerprint:
            raise HTTPException(409, "Idempotency key already used for a different request")
        return json.loads(row["response"]) if row else None

    def remember(db, s, key, fingerprint, result):
        db.execute(
            "INSERT INTO requests VALUES(?,?,?,?,?) ON CONFLICT(session_hash,request_key) "
            "DO UPDATE SET response=excluded.response "
            "WHERE requests.fingerprint=excluded.fingerprint",
            (s["token_hash"], key, fingerprint, encode(result), time.time()),
        )

    def record_event(db, s, result, started, event="chat"):
        db.execute(
            "INSERT INTO events(workspace,trace_id,event,intent,state,language,latency_ms,created) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                s["workspace"],
                result["trace_id"],
                event,
                result.get("intent"),
                result.get("state"),
                result.get("language", s["language"]),
                (time.perf_counter() - started) * 1000,
                time.time(),
            ),
        )

    @app.middleware("http")
    async def protections(request, call_next):
        try:
            length = int(request.headers.get("content-length", "0") or 0)
        except ValueError:
            return JSONResponse({"detail": "Invalid content length"}, status_code=400)
        if length > 16384:
            return JSONResponse({"detail": "Request too large"}, status_code=413)
        try:
            response = await call_next(request)
        except sqlite3.Error:
            response = JSONResponse(
                {"detail": "Storage unavailable. No action is claimed. Retry with the same key."},
                status_code=503,
            )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'self' https://huggingface.co"
        )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/healthz")
    def health():
        return {"status": "ok", "mode": "isolated_sandbox", "version": "1.0.0"}

    @app.get("/readyz")
    def ready():
        with app.state.store.connect() as db:
            db.execute("SELECT 1").fetchone()
        try:
            result = app.state.classifier("Quiero consultar una transacción", "es")
            model = result["model_version"]
            if "unavailable" in model or "model_unavailable" in result.get("signals", []):
                raise RuntimeError("Language model unavailable")
        except Exception:
            return JSONResponse(
                {"ready": False, "reason": "Language model unavailable"}, status_code=503
            )
        return {"ready": True, "mode": "sandbox_only", "language_model": model}

    @app.post("/api/session")
    def login(body: Login, request: Request, response: Response):
        origin_check(request)
        app.state.store.cleanup()
        now = time.time()
        workspace_token = request.cookies.get("claro_workspace", "")
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(24)
        persona = PERSONAS[body.persona]
        with app.state.store.connect() as db:
            row = db.execute(
                "SELECT id FROM workspaces WHERE token_hash=?", (digest(workspace_token),)
            ).fetchone()
            if row:
                workspace_id = row["id"]
            else:
                workspace_token = secrets.token_urlsafe(32)
                workspace_id = secrets.token_hex(16)
                db.execute(
                    "INSERT INTO workspaces VALUES(?,?,?)",
                    (workspace_id, digest(workspace_token), now),
                )
            db.execute(
                "DELETE FROM sessions WHERE token_hash=?",
                (digest(request.cookies.get("claro_session", "")),),
            )
            db.execute(
                "INSERT INTO sessions(token_hash,workspace,customer,role,language,csrf,expires) "
                "VALUES(?,?,?,?,?,?,?)",
                (
                    digest(token),
                    workspace_id,
                    persona["customer"],
                    persona["role"],
                    body.language,
                    csrf,
                    now + SESSION_TTL,
                ),
            )
        response.set_cookie(
            "claro_session",
            token,
            max_age=SESSION_TTL,
            httponly=True,
            secure=secure,
            samesite="strict",
        )
        response.set_cookie(
            "claro_workspace",
            workspace_token,
            max_age=86400,
            httponly=True,
            secure=secure,
            samesite="strict",
        )
        return session_response(
            {**persona, "csrf": csrf, "language": body.language, "expires": now + SESSION_TTL}
        )

    @app.get("/api/session")
    def whoami(request: Request):
        return session_response(session(request))

    @app.delete("/api/session")
    def logout(request: Request, response: Response):
        s = session(request, mutate=True)
        with app.state.store.connect() as db:
            db.execute("DELETE FROM sessions WHERE token_hash=?", (s["token_hash"],))
        response.delete_cookie("claro_session")
        return {"signed_out": True}

    @app.delete("/api/workspace")
    def delete_workspace(request: Request, response: Response):
        s = session(request, mutate=True)
        with app.state.store.connect() as db:
            db.execute(
                "DELETE FROM requests WHERE session_hash IN "
                "(SELECT token_hash FROM sessions WHERE workspace=?)",
                (s["workspace"],),
            )
            db.execute("DELETE FROM workspaces WHERE id=?", (s["workspace"],))
        response.delete_cookie("claro_session")
        response.delete_cookie("claro_workspace")
        return {"deleted": True}

    @app.get("/api/transactions")
    def list_transactions(request: Request):
        s = session(request, role="customer")
        return {"transactions": transactions(s["customer"]), "as_of": AS_OF}

    @app.post("/api/conversation/reset")
    def reset_conversation(request: Request):
        s = session(request, mutate=True, role="customer")
        with app.state.store.connect() as db:
            db.execute("UPDATE sessions SET state='{}' WHERE token_hash=?", (s["token_hash"],))
            db.execute("UPDATE proposals SET cancelled=1 WHERE session_hash=?", (s["token_hash"],))
        return {"reset": True}

    @app.post("/api/chat")
    def chat(body: Chat, request: Request):
        started = time.perf_counter()
        s = session(request, mutate=True, role="customer")
        fingerprint = digest(encode(body.model_dump()))
        with app.state.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            cached = retry(db, s, body.idempotency_key, fingerprint)
            if cached:
                return cached
            count = db.execute(
                "SELECT count(*) FROM events WHERE workspace=? AND created>?",
                (s["workspace"], time.time() - 60),
            ).fetchone()[0]
            if count >= 60:
                raise HTTPException(429, "Demo limit: 60 requests per minute")
            current = db.execute(
                "SELECT state FROM sessions WHERE token_hash=?", (s["token_hash"],)
            ).fetchone()
            result = workflow.run(
                body.message,
                body.language,
                body.transaction_id,
                json.loads(current["state"]),
                transactions(s["customer"]),
                app.state.classifier,
            )
            result.update(trace_id=secrets.token_hex(12), language=body.language)
            if result["state"] == "cancelled":
                db.execute(
                    "UPDATE proposals SET cancelled=1 WHERE session_hash=?", (s["token_hash"],)
                )
            payload = result.pop("proposal_payload", None)
            if payload:
                proposal_id = "PROP-" + secrets.token_hex(10)
                db.execute(
                    "UPDATE proposals SET cancelled=1 WHERE session_hash=?", (s["token_hash"],)
                )
                db.execute(
                    "INSERT INTO proposals VALUES(?,?,?,?,?,?,?,?)",
                    (
                        proposal_id,
                        s["workspace"],
                        s["token_hash"],
                        s["customer"],
                        encode(payload),
                        time.time(),
                        time.time() + 600,
                        0,
                    ),
                )
                result["proposal"] = {
                    "id": proposal_id,
                    "action": "create_case",
                    "summary": payload["summary"],
                    "expires_in_seconds": 600,
                }
            context = result.pop("context", json.loads(current["state"]))
            db.execute(
                "UPDATE sessions SET state=?,language=? WHERE token_hash=?",
                (encode(context), body.language, s["token_hash"]),
            )
            remember(db, s, body.idempotency_key, fingerprint, result)
            record_event(db, s, result, started)
        return result

    @app.post("/api/actions/confirm")
    def confirm(body: Confirm, request: Request):
        started = time.perf_counter()
        s = session(request, mutate=True, role="customer")
        fingerprint = digest("confirm:" + encode(body.model_dump()))
        with app.state.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            cached = retry(db, s, body.idempotency_key, fingerprint)
            if cached:
                return cached
            row = db.execute(
                "SELECT * FROM proposals WHERE id=? AND workspace=? "
                "AND session_hash=? AND customer=?",
                (body.proposal_id, s["workspace"], s["token_hash"], s["customer"]),
            ).fetchone()
            if row is None:
                raise HTTPException(404, "Proposal not found")
            existing = db.execute(
                "SELECT * FROM cases WHERE proposal_id=?", (body.proposal_id,)
            ).fetchone()
            if not existing and (row["cancelled"] or row["expires"] < time.time()):
                raise HTTPException(409, "Proposal cancelled or expired; create a new proposal")
            payload = json.loads(row["payload"])
            case_id = existing["id"] if existing else "CASE-" + secrets.token_hex(6).upper()
            # Bind the key before the side effect. A failed read-back leaves a retryable pending
            # response, but cannot let the same key execute a different proposal in the gap.
            db.execute(
                "INSERT OR IGNORE INTO requests VALUES(?,?,?,?,?)",
                (s["token_hash"], body.idempotency_key, fingerprint, "null", time.time()),
            )
            if not existing:
                now = time.time()
                db.execute(
                    "INSERT INTO cases VALUES(?,?,?,?,?,?,?,?)",
                    (
                        case_id,
                        s["workspace"],
                        s["customer"],
                        body.proposal_id,
                        encode(payload),
                        "open",
                        now,
                        now,
                    ),
                )
        verified = app.state.store.verify_case(case_id, s["workspace"])
        if not verified or verified["customer"] != s["customer"]:
            raise HTTPException(
                503,
                "Case write could not be verified. Retry with the same key; no success is claimed.",
            )
        receipt = {
            "id": case_id,
            "case_id": case_id,
            "status": verified["status"],
            "verified": True,
            "verification": "committed_read_back",
            "sandbox": True,
        }
        message = (
            f"Caso de prueba {case_id} creado y verificado. Está en la cola de revisión humana. "
            "No se ha bloqueado una tarjeta ni realizado un reembolso."
            if payload["language"] == "es"
            else f"Caso de teste {case_id} criado e verificado. Está na fila de análise humana. "
            "Nenhum cartão foi bloqueado e nenhum reembolso foi realizado."
        )
        result = {
            "message": message,
            "intent": payload["intent"],
            "state": "escalated",
            "evidence": payload["evidence"],
            "receipt": receipt,
            "proposal": None,
            "trace_id": secrets.token_hex(12),
            "language": payload["language"],
        }
        with app.state.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            cached = retry(db, s, body.idempotency_key, fingerprint)
            if cached:
                return cached
            remember(db, s, body.idempotency_key, fingerprint, result)
            record_event(db, s, result, started, "case_verified")
        return result

    @app.get("/api/cases")
    def cases(request: Request):
        s = session(request)
        with app.state.store.connect() as db:
            rows = db.execute(
                "SELECT * FROM cases WHERE workspace=? AND (?='analyst' OR customer=?) "
                "ORDER BY created DESC LIMIT 100",
                (s["workspace"], s["role"], s["customer"]),
            ).fetchall()
        return {"cases": [visible_case(row) for row in rows]}

    @app.get("/api/cases/{case_id}")
    def case_detail(case_id: str, request: Request):
        return read_case(case_id, session(request))

    @app.post("/api/cases/{case_id}/resolve")
    def resolve(case_id: str, body: Resolve, request: Request):
        s = session(request, mutate=True, role="analyst")
        read_case(case_id, s)
        with app.state.store.connect() as db:
            db.execute(
                "UPDATE cases SET status=?,updated=? WHERE id=? AND workspace=?",
                (body.resolution, time.time(), case_id, s["workspace"]),
            )
        verified = app.state.store.verify_case(case_id, s["workspace"])
        if not verified or verified["status"] != body.resolution:
            raise HTTPException(503, "Update could not be verified")
        return visible_case(verified)

    @app.get("/api/analytics")
    def analytics(request: Request):
        s = session(request, role="analyst")
        with app.state.store.connect() as db:
            rows = db.execute(
                "SELECT state,language,latency_ms,event FROM events "
                "WHERE workspace=? ORDER BY created",
                (s["workspace"],),
            ).fetchall()
            statuses = db.execute(
                "SELECT status,count(*) AS count FROM cases WHERE workspace=? GROUP BY status",
                (s["workspace"],),
            ).fetchall()
        latencies = sorted(row["latency_ms"] for row in rows)
        outcomes = {
            state: sum(r["state"] == state for r in rows) for state in {r["state"] for r in rows}
        }
        return {
            "scope": "this_browser_workspace_only",
            "total_requests": len(rows),
            "outcomes": outcomes,
            "cases_by_status": {r["status"]: r["count"] for r in statuses},
            "latency_ms": {
                "p50": latencies[int((len(latencies) - 1) * 0.5)] if latencies else None,
                "p95": latencies[int((len(latencies) - 1) * 0.95)] if latencies else None,
            },
            "model_api_cost_usd": 0,
            "limitations": "Demo telemetry, not production outcomes. "
            "No external model calls. Host costs excluded.",
        }

    @app.get("/api/evaluation")
    def evaluation():
        reports = {}
        for name in (
            "language-evaluation",
            "fraud-evaluation",
            "system-evaluation",
            "system-challenge-evaluation",
            "system-challenge-regression",
        ):
            path = ROOT / "resources" / f"{name}.json"
            if path.exists():
                reports[name] = json.loads(path.read_text())
        return {"reports": reports, "provenance": "offline evaluation; see repository methodology"}

    @app.get("/")
    def index():
        return FileResponse(ROOT / "static" / "index.html")

    app.mount("/static", StaticFiles(directory=ROOT / "static", check_dir=False), name="static")
    return app


app = create_app()

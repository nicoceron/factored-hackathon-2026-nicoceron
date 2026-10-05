"""Claro: scoped trusted test sessions, evidence tools, and verified sandbox actions."""

import json
import os
import re
import secrets
import sqlite3
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, model_validator

from factored_banking import workflow
from factored_banking.fixtures import AS_OF, PERSONAS, transactions
from factored_banking.language import detect_language
from factored_banking.privacy import redact_text
from factored_banking.store import Store, digest, encode
from factored_banking.web_assets import render_index

ROOT = Path(__file__).parent
SESSION_TTL = 3600
ROLE_COOKIES = {"customer": "claro_customer_session", "analyst": "claro_analyst_session"}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(StrictModel):
    persona: Literal["customer_es", "customer_pt", "analyst"] = "customer_es"
    language: Literal["es", "pt"] = "es"


class Chat(StrictModel):
    message: str = Field(min_length=1, max_length=2000)
    language: Literal["es", "pt"] | None = None
    transaction_id: str | None = Field(default=None, max_length=40)
    idempotency_key: str = Field(min_length=8, max_length=100)


class Confirm(StrictModel):
    proposal_id: str = Field(min_length=8, max_length=80)
    idempotency_key: str = Field(min_length=8, max_length=100)


class Resolve(StrictModel):
    resolution: Literal["reviewed_closed", "needs_information"]
    question: str | None = Field(default=None, min_length=5, max_length=1000)
    idempotency_key: str = Field(min_length=8, max_length=100)

    @model_validator(mode="after")
    def question_required(self):
        if self.resolution == "needs_information" and not self.question:
            raise ValueError("A specific question is required")
        if self.resolution == "reviewed_closed" and self.question:
            raise ValueError("A closed review cannot request more information")
        return self


class CaseMessage(StrictModel):
    message: str = Field(min_length=1, max_length=2000)
    question_id: str = Field(pattern=r"^EVT-[0-9a-f]{24}$")
    idempotency_key: str = Field(min_length=8, max_length=100)


def classifier(message, language):
    from factored_banking.language import classify

    return classify(message, language)


def create_app(db_path=None, secure_cookies=None, *, enable_external=None):
    from factored_banking.providers import ProviderRuntime

    @asynccontextmanager
    async def lifespan(app):
        yield
        app.state.ai.close()

    app = FastAPI(title="Claro Banking Sandbox", version="1.1.0", lifespan=lifespan)
    static = StaticFiles(directory=ROOT / "static", check_dir=False)
    index_html = render_index(ROOT / "static")
    index_headers = {
        "ETag": f'"{sha256(index_html.encode("utf-8")).hexdigest()}"',
        "Cache-Control": "no-cache",
    }
    app.state.store = Store(db_path or os.getenv("CLARO_DB", ".local/claro.sqlite"))
    app.state.ai = ProviderRuntime.from_env(
        enabled=enable_external,
        budget_path=os.getenv("CLARO_PROVIDER_BUDGET_DB") or app.state.store.path + ".ai.sqlite",
    )
    app.state.classifier = app.state.ai.classify
    app.state.readiness_classifier = classifier
    app.state.composer = app.state.ai.compose
    secure = secure_cookies if secure_cookies is not None else os.getenv("CLARO_SECURE", "0") == "1"

    def origin_check(request):
        origin = request.headers.get("origin")
        expected = os.getenv("CLARO_ORIGIN") or str(request.base_url).rstrip("/")
        if origin and origin.rstrip("/") != expected:
            raise HTTPException(403, "Cross-origin requests are not permitted")
        if request.headers.get("sec-fetch-site") == "cross-site":
            raise HTTPException(403, "Cross-site requests are not permitted")

    def requested_role(request):
        hint = request.headers.get("x-claro-role")
        if hint is not None and hint not in ROLE_COOKIES:
            raise HTTPException(400, "Unknown session role")
        return hint

    def session(request, *, mutate=False, role=None):
        hint = requested_role(request)
        cookie_name = ROLE_COOKIES[hint] if hint else "claro_session"
        token = request.cookies.get(cookie_name) or request.cookies.get("claro_session", "")
        with app.state.store.connect() as db:
            row = db.execute(
                "SELECT s.* FROM sessions s JOIN workspaces w ON w.id=s.workspace "
                "WHERE s.token_hash=? AND s.expires>? AND w.token_hash=?",
                (digest(token), time.time(), digest(request.cookies.get("claro_workspace", ""))),
            ).fetchone()
        if row is None:
            raise HTTPException(401, "Session expired. Open a new demo session.")
        value = dict(row)
        if (hint and value["role"] != hint) or (role and value["role"] != role):
            raise HTTPException(403, "Role is not authorized for this action")
        if mutate:
            origin_check(request)
            if not secrets.compare_digest(request.headers.get("x-csrf-token", ""), value["csrf"]):
                raise HTTPException(403, "CSRF token missing or invalid")
        return value

    def session_response(s):
        persona_id, persona = next(
            (key, value)
            for key, value in PERSONAS.items()
            if value["customer"] == s["customer"] and value["role"] == s["role"]
        )
        result = {
            "demo_persona": persona_id,
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
            "ai": app.state.ai.status(),
            "proposal": None,
            "proposal_evidence": [],
        }
        if s.get("token_hash") and s["role"] == "customer":
            with app.state.store.connect() as db:
                pending = db.execute(
                    "SELECT * FROM proposals WHERE session_hash=? AND workspace=? "
                    "AND customer=? AND cancelled=0 AND expires>? "
                    "AND NOT EXISTS(SELECT 1 FROM cases WHERE proposal_id=proposals.id) "
                    "ORDER BY created DESC LIMIT 1",
                    (s["token_hash"], s["workspace"], s["customer"], time.time()),
                ).fetchone()
            if pending:
                payload = json.loads(pending["payload"])
                result["proposal"] = proposal_response(
                    pending["id"], payload, max(0, int(pending["expires"] - time.time()))
                )
                result["proposal_evidence"] = payload["evidence"]
        return result

    def proposal_response(proposal_id, payload, expires_in_seconds=600):
        transaction = payload.get("transaction")
        if transaction is not None:
            validated = workflow.TransactionEvidence.model_validate(transaction).model_dump()
            transaction = {
                field: validated[field]
                for field in (
                    "id",
                    "merchant",
                    "amount",
                    "currency",
                    "status",
                    "date",
                    "as_of",
                    "source",
                    "provenance",
                )
            }
        return {
            "id": proposal_id,
            "action": "create_case",
            "summary": payload["summary"],
            "customer_report": payload["customer_report"],
            "report_provenance": payload["report_provenance"],
            "open_questions": payload["open_questions"],
            "transaction": transaction,
            "expires_in_seconds": expires_in_seconds,
        }

    def active_session(db, s):
        """Recheck authorization after acquiring the mutation transaction lock."""
        row = db.execute(
            "SELECT * FROM sessions WHERE token_hash=? AND workspace=? AND expires>?",
            (s["token_hash"], s["workspace"], time.time()),
        ).fetchone()
        if row is None:
            raise HTTPException(401, "Session expired or revoked during the request")
        return row

    def visible_case(row):
        value = json.loads(row["payload"])
        value.update(
            id=row["id"], status=row["status"], created_at=row["created"], updated_at=row["updated"]
        )
        with app.state.store.connect() as db:
            history = db.execute(
                "SELECT * FROM case_events WHERE case_id=? ORDER BY created,id", (row["id"],)
            ).fetchall()
        value["timeline"] = [
            {
                "id": e["id"],
                "type": e["event_type"],
                "actor_role": e["actor_role"],
                "created_at": e["created"],
                "text": e["body"],
                "status": e["status"],
                "client_request_id": e["client_request_id"],
            }
            for e in history
        ]
        value["pending_question"] = None
        if row["status"] == "needs_information":
            question = next(
                (e for e in reversed(history) if e["event_type"] == "question_requested"), None
            )
            if question:
                value["pending_question"] = {"id": question["id"], "text": question["body"]}
        value["history_complete"] = bool(history and history[0]["event_type"] == "case_created")
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

    def scoped_cases(s):
        with app.state.store.connect() as db:
            rows = db.execute(
                "SELECT * FROM cases WHERE workspace=? AND (?='analyst' OR customer=?) "
                "ORDER BY created DESC LIMIT 100",
                (s["workspace"], s["role"], s["customer"]),
            ).fetchall()
        return [visible_case(row) for row in rows]

    def conversational_cases(message, s, language, result):
        values = scoped_cases(s)
        references = set(re.findall(r"\bCASE-[A-Z0-9]+\b", message.upper()))
        known_case = result.pop("case_context_id", None)
        if not references and known_case:
            references = {known_case}
        if references:
            owned = {case["id"] for case in values}
            if not references <= owned:
                result.update(
                    message=(
                        "No hay un caso autorizado con esa referencia en tu sesión."
                        if language == "es"
                        else "Não há um caso autorizado com essa referência na sua sessão."
                    ),
                    state="blocked",
                    cases=[],
                    context={},
                )
                return result
            values = [case for case in values if case["id"] in references]
        if not values:
            result.update(
                message=(
                    "Todavía no tienes casos de prueba guardados. Describe qué ocurrió "
                    "y puedo preparar una solicitud de revisión humana."
                    if language == "es"
                    else "Você ainda não tem casos de teste salvos. Conte o que aconteceu "
                    "e posso preparar uma solicitação de análise humana."
                ),
                cases=[],
            )
            return result
        labels = {
            "open": ("en revisión humana", "em análise humana"),
            "needs_information": ("esperando tu respuesta", "aguardando sua resposta"),
            "reviewed_closed": ("revisión cerrada", "análise encerrada"),
        }
        lines = [
            "Leí estos casos guardados en tu sesión de prueba:"
            if language == "es"
            else "Consultei estes casos salvos na sua sessão de teste:"
        ]
        evidence = []
        for case in values:
            status = labels[case["status"]][language == "pt"]
            updated = datetime.fromtimestamp(case["updated_at"], UTC).isoformat(timespec="seconds")
            transaction = case.get("transaction") or {}
            reference = " · " + transaction["id"] if transaction.get("id") else ""
            lines.append(f"{case['id']}: {status}{reference}. UTC: {updated}.")
            if case["pending_question"]:
                prefix = "El analista pregunta: " if language == "es" else "O analista pergunta: "
                lines.append(prefix + case["pending_question"]["text"])
            evidence.append(
                {
                    "id": case["id"],
                    "title": "Caso guardado" if language == "es" else "Caso salvo",
                    "source": "sandbox_case_store/" + case["id"],
                    "text": status,
                    "as_of": updated,
                    "provenance": "persisted_sandbox_case",
                }
            )
        lines.append(
            "El estado del caso no determina fraude ni concede un reembolso."
            if language == "es"
            else "O estado do caso não determina fraude nem concede um reembolso."
        )
        next_context = {"last_case_id": values[0]["id"]} if len(values) == 1 else {}
        result.update(
            message="\n".join(lines), cases=values, evidence=evidence, context=next_context
        )
        return result

    def bounded_history(context, message, answer):
        """Keep a short redacted UI recovery window, never a raw full transcript."""
        existing = context.get("history", [])
        history = (
            [
                {"role": item["role"], "content": redact_text(item["content"])[:3000]}
                for item in existing[-10 if message is not None else -11 :]
                if isinstance(item, dict)
                and item.get("role") in {"user", "assistant"}
                and isinstance(item.get("content"), str)
            ]
            if isinstance(existing, list)
            else []
        )
        if message is not None:
            history.append({"role": "user", "content": redact_text(message)[:2000]})
        history.append({"role": "assistant", "content": redact_text(answer)[:3000]})
        while len(history) > 2 and sum(len(item["content"]) for item in history) > 12000:
            history = history[2:]
        return history

    def retry(db, s, key, fingerprint):
        row = db.execute(
            "SELECT * FROM requests WHERE session_hash=? AND request_key=?",
            (s["token_hash"], key),
        ).fetchone()
        if row and row["fingerprint"] != fingerprint:
            raise HTTPException(409, "Idempotency key already used for a different request")
        result = json.loads(row["response"]) if row else None
        if isinstance(result, dict) and result.get("_pending"):
            if time.time() - result["started"] < 90:
                raise HTTPException(409, "Request in progress. Retry later with the same key.")
            db.execute(
                "DELETE FROM requests WHERE session_hash=? AND request_key=?",
                (s["token_hash"], key),
            )
            return None
        return result

    def remember(db, s, key, fingerprint, result):
        db.execute(
            "INSERT INTO requests VALUES(?,?,?,?,?) ON CONFLICT(session_hash,request_key) "
            "DO UPDATE SET response=excluded.response "
            "WHERE requests.fingerprint=excluded.fingerprint",
            (s["token_hash"], key, fingerprint, encode(result), time.time()),
        )

    def record_event(db, s, result, started, event="chat"):
        db.execute(
            "INSERT INTO events(workspace,trace_id,event,intent,state,language,"
            "latency_ms,created,ai_usage) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (
                s["workspace"],
                result["trace_id"],
                event,
                result.get("intent"),
                result.get("state"),
                result.get("language", s["language"]),
                (time.perf_counter() - started) * 1000,
                time.time(),
                encode(result.get("ai", {})),
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
        elif request.url.path == "/" or request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache"
        return response

    @app.get("/healthz")
    def health():
        return {"status": "ok", "mode": "isolated_sandbox", "version": "1.1.0"}

    @app.get("/readyz")
    def ready():
        with app.state.store.connect() as db:
            db.execute("SELECT 1").fetchone()
        try:
            # Health probes never incur provider spend or transmit a customer message.
            result = app.state.readiness_classifier("Quiero consultar una transacción", "es")
            model = result["model_version"]
            if "unavailable" in model or "model_unavailable" in result.get("signals", []):
                raise RuntimeError("Language model unavailable")
        except Exception:
            return JSONResponse(
                {"ready": False, "reason": "Language model unavailable"}, status_code=503
            )
        return {
            "ready": True,
            "mode": "sandbox_only",
            "language_model": model,
            "ai": app.state.ai.status(),
        }

    @app.post("/api/session")
    def login(body: Login, request: Request, response: Response):
        origin_check(request)
        hint = requested_role(request)
        persona = PERSONAS[body.persona]
        if hint and hint != persona["role"]:
            raise HTTPException(400, "Requested session role does not match the demo identity")
        app.state.store.cleanup()
        now = time.time()
        workspace_token = request.cookies.get("claro_workspace", "")
        legacy_token = request.cookies.get("claro_session", "")
        role_cookie = ROLE_COOKIES[persona["role"]]
        token = request.cookies.get(role_cookie) or legacy_token
        legacy_session = None
        with app.state.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
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
            legacy_session = db.execute(
                "SELECT * FROM sessions WHERE token_hash=? AND workspace=? AND expires>?",
                (digest(legacy_token), workspace_id, now),
            ).fetchone()
            existing = db.execute(
                "SELECT * FROM sessions WHERE token_hash=? AND workspace=? AND role=? "
                "AND expires>?",
                (digest(token), workspace_id, persona["role"], now),
            ).fetchone()
            if existing and existing["customer"] == persona["customer"]:
                language = (
                    body.language if "language" in body.model_fields_set else existing["language"]
                )
                db.execute(
                    "UPDATE sessions SET expires=?,language=?,revision=revision+? "
                    "WHERE token_hash=?",
                    (
                        now + SESSION_TTL,
                        language,
                        int(language != existing["language"]),
                        existing["token_hash"],
                    ),
                )
            else:
                # Changing a test identity revokes only its role in this workspace.
                # A reviewer login must leave the customer's proposals and retries intact.
                db.execute(
                    "DELETE FROM sessions WHERE token_hash=? AND workspace=? AND role=?",
                    (digest(token), workspace_id, persona["role"]),
                )
                token = secrets.token_urlsafe(32)
                db.execute(
                    "INSERT INTO sessions"
                    "(token_hash,workspace,customer,role,language,csrf,expires) "
                    "VALUES(?,?,?,?,?,?,?)",
                    (
                        digest(token),
                        workspace_id,
                        persona["customer"],
                        persona["role"],
                        body.language,
                        secrets.token_urlsafe(24),
                        now + SESSION_TTL,
                    ),
                )
            current = dict(
                db.execute("SELECT * FROM sessions WHERE token_hash=?", (digest(token),)).fetchone()
            )
        if legacy_session and legacy_session["role"] != persona["role"]:
            previous_cookie = ROLE_COOKIES[legacy_session["role"]]
            if not request.cookies.get(previous_cookie):
                response.set_cookie(
                    previous_cookie,
                    legacy_token,
                    max_age=max(0, int(legacy_session["expires"] - now)),
                    httponly=True,
                    secure=secure,
                    samesite="strict",
                )
        for name in (role_cookie, "claro_session"):
            response.set_cookie(
                name,
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
        return session_response(current)

    @app.get("/api/session")
    def whoami(request: Request):
        return session_response(session(request))

    @app.delete("/api/session")
    def logout(request: Request, response: Response):
        s = session(request, mutate=True)
        with app.state.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            active_session(db, s)
            db.execute("DELETE FROM sessions WHERE token_hash=?", (s["token_hash"],))
        response.delete_cookie(ROLE_COOKIES[s["role"]])
        if digest(request.cookies.get("claro_session", "")) == s["token_hash"]:
            response.delete_cookie("claro_session")
        return {"signed_out": True}

    @app.delete("/api/workspace")
    def delete_workspace(request: Request, response: Response):
        s = session(request, mutate=True)
        with app.state.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            active_session(db, s)
            db.execute(
                "DELETE FROM requests WHERE session_hash IN "
                "(SELECT token_hash FROM sessions WHERE workspace=?)",
                (s["workspace"],),
            )
            db.execute("DELETE FROM workspaces WHERE id=?", (s["workspace"],))
        response.delete_cookie("claro_session")
        for name in ROLE_COOKIES.values():
            response.delete_cookie(name)
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
            db.execute("BEGIN IMMEDIATE")
            active_session(db, s)
            db.execute(
                "UPDATE sessions SET state='{}',revision=revision+1 WHERE token_hash=?",
                (s["token_hash"],),
            )
            db.execute("UPDATE proposals SET cancelled=1 WHERE session_hash=?", (s["token_hash"],))
            db.execute(
                "DELETE FROM requests WHERE session_hash=? AND response LIKE ?",
                (s["token_hash"], '%"_pending":true%'),
            )
        return {"reset": True}

    @app.post("/api/chat")
    def chat(body: Chat, request: Request):
        started = time.perf_counter()
        s = session(request, mutate=True, role="customer")
        fingerprint = digest(encode(body.model_dump()))
        with app.state.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            current = active_session(db, s)
            cached = retry(db, s, body.idempotency_key, fingerprint)
            if cached:
                return cached
            db.execute(
                "DELETE FROM requests WHERE session_hash=? AND created<? AND response LIKE ?",
                (s["token_hash"], time.time() - 90, '%"_pending":true%'),
            )
            count = db.execute(
                "SELECT count(*) FROM events WHERE workspace=? AND created>?",
                (s["workspace"], time.time() - 60),
            ).fetchone()[0]
            pending_count = db.execute(
                "SELECT count(*) FROM requests WHERE session_hash=? AND response LIKE ?",
                (s["token_hash"], '%"_pending":true%'),
            ).fetchone()[0]
            if count >= 60 or pending_count >= 2:
                raise HTTPException(429, "Demo request limit reached")
            context = json.loads(current["state"])
            language = detect_language(body.message, body.language or current["language"])
            revision = current["revision"]
            pending_claim = {
                "_pending": True,
                "started": time.time(),
                "owner": secrets.token_hex(16),
                "revision": revision,
            }
            remember(db, s, body.idempotency_key, fingerprint, pending_claim)
        # External inference runs outside SQLite's write transaction. The revision
        # check below rejects stale responses after reset, logout or a competing turn.
        try:
            with app.state.ai.scope(s["workspace"]):
                message = redact_text(body.message)
                classifier_fn = app.state.classifier
                if getattr(classifier_fn, "__self__", None) is app.state.ai:

                    def classifier_fn(text, lang):
                        return app.state.ai.classify(text, lang, context=context)

                result = workflow.run(
                    message,
                    language,
                    body.transaction_id,
                    context,
                    transactions(s["customer"]),
                    classifier_fn,
                )
                if result["state"] == "case_lookup":
                    result = conversational_cases(message, s, language, result)
                result.update(trace_id=secrets.token_hex(12), language=language)
                history = (
                    [{"role": "user", "content": context["customer_report"]}]
                    if context.get("customer_report")
                    else []
                )
                composed = app.state.composer(message, language, result, history=history)
                result["message"] = composed["message"]
                assessment = result.get("assessment", {})
                result["ai"] = {
                    "classifier": assessment.get(
                        "provider_meta",
                        {
                            "provider": "local",
                            "model": assessment.get("model_version", "deterministic"),
                            "status": "used" if assessment else "not_needed",
                        },
                    ),
                    "response": composed["provider_meta"],
                }
            with app.state.store.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                active = active_session(db, s)
                if active["revision"] != revision:
                    raise HTTPException(
                        409, "Conversation changed. Submit your current request again."
                    )
                owns_claim = db.execute(
                    "SELECT 1 FROM requests WHERE session_hash=? AND request_key=? "
                    "AND fingerprint=? AND response=?",
                    (s["token_hash"], body.idempotency_key, fingerprint, encode(pending_claim)),
                ).fetchone()
                if not owns_claim:
                    raise HTTPException(409, "Request was replaced. Refresh the conversation.")
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
                    result["proposal"] = proposal_response(proposal_id, payload)
                next_context = result.pop("context", context)
                if result["state"] != "cancelled":
                    next_context["history"] = bounded_history(context, message, result["message"])
                db.execute(
                    "UPDATE sessions SET state=?,language=?,revision=revision+1 WHERE token_hash=?",
                    (encode(next_context), language, s["token_hash"]),
                )
                remember(db, s, body.idempotency_key, fingerprint, result)
                record_event(db, s, result, started)
            return result
        except Exception:
            with app.state.store.connect() as db:
                db.execute(
                    "DELETE FROM requests WHERE session_hash=? AND request_key=? "
                    "AND fingerprint=? AND response=?",
                    (s["token_hash"], body.idempotency_key, fingerprint, encode(pending_claim)),
                )
            raise

    @app.post("/api/actions/confirm")
    def confirm(body: Confirm, request: Request):
        started = time.perf_counter()
        s = session(request, mutate=True, role="customer")
        fingerprint = digest("confirm:" + encode(body.model_dump()))
        with app.state.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            active_session(db, s)
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
                db.execute(
                    "INSERT INTO case_events VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (
                        "EVT-" + secrets.token_hex(12),
                        case_id,
                        "customer",
                        "case_created",
                        payload["customer_report"],
                        "open",
                        now,
                        body.idempotency_key,
                        s["token_hash"],
                        fingerprint,
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
            active = active_session(db, s)
            cached = retry(db, s, body.idempotency_key, fingerprint)
            if cached:
                return cached
            context = json.loads(active["state"])
            history = context.get("history", [])
            if not isinstance(history, list):
                history = []
            if not history or history[-1].get("content") != message:
                history = bounded_history(context, None, message)
            next_context = {
                "history": history[-12:],
                "last_case_id": case_id,
                "pending_intent": "transaction_status",
            }
            if payload.get("transaction"):
                next_context["transaction_id"] = payload["transaction"]["id"]
            db.execute(
                "UPDATE sessions SET state=?,revision=revision+1 WHERE token_hash=?",
                (encode(next_context), s["token_hash"]),
            )
            remember(db, s, body.idempotency_key, fingerprint, result)
            record_event(db, s, result, started, "case_verified")
        return result

    @app.get("/api/cases")
    def cases(request: Request):
        s = session(request)
        return {"cases": scoped_cases(s)}

    @app.get("/api/cases/{case_id}")
    def case_detail(case_id: str, request: Request):
        return read_case(case_id, session(request))

    def mutate_case(case_id, body, s, *, reply=False):
        started = time.perf_counter()
        fingerprint = digest(
            ("reply:" if reply else "review:") + case_id + encode(body.model_dump())
        )
        with app.state.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            active_session(db, s)
            cached = retry(db, s, body.idempotency_key, fingerprint)
            if cached:
                return cached
            row = db.execute(
                "SELECT * FROM cases WHERE id=? AND workspace=? AND (?='analyst' OR customer=?)",
                (case_id, s["workspace"], s["role"], s["customer"]),
            ).fetchone()
            if row is None:
                raise HTTPException(404, "Case not found")
            existing = db.execute(
                "SELECT * FROM case_events WHERE case_id=? "
                "AND actor_session=? AND client_request_id=?",
                (case_id, s["token_hash"], body.idempotency_key),
            ).fetchone()
            if existing and existing["fingerprint"] != fingerprint:
                raise HTTPException(409, "Idempotency key already used for a different request")
            if existing:
                event_id = existing["id"]
            else:
                if row["status"] == "reviewed_closed":
                    raise HTTPException(
                        409, "Review is closed. Create a new case for a new request."
                    )
                if reply and row["status"] != "needs_information":
                    raise HTTPException(409, "There is no unanswered analyst question")
                if reply:
                    pending_question = db.execute(
                        "SELECT id FROM case_events WHERE case_id=? "
                        "AND event_type='question_requested' ORDER BY created DESC,id DESC LIMIT 1",
                        (case_id,),
                    ).fetchone()
                    if not pending_question or pending_question["id"] != body.question_id:
                        raise HTTPException(409, "The analyst question changed. Refresh the case.")
                if (
                    not reply
                    and body.resolution == "needs_information"
                    and row["status"] == "needs_information"
                ):
                    raise HTTPException(409, "Wait for the pending question to be answered")
                if (
                    db.execute(
                        "SELECT count(*) FROM case_events WHERE case_id=?", (case_id,)
                    ).fetchone()[0]
                    >= 100
                ):
                    raise HTTPException(429, "Sandbox case history limit reached")
                text = redact_text(body.message if reply else body.question or "")
                if (reply or body.resolution == "needs_information") and not text:
                    raise HTTPException(422, "A nonempty message is required")
                status = "open" if reply else body.resolution
                event_type = (
                    "customer_reply"
                    if reply
                    else (
                        "question_requested" if status == "needs_information" else "review_closed"
                    )
                )
                event_id = "EVT-" + secrets.token_hex(12)
                now = time.time()
                # Reserve the fingerprint atomically with the event. If read-back
                # fails, a retry can verify this same event without another write.
                db.execute(
                    "INSERT OR IGNORE INTO requests VALUES(?,?,?,?,?)",
                    (s["token_hash"], body.idempotency_key, fingerprint, "null", now),
                )
                db.execute(
                    "INSERT INTO case_events VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (
                        event_id,
                        case_id,
                        s["role"],
                        event_type,
                        text,
                        status,
                        now,
                        body.idempotency_key,
                        s["token_hash"],
                        fingerprint,
                    ),
                )
                db.execute(
                    "UPDATE cases SET status=?,updated=? WHERE id=? AND workspace=?",
                    (status, now, case_id, s["workspace"]),
                )
        verified = app.state.store.verify_case_event(case_id, event_id, s["workspace"])
        if not verified or verified["fingerprint"] != fingerprint:
            raise HTTPException(503, "Update could not be verified. Retry with the same key.")
        result = read_case(case_id, s)
        result["receipt"] = {
            "id": event_id,
            "case_id": case_id,
            "verified": True,
            "verification": "committed_read_back",
            "sandbox": True,
        }
        result.update(trace_id=secrets.token_hex(12), state=result["status"])
        with app.state.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            active = active_session(db, s)
            cached = retry(db, s, body.idempotency_key, fingerprint)
            if cached:
                return cached
            if reply:
                language = detect_language(verified["body"], active["language"])
                result["message"] = (
                    "Respuesta guardada y verificada."
                    if language == "es"
                    else "Resposta salva e verificada."
                )
                result["response_language"] = language
                context = json.loads(active["state"])
                context["history"] = bounded_history(context, verified["body"], result["message"])
                db.execute(
                    "UPDATE sessions SET state=?,language=?,revision=revision+1 WHERE token_hash=?",
                    (encode(context), language, s["token_hash"]),
                )
            remember(db, s, body.idempotency_key, fingerprint, result)
            record_event(db, s, result, started, "case_reply" if reply else "case_review")
        return result

    @app.post("/api/cases/{case_id}/resolve")
    def resolve(case_id: str, body: Resolve, request: Request):
        return mutate_case(case_id, body, session(request, mutate=True, role="analyst"))

    @app.post("/api/cases/{case_id}/messages")
    def case_message(case_id: str, body: CaseMessage, request: Request):
        return mutate_case(
            case_id, body, session(request, mutate=True, role="customer"), reply=True
        )

    @app.get("/api/analytics")
    def analytics(request: Request):
        s = session(request, role="analyst")
        with app.state.store.connect() as db:
            rows = db.execute(
                "SELECT state,language,latency_ms,event,ai_usage FROM events "
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
        usage = app.state.ai.usage_for_scope(s["workspace"])
        attempts = usage["attempts"]
        unknown = usage["unknown_cost_attempts"]
        estimate = usage["estimated_cost_usd"]
        return {
            "scope": "this_browser_workspace_only",
            "total_requests": len(rows),
            "outcomes": outcomes,
            "cases_by_status": {r["status"]: r["count"] for r in statuses},
            "latency_ms": {
                "p50": latencies[int((len(latencies) - 1) * 0.5)] if latencies else None,
                "p95": latencies[int((len(latencies) - 1) * 0.95)] if latencies else None,
            },
            "model_api_cost_usd": 0 if attempts == 0 and unknown == 0 else None,
            "estimated_model_api_cost_usd": None if unknown else estimate,
            "provider_attempts": attempts,
            "unknown_cost_attempts": unknown,
            "provider_usage": usage,
            "limitations": "Demo telemetry, not production outcomes. "
            "Provider tariff estimates are not invoices. Unknown usage is not zero. "
            "Host costs excluded.",
        }

    @app.get("/api/evaluation")
    def evaluation():
        reports = {}
        report_files = {}
        current_regressions = {
            "system-evaluation": "chat-system-regression.json",
            "system-challenge-regression": "chat-challenge-regression.json",
            "service-segment-evaluation": "chat-service-segment-regression.json",
        }
        for name in (
            "language-evaluation",
            "fraud-evaluation",
            "system-evaluation",
            "system-challenge-evaluation",
            "system-challenge-regression",
            "service-segment-evaluation",
        ):
            latest = ROOT / "resources" / f"{name}-v2.json"
            path = latest if latest.exists() else ROOT / "resources" / f"{name}.json"
            current_name = current_regressions.get(name)
            current = ROOT / "resources" / current_name if current_name else None
            if current is not None and current.exists():
                path = current
            if path.exists():
                reports[name] = json.loads(path.read_text())
                report_files[name] = path.name
        return {
            "reports": reports,
            "report_files": report_files,
            "provenance": "offline authored evaluation and regression; see repository methodology",
        }

    @app.api_route("/", methods=["GET", "HEAD"])
    @app.api_route("/static/index.html", methods=["GET", "HEAD"], include_in_schema=False)
    def index(request: Request):
        response = HTMLResponse(index_html, headers=index_headers)
        if static.is_not_modified(response.headers, request.headers):
            return Response(status_code=304, headers=index_headers)
        if request.method == "HEAD":
            response.body = b""
        return response

    app.mount("/static", static, name="static")
    return app


app = create_app()

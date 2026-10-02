"""SQLite sandbox persistence with minimized reports and an append-only case history."""

import hashlib
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS workspaces (
 id TEXT PRIMARY KEY, token_hash TEXT UNIQUE NOT NULL, created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, workspace TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
 customer TEXT, role TEXT NOT NULL, language TEXT NOT NULL, csrf TEXT NOT NULL,
 expires REAL NOT NULL, state TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS proposals (
 id TEXT PRIMARY KEY, workspace TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
 session_hash TEXT NOT NULL, customer TEXT NOT NULL, payload TEXT NOT NULL,
 created REAL NOT NULL, expires REAL NOT NULL, cancelled INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS cases (
 id TEXT PRIMARY KEY, workspace TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
 customer TEXT NOT NULL, proposal_id TEXT UNIQUE NOT NULL,
 payload TEXT NOT NULL, status TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS requests (
 session_hash TEXT NOT NULL REFERENCES sessions(token_hash) ON DELETE CASCADE,
 request_key TEXT NOT NULL, fingerprint TEXT NOT NULL,
 response TEXT NOT NULL, created REAL NOT NULL, PRIMARY KEY(session_hash, request_key)
);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY, workspace TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
 trace_id TEXT NOT NULL, event TEXT NOT NULL, intent TEXT, state TEXT, language TEXT,
 latency_ms REAL NOT NULL, created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS case_events (
 id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
 actor_role TEXT NOT NULL, event_type TEXT NOT NULL, body TEXT NOT NULL,
 status TEXT NOT NULL, created REAL NOT NULL, client_request_id TEXT NOT NULL,
 actor_session TEXT NOT NULL, fingerprint TEXT NOT NULL,
 UNIQUE(case_id, actor_session, client_request_id)
);
CREATE INDEX IF NOT EXISTS case_scope ON cases(workspace, customer);
CREATE INDEX IF NOT EXISTS event_scope ON events(workspace, created);
CREATE INDEX IF NOT EXISTS case_event_order ON case_events(case_id, created);
"""


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def encode(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class Store:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            if "revision" not in {
                row["name"] for row in connection.execute("PRAGMA table_info(sessions)")
            }:
                connection.execute(
                    "ALTER TABLE sessions ADD COLUMN revision INTEGER NOT NULL DEFAULT 0"
                )
            if "ai_usage" not in {
                row["name"] for row in connection.execute("PRAGMA table_info(events)")
            }:
                connection.execute(
                    "ALTER TABLE events ADD COLUMN ai_usage TEXT NOT NULL DEFAULT '{}'"
                )
            if not connection.execute("PRAGMA foreign_key_list(requests)").fetchall():
                # Upgrade the initial local prototype without retaining responses for revoked
                # sessions. Existing committed cases and active retry receipts are preserved.
                connection.executescript("""
                    ALTER TABLE requests RENAME TO requests_before_cascade;
                    CREATE TABLE requests (
                      session_hash TEXT NOT NULL REFERENCES sessions(token_hash) ON DELETE CASCADE,
                      request_key TEXT NOT NULL, fingerprint TEXT NOT NULL,
                      response TEXT NOT NULL, created REAL NOT NULL,
                      PRIMARY KEY(session_hash, request_key)
                    );
                    INSERT INTO requests SELECT r.* FROM requests_before_cascade r
                      INNER JOIN sessions s ON s.token_hash=r.session_hash;
                    DROP TABLE requests_before_cascade;
                """)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=3, isolation_level="IMMEDIATE")
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def cleanup(self, retention_seconds=86400):
        """Ephemeral review workspaces expire after 24h; session expiry is independent."""
        now = time.time()
        with self.connect() as db:
            db.execute("DELETE FROM workspaces WHERE created < ?", (now - retention_seconds,))
            db.execute("DELETE FROM sessions WHERE expires < ?", (now,))
            db.execute("DELETE FROM requests WHERE created < ?", (now - retention_seconds,))

    def verify_case(self, case_id, workspace):
        # A fresh connection proves the write committed, rather than echoing its input.
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM cases WHERE id=? AND workspace=?", (case_id, workspace)
            ).fetchone()
        return dict(row) if row else None

    def verify_case_event(self, case_id, event_id, workspace):
        with self.connect() as db:
            row = db.execute(
                "SELECT e.* FROM case_events e JOIN cases c ON c.id=e.case_id "
                "WHERE e.id=? AND e.case_id=? AND c.workspace=?",
                (event_id, case_id, workspace),
            ).fetchone()
        return dict(row) if row else None

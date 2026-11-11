"""Persistent local CloudPilot session lifecycle (simulation only)."""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

PROVIDERS = ("aws", "azure", "gcp")
ALLOWED_TIMEOUTS = (5, 10, 15, 30)
DEFAULT_TIMEOUT = int(os.getenv("SESSION_IDLE_TIMEOUT_MINUTES", "15"))
WARNING_MINUTES = int(os.getenv("SESSION_WARNING_MINUTES", "2"))


def _db_path() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///./cloudpilot.db")
    if url.startswith("sqlite:///"):
        path = url.removeprefix("sqlite:///")
        if path.startswith("./"):
            path = path[2:]
        return path or "cloudpilot.db"
    return "cloudpilot.db"


def _connect() -> sqlite3.Connection:
    path = _db_path()
    if Path(path).parent != Path("."):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cloud_sessions (
            id TEXT PRIMARY KEY, provider TEXT NOT NULL, status TEXT NOT NULL,
            started_at TEXT NOT NULL, last_activity_at TEXT NOT NULL,
            expires_at TEXT NOT NULL, ended_at TEXT, end_reason TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cloud_sessions_provider_status ON cloud_sessions(provider, status)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY, value TEXT NOT NULL
        )
    """)
    conn.execute(
        "INSERT OR IGNORE INTO app_settings (key, value) VALUES ('idle_timeout_minutes', ?)",
        (str(DEFAULT_TIMEOUT),),
    )
    return conn


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value)


def get_settings() -> dict[str, int]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT value FROM app_settings WHERE key='idle_timeout_minutes'"
        ).fetchone()
        return {
            "idle_timeout_minutes": int(row["value"]) if row else DEFAULT_TIMEOUT,
            "warning_minutes": WARNING_MINUTES,
        }


def set_idle_timeout(minutes: int) -> dict[str, int]:
    if minutes not in ALLOWED_TIMEOUTS:
        raise ValueError(f"Timeout must be one of {', '.join(map(str, ALLOWED_TIMEOUTS))} minutes")
    now = _now()
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES ('idle_timeout_minutes', ?)",
            (str(minutes),),
        )
        rows = conn.execute(
            "SELECT id, last_activity_at FROM cloud_sessions WHERE status='active'"
        ).fetchall()
        for row in rows:
            expires = _parse(row["last_activity_at"]) + timedelta(minutes=minutes)
            if expires <= now:
                conn.execute(
                    "UPDATE cloud_sessions SET status='ended', ended_at=?, end_reason='idle_timeout' WHERE id=?",
                    (now.isoformat(), row["id"]),
                )
            else:
                conn.execute(
                    "UPDATE cloud_sessions SET expires_at=? WHERE id=?",
                    (expires.isoformat(), row["id"]),
                )
    return get_settings()


def _expire_due(conn: sqlite3.Connection) -> None:
    now = _now()
    timeout = get_settings()["idle_timeout_minutes"]
    rows = conn.execute("SELECT id, last_activity_at FROM cloud_sessions WHERE status='active'").fetchall()
    for row in rows:
        if now >= _parse(row["last_activity_at"]) + timedelta(minutes=timeout):
            conn.execute(
                "UPDATE cloud_sessions SET status='ended', ended_at=?, end_reason='idle_timeout' WHERE id=?",
                (now.isoformat(), row["id"]),
            )


def _serialize(row: sqlite3.Row) -> dict[str, Any]:
    now = _now()
    settings = get_settings()
    expires = _parse(row["expires_at"])
    seconds = max(0, int((expires - now).total_seconds())) if row["status"] == "active" else 0
    return {
        "id": row["id"], "provider": row["provider"], "status": row["status"],
        "started_at": row["started_at"], "last_activity_at": row["last_activity_at"],
        "expires_at": row["expires_at"], "ended_at": row["ended_at"],
        "end_reason": row["end_reason"], "seconds_until_expiry": seconds,
        "warning": row["status"] == "active" and seconds <= settings["warning_minutes"] * 60,
    }


def list_sessions() -> dict[str, Any]:
    with _connect() as conn:
        _expire_due(conn)
        rows = conn.execute("SELECT * FROM cloud_sessions ORDER BY started_at DESC").fetchall()
        history = [_serialize(row) for row in rows]
        latest: dict[str, dict[str, Any]] = {}
        for session in history:
            latest.setdefault(session["provider"], session)
        providers = []
        for provider in PROVIDERS:
            session = latest.get(provider)
            providers.append({
                "provider": provider, "connected": False,
                "session": session if session and session["status"] == "active" else None,
            })
        settings = get_settings()
        return {
            "providers": providers,
            "active_sessions": sum(1 for item in providers if item["session"]),
            "idle_timeout_minutes": settings["idle_timeout_minutes"],
            "warning_minutes": settings["warning_minutes"],
            "allowed_timeouts": list(ALLOWED_TIMEOUTS),
            "history": history[:25],
            "simulation_only": True,
        }


def start_session(provider: str) -> dict[str, Any]:
    if provider not in PROVIDERS:
        raise ValueError("Unsupported provider")
    with _connect() as conn:
        _expire_due(conn)
        current = conn.execute(
            "SELECT * FROM cloud_sessions WHERE provider=? AND status='active' ORDER BY started_at DESC LIMIT 1",
            (provider,),
        ).fetchone()
        if current:
            return _serialize(current)
        now = _now()
        expires = now + timedelta(minutes=get_settings()["idle_timeout_minutes"])
        session_id = str(uuid4())
        conn.execute(
            """INSERT INTO cloud_sessions
            (id, provider, status, started_at, last_activity_at, expires_at)
            VALUES (?, ?, 'active', ?, ?, ?)""",
            (session_id, provider, now.isoformat(), now.isoformat(), expires.isoformat()),
        )
        return _serialize(conn.execute("SELECT * FROM cloud_sessions WHERE id=?", (session_id,)).fetchone())


def record_activity(provider: str) -> dict[str, Any]:
    if provider not in PROVIDERS:
        raise ValueError("Unsupported provider")
    with _connect() as conn:
        _expire_due(conn)
        row = conn.execute(
            "SELECT * FROM cloud_sessions WHERE provider=? AND status='active' ORDER BY started_at DESC LIMIT 1",
            (provider,),
        ).fetchone()
        if not row:
            raise LookupError("No active session for this provider")
        now = _now()
        expires = now + timedelta(minutes=get_settings()["idle_timeout_minutes"])
        conn.execute(
            "UPDATE cloud_sessions SET last_activity_at=?, expires_at=? WHERE id=?",
            (now.isoformat(), expires.isoformat(), row["id"]),
        )
        return _serialize(conn.execute("SELECT * FROM cloud_sessions WHERE id=?", (row["id"],)).fetchone())


def end_session(provider: str, reason: str = "manual") -> dict[str, Any]:
    if provider not in PROVIDERS:
        raise ValueError("Unsupported provider")
    with _connect() as conn:
        _expire_due(conn)
        row = conn.execute(
            "SELECT * FROM cloud_sessions WHERE provider=? AND status='active' ORDER BY started_at DESC LIMIT 1",
            (provider,),
        ).fetchone()
        if not row:
            raise LookupError("No active session for this provider")
        now = _now()
        conn.execute(
            "UPDATE cloud_sessions SET status='ended', ended_at=?, end_reason=? WHERE id=?",
            (now.isoformat(), reason, row["id"]),
        )
        return _serialize(conn.execute("SELECT * FROM cloud_sessions WHERE id=?", (row["id"],)).fetchone())


def end_all_sessions() -> dict[str, Any]:
    with _connect() as conn:
        _expire_due(conn)
        now = _now().isoformat()
        cursor = conn.execute(
            "UPDATE cloud_sessions SET status='ended', ended_at=?, end_reason='end_all' WHERE status='active'",
            (now,),
        )
        return {"ended_count": cursor.rowcount, "ended_at": now}

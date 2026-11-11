"""Persistent local CloudPilot session lifecycle (simulation only)."""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

PROVIDERS = ("aws", "azure", "gcp")
IDLE_TIMEOUT_MINUTES = int(os.getenv("SESSION_IDLE_TIMEOUT_MINUTES", "15"))
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
    Path(path).parent.mkdir(parents=True, exist_ok=True) if Path(path).parent != Path(".") else None
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cloud_sessions (
            id TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT NOT NULL,
            last_activity_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            ended_at TEXT,
            end_reason TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cloud_sessions_provider_status ON cloud_sessions(provider, status)")
    return conn


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _expire_due(conn: sqlite3.Connection) -> None:
    now = _now()
    rows = conn.execute("SELECT id, last_activity_at FROM cloud_sessions WHERE status='active'").fetchall()
    for row in rows:
        last = _parse(row["last_activity_at"])
        if now >= last + timedelta(minutes=IDLE_TIMEOUT_MINUTES):
            conn.execute(
                "UPDATE cloud_sessions SET status='ended', ended_at=?, end_reason='idle_timeout' WHERE id=?",
                (now.isoformat(), row["id"]),
            )


def _serialize(row: sqlite3.Row) -> dict[str, Any]:
    now = _now()
    expires = _parse(row["expires_at"])
    seconds = max(0, int((expires - now).total_seconds())) if row["status"] == "active" else 0
    return {
        "id": row["id"],
        "provider": row["provider"],
        "status": row["status"],
        "started_at": row["started_at"],
        "last_activity_at": row["last_activity_at"],
        "expires_at": row["expires_at"],
        "ended_at": row["ended_at"],
        "end_reason": row["end_reason"],
        "seconds_until_expiry": seconds,
        "warning": row["status"] == "active" and seconds <= WARNING_MINUTES * 60,
    }


def list_sessions() -> dict[str, Any]:
    with _connect() as conn:
        _expire_due(conn)
        rows = conn.execute(
            "SELECT * FROM cloud_sessions ORDER BY started_at DESC"
        ).fetchall()
        latest: dict[str, dict[str, Any]] = {}
        history = [_serialize(row) for row in rows]
        for session in history:
            latest.setdefault(session["provider"], session)
        providers = []
        for provider in PROVIDERS:
            session = latest.get(provider)
            providers.append({
                "provider": provider,
                "connected": False,
                "session": session if session and session["status"] == "active" else None,
            })
        active_count = sum(1 for p in providers if p["session"])
        return {
            "providers": providers,
            "active_sessions": active_count,
            "idle_timeout_minutes": IDLE_TIMEOUT_MINUTES,
            "warning_minutes": WARNING_MINUTES,
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
        expires = now + timedelta(minutes=IDLE_TIMEOUT_MINUTES)
        session_id = str(uuid4())
        conn.execute(
            """INSERT INTO cloud_sessions
            (id, provider, status, started_at, last_activity_at, expires_at)
            VALUES (?, ?, 'active', ?, ?, ?)""",
            (session_id, provider, now.isoformat(), now.isoformat(), expires.isoformat()),
        )
        row = conn.execute("SELECT * FROM cloud_sessions WHERE id=?", (session_id,)).fetchone()
        return _serialize(row)


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
        expires = now + timedelta(minutes=IDLE_TIMEOUT_MINUTES)
        conn.execute(
            "UPDATE cloud_sessions SET last_activity_at=?, expires_at=? WHERE id=?",
            (now.isoformat(), expires.isoformat(), row["id"]),
        )
        updated = conn.execute("SELECT * FROM cloud_sessions WHERE id=?", (row["id"],)).fetchone()
        return _serialize(updated)


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
        ended = conn.execute("SELECT * FROM cloud_sessions WHERE id=?", (row["id"],)).fetchone()
        return _serialize(ended)


def end_all_sessions() -> dict[str, Any]:
    with _connect() as conn:
        _expire_due(conn)
        now = _now().isoformat()
        cursor = conn.execute(
            "UPDATE cloud_sessions SET status='ended', ended_at=?, end_reason='end_all' WHERE status='active'",
            (now,),
        )
        return {"ended_count": cursor.rowcount, "ended_at": now}

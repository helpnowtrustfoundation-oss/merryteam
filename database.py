"""SQLite persistence layer for the attendance bot."""
from __future__ import annotations

import logging
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from werkzeug.security import generate_password_hash

from config import ADMIN_PASSWORD, ADMIN_USERNAME, DB_PATH
from utils import now_ts

logger = logging.getLogger("merry-team.database")


def _resolve_db_path() -> Path:
    """Use configured DB path if writable; otherwise fall back to a local file."""
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        if os.access(DB_PATH.parent, os.W_OK):
            return DB_PATH
        logger.warning("DB folder not writable: %s", DB_PATH.parent)
    except OSError as exc:
        logger.warning("Cannot prepare DB folder %s: %s", DB_PATH.parent, exc)
    fallback = Path("attendance.db")
    logger.warning("Using fallback DB: %s (data may not persist across redeploys)", fallback)
    return fallback


ACTIVE_DB_PATH = _resolve_db_path()

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id   INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    employee_id   TEXT NOT NULL UNIQUE,
    role          TEXT NOT NULL DEFAULT 'employee',
    status        TEXT NOT NULL DEFAULT 'pending',
    registered_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS attendance (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(telegram_id),
    date       TEXT NOT NULL,
    check_in   REAL NOT NULL,
    check_out  REAL,
    work_seconds REAL,
    UNIQUE(user_id, date)
);

CREATE TABLE IF NOT EXISTS breaks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    attendance_id INTEGER NOT NULL REFERENCES attendance(id),
    type          TEXT NOT NULL,
    start_time    REAL NOT NULL,
    end_time      REAL,
    duration_seconds REAL
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS admins (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);
CREATE INDEX IF NOT EXISTS idx_breaks_attendance ON breaks(attendance_id);
"""


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    db = sqlite3.connect(ACTIVE_DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    with get_db() as db:
        db.executescript(SCHEMA)
        db.execute(
            "INSERT OR IGNORE INTO settings(key, value) VALUES ('late_after', '09:30')"
        )
        # Pehli baar env se default admin banayein (Baad me CLI se add karein)
        if ADMIN_PASSWORD and not db.execute("SELECT 1 FROM admins LIMIT 1").fetchone():
            db.execute(
                "INSERT INTO admins(username, password_hash, created_at) VALUES (?, ?, ?)",
                (ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD), now_ts()),
            )


# ---------- settings ----------

def get_setting(key: str, default: str = "") -> str:
    with get_db() as db:
        row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with get_db() as db:
        db.execute(
            "INSERT INTO settings(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


# ---------- users ----------

def get_user(telegram_id: int):
    with get_db() as db:
        return db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()


def get_user_by_identifier(identifier: str):
    """Look up by employee ID first, then by Telegram ID."""
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM users WHERE employee_id = ? COLLATE NOCASE", (identifier,)
        ).fetchone()
        if row is None and identifier.isdigit():
            row = db.execute(
                "SELECT * FROM users WHERE telegram_id = ?", (int(identifier),)
            ).fetchone()
        return row


def employee_id_exists(employee_id: str) -> bool:
    with get_db() as db:
        return db.execute(
            "SELECT 1 FROM users WHERE employee_id = ? COLLATE NOCASE", (employee_id,)
        ).fetchone() is not None


def create_user(telegram_id: int, name: str, employee_id: str) -> None:
    with get_db() as db:
        db.execute(
            "INSERT INTO users(telegram_id, name, employee_id, registered_at) "
            "VALUES (?, ?, ?, ?)",
            (telegram_id, name.strip(), employee_id.strip(), now_ts()),
        )


def set_user_status(telegram_id: int, status: str) -> None:
    with get_db() as db:
        db.execute(
            "UPDATE users SET status = ? WHERE telegram_id = ?", (status, telegram_id)
        )


def users_with_status(status: str | None = None):
    with get_db() as db:
        if status is None:
            return db.execute("SELECT * FROM users ORDER BY name").fetchall()
        return db.execute(
            "SELECT * FROM users WHERE status = ? ORDER BY name", (status,)
        ).fetchall()


def approved_users():
    return users_with_status("approved")


# ---------- attendance ----------

def get_attendance(telegram_id: int, date: str):
    with get_db() as db:
        return db.execute(
            "SELECT * FROM attendance WHERE user_id = ? AND date = ?",
            (telegram_id, date),
        ).fetchone()


def get_attendance_by_id(attendance_id: int):
    with get_db() as db:
        return db.execute(
            "SELECT * FROM attendance WHERE id = ?", (attendance_id,)
        ).fetchone()


def check_in(telegram_id: int, date: str, ts: float) -> int:
    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO attendance(user_id, date, check_in) VALUES (?, ?, ?)",
            (telegram_id, date, ts),
        )
        return cursor.lastrowid


def check_out(attendance_id: int, ts: float, work_seconds: int) -> None:
    with get_db() as db:
        db.execute(
            "UPDATE attendance SET check_out = ?, work_seconds = ? WHERE id = ?",
            (ts, work_seconds, attendance_id),
        )


def attendance_for_dates(dates: tuple[str, ...]):
    if not dates:
        return []
    placeholders = ",".join("?" for _ in dates)
    with get_db() as db:
        return db.execute(
            f"SELECT a.*, u.name, u.employee_id FROM attendance a "
            f"JOIN users u ON u.telegram_id = a.user_id "
            f"WHERE a.date IN ({placeholders}) ORDER BY a.date DESC, u.name",
            dates,
        ).fetchall()


def attendance_for_month(month: str):
    with get_db() as db:
        return db.execute(
            "SELECT a.*, u.name, u.employee_id FROM attendance a "
            "JOIN users u ON u.telegram_id = a.user_id "
            "WHERE a.date LIKE ? ORDER BY a.date, u.name",
            (f"{month}-%",),
        ).fetchall()


# ---------- breaks ----------

def active_break(attendance_id: int):
    with get_db() as db:
        return db.execute(
            "SELECT * FROM breaks WHERE attendance_id = ? AND end_time IS NULL "
            "ORDER BY start_time DESC LIMIT 1",
            (attendance_id,),
        ).fetchone()


def start_break(attendance_id: int, break_type: str, ts: float) -> int:
    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO breaks(attendance_id, type, start_time) VALUES (?, ?, ?)",
            (attendance_id, break_type, ts),
        )
        return cursor.lastrowid


def end_break(break_id: int, ts: float, duration_seconds: int) -> None:
    with get_db() as db:
        db.execute(
            "UPDATE breaks SET end_time = ?, duration_seconds = ? WHERE id = ?",
            (ts, duration_seconds, break_id),
        )


def breaks_for_attendance(attendance_id: int):
    with get_db() as db:
        return db.execute(
            "SELECT * FROM breaks WHERE attendance_id = ? ORDER BY start_time",
            (attendance_id,),
        ).fetchall()


def breaks_for_month(month: str):
    with get_db() as db:
        return db.execute(
            "SELECT b.*, a.user_id, a.date, u.name, u.employee_id FROM breaks b "
            "JOIN attendance a ON a.id = b.attendance_id "
            "JOIN users u ON u.telegram_id = a.user_id "
            "WHERE a.date LIKE ? ORDER BY a.date, u.name, b.start_time",
            (f"{month}-%",),
        ).fetchall()


# ---------- web admins ----------

def get_admin(username: str):
    with get_db() as db:
        return db.execute(
            "SELECT * FROM admins WHERE username = ? COLLATE NOCASE", (username,)
        ).fetchone()


def list_admins():
    with get_db() as db:
        return db.execute("SELECT id, username, created_at FROM admins ORDER BY username").fetchall()


def add_admin(username: str, password_hash: str) -> None:
    with get_db() as db:
        db.execute(
            "INSERT INTO admins(username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, now_ts()),
        )


def remove_admin(username: str) -> bool:
    with get_db() as db:
        cursor = db.execute("DELETE FROM admins WHERE username = ?", (username,))
        return cursor.rowcount > 0

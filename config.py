"""Environment configuration for the attendance bot."""
from __future__ import annotations

import os
import secrets
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

ADMIN_IDS: set[int] = {
    int(part.strip())
    for part in os.getenv("ADMIN_IDS", "").split(",")
    if part.strip().isdigit()
}

_raw_timezone = os.getenv("TIMEZONE", "Asia/Kolkata").strip()
# "Asia/Kolkata (auto)" jaase values ko bhi safari kar lein
_raw_timezone = _raw_timezone.split("(")[0].strip() or "Asia/Kolkata"
try:
    ZoneInfo(_raw_timezone)
except (ZoneInfoNotFoundError, ValueError):
    _raw_timezone = "Asia/Kolkata"
TIMEZONE: str = _raw_timezone
_raw_db_path = os.getenv("DB_PATH", "attendance.db").strip().split("(")[0].strip()
DB_PATH: Path = Path(_raw_db_path or "attendance.db")

# External database (Render free par persistent storage ke liye Neon/Supabase PostgreSQL)
DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()
USE_POSTGRES: bool = DATABASE_URL.startswith(("postgres://", "postgresql://"))

# Web admin login
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin").strip() or "admin"
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "").strip()
SECRET_KEY: str = os.getenv("SECRET_KEY", "").strip() or secrets.token_hex(32)
PORT: int = int(os.getenv("PORT", "5000"))

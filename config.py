"""Environment configuration for the attendance bot."""
from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

ADMIN_IDS: set[int] = {
    int(part.strip())
    for part in os.getenv("ADMIN_IDS", "").split(",")
    if part.strip().isdigit()
}

TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Kolkata").strip() or "Asia/Kolkata"
DB_PATH: Path = Path(os.getenv("DB_PATH", "attendance.db").strip() or "attendance.db")

# Web admin login
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin").strip() or "admin"
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "").strip()
SECRET_KEY: str = os.getenv("SECRET_KEY", "").strip() or secrets.token_hex(32)
PORT: int = int(os.getenv("PORT", "5000"))

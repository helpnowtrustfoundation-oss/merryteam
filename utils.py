"""Time helpers, constants and formatting used across the bot."""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from config import TIMEZONE

TZ = ZoneInfo(TIMEZONE)

LABEL_IN = "\U0001F7E2 Check In"
LABEL_OUT = "\U0001F534 Check Out"
LABEL_TEA = "\U0001F375 Tea Break"
LABEL_WASHROOM = "\U0001F6BA Washroom Break"
LABEL_LUNCH = "\U0001F371 Lunch Break"
LABEL_OTHER = "\u2615 Other Break"
LABEL_END = "\u2705 End Break"
LABEL_MY = "\U0001F4CA My Attendance"

MENU_LABELS = [
    LABEL_IN,
    LABEL_OUT,
    LABEL_TEA,
    LABEL_WASHROOM,
    LABEL_LUNCH,
    LABEL_OTHER,
    LABEL_END,
    LABEL_MY,
]

BREAK_TYPES = {
    LABEL_TEA: "tea",
    LABEL_WASHROOM: "washroom",
    LABEL_LUNCH: "lunch",
    LABEL_OTHER: "other",
}

BREAK_NAMES = {
    "tea": "Tea Break",
    "washroom": "Washroom Break",
    "lunch": "Lunch Break",
    "other": "Other Break",
}


def now_ts() -> float:
    """Current UTC epoch timestamp."""
    return datetime.now(timezone.utc).timestamp()


def to_local(ts: float) -> datetime:
    return datetime.fromtimestamp(ts, TZ)


def today_str() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


def month_str() -> str:
    return datetime.now(TZ).strftime("%Y-%m")


def date_of(ts: float) -> str:
    return to_local(ts).strftime("%Y-%m-%d")


def time_str(ts: float) -> str:
    return to_local(ts).strftime("%H:%M:%S")


def hhmm_str(ts: float) -> str:
    return to_local(ts).strftime("%H:%M")


def duration_str(seconds: float | None) -> str:
    if seconds is None:
        return "\u2014"
    total = max(0, int(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def parse_hhmm(value: str) -> tuple[int, int] | None:
    try:
        hour, minute = value.split(":")
        hour, minute = int(hour), int(minute)
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return hour, minute
    except (ValueError, AttributeError):
        pass
    return None


def is_late(check_in_ts: float, late_after: str) -> bool:
    parsed = parse_hhmm(late_after)
    if parsed is None:
        return False
    local = to_local(check_in_ts)
    return (local.hour, local.minute) > parsed


def valid_month(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m")
        return True
    except ValueError:
        return False


def esc(text: object) -> str:
    """Escape a value for Telegram's default Markdown parse mode."""
    return str(text).replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")

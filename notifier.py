"""Send Telegram messages from the Flask thread via the bot's event loop."""
from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger("merry-team.notifier")

_loop: asyncio.AbstractEventLoop | None = None
_app = None


def configure(loop: asyncio.AbstractEventLoop, application) -> None:
    global _loop, _app
    _loop = loop
    _app = application


def send_sync(telegram_id: int, text: str, reply_markup=None) -> bool:
    """Thread-safe send. Returns False when the bot is not running."""
    if _loop is None or _app is None:
        return False

    async def _send() -> bool:
        try:
            await _app.bot.send_message(
                chat_id=telegram_id, text=text, reply_markup=reply_markup
            )
            return True
        except Exception as exc:
            logger.warning("Telegram message to %s failed: %s", telegram_id, exc)
            return False

    try:
        return asyncio.run_coroutine_threadsafe(_send(), _loop).result(timeout=8)
    except Exception as exc:
        logger.warning("Could not schedule Telegram message: %s", exc)
        return False

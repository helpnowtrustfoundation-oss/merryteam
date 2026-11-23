"""Start the Merry Team web admin app and the Telegram bot together."""
from __future__ import annotations

import asyncio
import logging
import threading

from telegram import Update

import notifier
from bot import build_app
from config import BOT_TOKEN, PORT, USE_POSTGRES
from database import ACTIVE_DB_PATH, init_db
from webapp import app as web_app

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("merry-team.main")


def run_bot() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        application = build_app()
        notifier.configure(loop, application)
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            stop_signals=None,
            close_loop=False,
        )
    except Exception:
        logger.exception("Telegram bot thread band ho gaya")


def main() -> None:
    init_db()
    logger.info(
        "Database: %s", "PostgreSQL (DATABASE_URL)" if USE_POSTGRES else ACTIVE_DB_PATH
    )

    if BOT_TOKEN:
        threading.Thread(target=run_bot, name="telegram-bot", daemon=True).start()
        logger.info("Telegram bot shuru ho gaya.")
    else:
        logger.warning("BOT_TOKEN missing — sirf web admin chalega.")

    logger.info("Web admin chal raha hai: http://0.0.0.0:%s/login", PORT)
    web_app.run(host="0.0.0.0", port=PORT, threaded=True, use_reloader=False)


if __name__ == "__main__":
    main()

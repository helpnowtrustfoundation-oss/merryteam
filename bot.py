"""Telegram bot for Merry Team (employee flow only)."""
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import database as db
from config import BOT_TOKEN
from handlers import employee
from i18n import t

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("merry-team")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = db.get_user_language(update.effective_user.id)
    await update.message.reply_text(t("bot.help", lang))


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Update failed: %s", context.error, exc_info=context.error)


def build_app() -> Application:
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", employee.start))
    application.add_handler(CommandHandler("cancel", employee.cancel))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("attendance", employee.my_attendance))
    application.add_handler(CommandHandler("language", employee.language_command))
    application.add_handler(
        CallbackQueryHandler(employee.language_callback, pattern=r"^lang:")
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, employee.handle_text)
    )
    application.add_error_handler(on_error)
    return application

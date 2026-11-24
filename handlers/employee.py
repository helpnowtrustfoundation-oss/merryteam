"""Employee registration and daily attendance flow."""
from __future__ import annotations

import re
from datetime import datetime, timedelta

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

import database as db
from config import ADMIN_IDS
from i18n import (
    BREAK_ACTIONS,
    LANG_LABELS,
    action_for_label,
    break_name,
    menu_rows,
    normalize_lang,
    t,
)
from utils import TZ, duration_str, hhmm_str, now_ts, time_str, today_str


def _lang(user=None, context: ContextTypes.DEFAULT_TYPE | None = None) -> str:
    """Language of a user row, with a safe fallback for pre-migration rows."""
    if user is not None:
        try:
            return normalize_lang(user["language"])
        except (KeyError, IndexError, TypeError):
            pass
    if context is not None and context.user_data.get("pending_lang"):
        return normalize_lang(context.user_data["pending_lang"])
    return "en"


def menu_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(menu_rows(lang), resize_keyboard=True, one_time_keyboard=False)


async def _send_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    lang: str = "en",
) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=menu_keyboard(lang),
    )


async def _notify_admins(context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=text)
        except Exception:
            pass  # Admin ne bot ko block kar diya ho to ignore


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start and drive the short registration flow."""
    telegram_id = update.effective_user.id
    user = db.get_user(telegram_id)
    lang = _lang(user, context)

    if user is not None:
        if user["status"] == "approved":
            await _send_menu(
                update, context, t("bot.welcome_back", lang, name=user["name"]), lang
            )
            return
        if user["status"] == "pending":
            await update.message.reply_text(t("bot.pending", lang))
            return
        await update.message.reply_text(t("bot.rejected", lang))
        return

    context.user_data["reg_state"] = "name"
    await update.message.reply_text(t("bot.welcome", lang))


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = _lang(db.get_user(update.effective_user.id), context)
    if context.user_data.pop("reg_state", None):
        context.user_data.pop("reg_name", None)
        await update.message.reply_text(t("bot.cancel_done", lang))
    else:
        await update.message.reply_text(t("bot.cancel_none", lang))


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Let an employee pick English or 中文; answer with an inline keyboard."""
    lang = _lang(db.get_user(update.effective_user.id), context)
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(LANG_LABELS["en"], callback_data="lang:en"),
                InlineKeyboardButton(LANG_LABELS["zh"], callback_data="lang:zh"),
            ]
        ]
    )
    await update.message.reply_text(t("bot.language_prompt", lang), reply_markup=keyboard)


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Store the chosen language and refresh the reply keyboard."""
    query = update.callback_query
    await query.answer()
    lang = normalize_lang((query.data or "").split(":", 1)[-1])
    telegram_id = query.from_user.id

    user = db.get_user(telegram_id)
    if user is not None:
        db.set_user_language(telegram_id, lang)
    else:
        context.user_data["pending_lang"] = lang

    await query.edit_message_text(
        t("bot.language_saved", lang, label=LANG_LABELS[lang])
    )
    if user is not None and user["status"] == "approved":
        await context.bot.send_message(
            chat_id=telegram_id,
            text=t("bot.welcome_back", lang, name=user["name"]),
            reply_markup=menu_keyboard(lang),
        )


async def _finish_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> None:
    telegram_id = update.effective_user.id
    name = context.user_data.pop("reg_name", "").strip()
    employee_id = text.strip()
    lang = _lang(context=context)

    if not re.fullmatch(r"[A-Za-z0-9_-]{2,32}", employee_id):
        await update.message.reply_text(t("bot.emp_invalid", lang))
        return
    if db.employee_id_exists(employee_id):
        await update.message.reply_text(t("bot.emp_taken", lang))
        return

    db.create_user(telegram_id, name, employee_id, language=lang)
    context.user_data.pop("reg_state", None)
    await update.message.reply_text(
        t("bot.reg_saved", lang, name=name, employee_id=employee_id)
    )
    await _notify_admins(
        context,
        t(
            "bot.admin_new_reg",
            "en",  # admin notification stays in the original admin-facing language
            name=name,
            employee_id=employee_id,
            telegram_id=telegram_id,
        ),
    )


async def _approved_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    user = db.get_user(telegram_id)
    lang = _lang(user, context)
    if user is None:
        await update.message.reply_text(t("bot.not_registered", lang))
        return None
    if user["status"] != "approved":
        await update.message.reply_text(t("bot.not_approved", lang))
        return None
    return user


async def _do_check_in(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user, lang: str
) -> None:
    telegram_id = user["telegram_id"]
    date = today_str()
    existing = db.get_attendance(telegram_id, date)
    if existing:
        await update.message.reply_text(
            t("bot.duplicate_checkin", lang, time=hhmm_str(existing["check_in"]))
        )
        return
    ts = now_ts()
    db.check_in(telegram_id, date, ts)
    await update.message.reply_text(t("bot.checkin_ok", lang, time=time_str(ts)))


async def _do_break(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user,
    action: str,
    lang: str,
) -> None:
    date = today_str()
    att = db.get_attendance(user["telegram_id"], date)
    if att is None:
        await update.message.reply_text(t("bot.checkin_first", lang))
        return
    if att["check_out"] is not None:
        await update.message.reply_text(t("bot.checked_out_break", lang))
        return
    running = db.active_break(att["id"])
    if running:
        await update.message.reply_text(
            t(
                "bot.break_running",
                lang,
                break_name=break_name(running["type"], lang),
                time=hhmm_str(running["start_time"]),
            )
        )
        return
    ts = now_ts()
    db.start_break(att["id"], action, ts)
    await update.message.reply_text(
        t(
            "bot.break_started",
            lang,
            break_name=break_name(action, lang),
            time=time_str(ts),
        )
    )


async def _do_end_break(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user, lang: str
) -> None:
    att = db.get_attendance(user["telegram_id"], today_str())
    if att is None:
        await update.message.reply_text(t("bot.no_break_att", lang))
        return
    running = db.active_break(att["id"])
    if running is None:
        await update.message.reply_text(t("bot.no_break", lang))
        return
    ts = now_ts()
    seconds = int(ts - running["start_time"])
    db.end_break(running["id"], ts, seconds)
    await update.message.reply_text(
        t(
            "bot.break_ended",
            lang,
            break_name=break_name(running["type"], lang),
            time=time_str(ts),
            duration=duration_str(seconds),
        )
    )


async def _do_check_out(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user, lang: str
) -> None:
    att = db.get_attendance(user["telegram_id"], today_str())
    if att is None:
        await update.message.reply_text(t("bot.checkin_first", lang))
        return
    if att["check_out"] is not None:
        await update.message.reply_text(
            t("bot.duplicate_checkout", lang, time=hhmm_str(att["check_out"]))
        )
        return

    note = ""
    running = db.active_break(att["id"])
    ts = now_ts()
    if running:
        db.end_break(running["id"], ts, int(ts - running["start_time"]))
        note = t("bot.auto_end_note", lang)

    breaks = db.breaks_for_attendance(att["id"])
    total_break = sum(b["duration_seconds"] or 0 for b in breaks)
    work = max(0, int(ts - att["check_in"] - total_break))
    db.check_out(att["id"], ts, work)

    await update.message.reply_text(
        t(
            "bot.checkout_done",
            lang,
            time=time_str(ts),
            in_time=hhmm_str(att["check_in"]),
            total_break=duration_str(total_break),
            work=duration_str(work),
            note=note,
        )
    )


async def my_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await _approved_user(update, context)
    if user is None:
        return
    lang = _lang(user, context)
    telegram_id = user["telegram_id"]
    date = today_str()
    att = db.get_attendance(telegram_id, date)

    lines = [t("bot.attendance_title", lang, name=user["name"]), ""]
    if att is None:
        lines.append(t("bot.no_checkin_today", lang))
    else:
        breaks = db.breaks_for_attendance(att["id"])
        total_break = sum(b["duration_seconds"] or 0 for b in breaks)
        running = db.active_break(att["id"])
        end_ts = att["check_out"] or now_ts()
        work = max(0, int(end_ts - att["check_in"] - total_break))
        lines.append(t("bot.today", lang, date=date))
        lines.append(
            f"• {t('bot.field.check_in', lang)}: {hhmm_str(att['check_in'])}"
        )
        check_out = (
            hhmm_str(att["check_out"])
            if att["check_out"]
            else t("bot.check_out_pending", lang)
        )
        lines.append(f"• {t('bot.field.check_out', lang)}: {check_out}")
        lines.append(t("bot.total_break", lang, value=duration_str(total_break)))
        lines.append(t("bot.working_time", lang, value=duration_str(work)))
        if breaks:
            lines.extend(["", t("bot.breaks_header", lang)])
            for b in breaks:
                status = (
                    f"{hhmm_str(b['start_time'])} – {t('bot.break_running_short', lang)}"
                    if b["end_time"] is None
                    else f"{hhmm_str(b['start_time'])} – {hhmm_str(b['end_time'])}"
                )
                lines.append(
                    f"  • {break_name(b['type'], lang)}: {status} "
                    f"({duration_str(b['duration_seconds'])})"
                )
        if running:
            lines.append(t("bot.break_active", lang))

    dates = tuple(
        (datetime.now(TZ) - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 8)
    )
    history = {row["date"]: row for row in db.attendance_for_dates(dates)}
    lines.extend(["", t("bot.last_7", lang)])
    for day in dates:
        row = history.get(day)
        if row is None:
            lines.append(f"{day}:  \u2014")
        else:
            secs = row["work_seconds"]
            if secs is None:
                secs = max(0, int(now_ts() - row["check_in"]))
            out = hhmm_str(row["check_out"]) if row["check_out"] else "..."
            lines.append(
                f"{day}:  {hhmm_str(row['check_in'])} → {out}  {duration_str(secs)}"
            )

    await update.message.reply_text("\n".join(lines))


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route non-command text: registration steps first, then menu buttons."""
    text = update.message.text.strip()
    reg_state = context.user_data.get("reg_state")
    user = db.get_user(update.effective_user.id)
    lang = _lang(user, context)

    if reg_state == "name":
        name = text
        if len(name) < 2 or len(name) > 60 or "\n" in name:
            await update.message.reply_text(t("bot.name_invalid", lang))
            return
        context.user_data["reg_name"] = name
        context.user_data["reg_state"] = "emp_id"
        await update.message.reply_text(t("bot.name_thanks", lang, name=name))
        return

    if reg_state == "emp_id":
        await _finish_registration(update, context, text)
        return

    if user is None:
        # Koi bhi pehla message registration shuru kar deta hai
        context.user_data["reg_state"] = "name"
        await update.message.reply_text(t("bot.first_message", lang))
        return

    if user["status"] != "approved":
        await update.message.reply_text(t("bot.pending", lang))
        return

    action = action_for_label(text)
    if action is None:
        await _send_menu(update, context, t("bot.use_buttons", lang), lang)
        return

    user = await _approved_user(update, context)
    if user is None:
        return

    if action == "in":
        await _do_check_in(update, context, user, lang)
    elif action == "out":
        await _do_check_out(update, context, user, lang)
    elif action in BREAK_ACTIONS:
        await _do_break(update, context, user, action, lang)
    elif action == "end":
        await _do_end_break(update, context, user, lang)
    elif action == "my":
        await my_attendance(update, context)

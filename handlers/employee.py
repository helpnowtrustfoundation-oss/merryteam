"""Employee registration and daily attendance flow."""
from __future__ import annotations

import re
from datetime import datetime, timedelta

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

import database as db
from config import ADMIN_IDS
from utils import (
    BREAK_NAMES,
    BREAK_TYPES,
    LABEL_END,
    LABEL_IN,
    LABEL_MY,
    LABEL_OUT,
    MENU_LABELS,
    TZ,
    duration_str,
    hhmm_str,
    now_ts,
    time_str,
    today_str,
)


def menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [MENU_LABELS[i : i + 2] for i in range(0, len(MENU_LABELS), 2)]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=False)


async def _send_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=menu_keyboard(),
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

    if user is not None:
        if user["status"] == "approved":
            await _send_menu(update, context, f"Namaste {user['name']}! 👋\nNiche se kaam chunin.")
            return
        if user["status"] == "pending":
            await update.message.reply_text(
                "Aapka registration admin ke paas pending hai. Approve hone tak wait karein."
            )
            return
        await update.message.reply_text(
            "Aapka registration reject ho chuka hai. Kisi admin se baat karein."
        )
        return

    context.user_data["reg_state"] = "name"
    await update.message.reply_text(
        "Namaste! *Merry Team — Office Attendance Bot* me swagat hai. 👋\nAapka **naam** likhein:"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.pop("reg_state", None):
        context.user_data.pop("reg_name", None)
        await update.message.reply_text(
            "Registration cancel ho gaya. Dobare /start se shuru karein."
        )
    else:
        await update.message.reply_text("Kuch cancel karne ke liye nahi hai.")


async def _finish_registration(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    telegram_id = update.effective_user.id
    name = context.user_data.pop("reg_name", "").strip()
    employee_id = text.strip()

    if not re.fullmatch(r"[A-Za-z0-9_-]{2,32}", employee_id):
        await update.message.reply_text(
            "Employee ID sirf letters, numbers, '-' ya '_' se ban sakti hai (2-32 characters). "
            "Dobara likhein:"
        )
        return
    if db.employee_id_exists(employee_id):
        await update.message.reply_text(
            "Ye employee ID pehle se registered hai. Koi doosri ID likhein:"
        )
        return

    db.create_user(telegram_id, name, employee_id)
    context.user_data.pop("reg_state", None)
    await update.message.reply_text(
        f"✅ Registration save ho gaya!\n\nNaam: {name}\nEmployee ID: {employee_id}\n\n"
        "Admin ke approve karne ka intezaar karein."
    )
    await _notify_admins(
        context,
        f"🆕 Naya registration:\nName: {name}\nEmployee ID: {employee_id}\n"
        f"Telegram ID: {telegram_id}\n\nAdmin web panel me approve karein.",
    )


async def _approved_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    user = db.get_user(telegram_id)
    if user is None:
        await update.message.reply_text("Pehle /start se register karein.")
        return None
    if user["status"] != "approved":
        await update.message.reply_text(
            "Aapka account abhi approve nahi hua hai. Admin ke approve ka intezaar karein."
        )
        return None
    return user


async def _do_check_in(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    telegram_id = user["telegram_id"]
    date = today_str()
    existing = db.get_attendance(telegram_id, date)
    if existing:
        await update.message.reply_text(
            f"Aap aaj pehle hi {hhmm_str(existing['check_in'])} par check-in kar chuke hain."
        )
        return
    ts = now_ts()
    db.check_in(telegram_id, date, ts)
    await update.message.reply_text(
        f"✅ Check In: {time_str(ts)}\n\nBreak ke liye neeche ka button dabayein."
    )


async def _do_break(update: Update, context: ContextTypes.DEFAULT_TYPE, user, label: str) -> None:
    date = today_str()
    att = db.get_attendance(user["telegram_id"], date)
    if att is None:
        await update.message.reply_text("Pehle Check In karein.")
        return
    if att["check_out"] is not None:
        await update.message.reply_text("Aaj ka Check Out ho chuka hai. Naya break nahi le sakte.")
        return
    running = db.active_break(att["id"])
    if running:
        await update.message.reply_text(
            f"Ek break pehle se chal raha hai: {BREAK_NAMES.get(running['type'], running['type'])} "
            f"({hhmm_str(running['start_time'])} se). Pehle **End Break** dabayein."
        )
        return
    break_type = BREAK_TYPES[label]
    ts = now_ts()
    db.start_break(att["id"], break_type, ts)
    await update.message.reply_text(
        f"⏸️ {BREAK_NAMES[break_type]} start: {time_str(ts)}\nWapas aane par **End Break** dabayein."
    )


async def _do_end_break(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    att = db.get_attendance(user["telegram_id"], today_str())
    if att is None:
        await update.message.reply_text("Koi active break nahi mila. Pehle Check In karein.")
        return
    running = db.active_break(att["id"])
    if running is None:
        await update.message.reply_text("Koi break abhi chal nahi raha hai.")
        return
    ts = now_ts()
    seconds = int(ts - running["start_time"])
    db.end_break(running["id"], ts, seconds)
    await update.message.reply_text(
        f"✅ {BREAK_NAMES.get(running['type'], 'Break')} khatam: {time_str(ts)}\n"
        f"Duration: {duration_str(seconds)}"
    )


async def _do_check_out(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    att = db.get_attendance(user["telegram_id"], today_str())
    if att is None:
        await update.message.reply_text("Pehle Check In karein.")
        return
    if att["check_out"] is not None:
        await update.message.reply_text(
            f"Aaj ka Check Out pehle hi {hhmm_str(att['check_out'])} par ho chuka hai."
        )
        return

    note = ""
    running = db.active_break(att["id"])
    ts = now_ts()
    if running:
        db.end_break(running["id"], ts, int(ts - running["start_time"]))
        note = "\n(Chal raha break auto-end kar diya gaya.)"

    breaks = db.breaks_for_attendance(att["id"])
    total_break = sum(b["duration_seconds"] or 0 for b in breaks)
    work = max(0, int(ts - att["check_in"] - total_break))
    db.check_out(att["id"], ts, work)

    await update.message.reply_text(
        f"🏁 Check Out: {time_str(ts)}\n"
        f"Check In: {hhmm_str(att['check_in'])}\n"
        f"Total break: {duration_str(total_break)}\n"
        f"Net working time: *{duration_str(work)}*{note}"
    )


async def my_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await _approved_user(update, context)
    if user is None:
        return
    telegram_id = user["telegram_id"]
    date = today_str()
    att = db.get_attendance(telegram_id, date)

    lines = [f"*📊 My Attendance — {user['name']}*", ""]
    if att is None:
        lines.append("Aaj abhi check-in nahi kiya.")
    else:
        breaks = db.breaks_for_attendance(att["id"])
        total_break = sum(b["duration_seconds"] or 0 for b in breaks)
        running = db.active_break(att["id"])
        end_ts = att["check_out"] or now_ts()
        work = max(0, int(end_ts - att["check_in"] - total_break))
        lines.append(f"*Aaj ({date})*")
        lines.append(f"• Check In: {hhmm_str(att['check_in'])}")
        lines.append(
            f"• Check Out: {hhmm_str(att['check_out']) if att['check_out'] else 'abhi tak nahi'}"
        )
        lines.append(f"• Total break: {duration_str(total_break)}")
        lines.append(f"• Working time: {duration_str(work)}")
        if breaks:
            lines.append("")
            lines.append("*Breaks:*")
            for b in breaks:
                status = (
                    f"{hhmm_str(b['start_time'])} – chal raha hai"
                    if b["end_time"] is None
                    else f"{hhmm_str(b['start_time'])} – {hhmm_str(b['end_time'])}"
                )
                lines.append(
                    f"  • {BREAK_NAMES.get(b['type'], b['type'])}: {status} "
                    f"({duration_str(b['duration_seconds'])})"
                )
        if running:
            lines.append("_Ek break abhi chal raha hai._")

    dates = tuple(
        (datetime.now(TZ) - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 8)
    )
    history = {row["date"]: row for row in db.attendance_for_dates(dates)}
    lines.extend(["", "*Pichhle 7 din:*"])
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

    if reg_state == "name":
        name = text
        if len(name) < 2 or len(name) > 60 or "\n" in name:
            await update.message.reply_text("Naam 2 se 60 characters ka hona chahiye. Dobare likhein:")
            return
        context.user_data["reg_name"] = name
        context.user_data["reg_state"] = "emp_id"
        await update.message.reply_text(
            f"Thanks {name}. Ab aapka **Employee ID** likhein:"
        )
        return

    if reg_state == "emp_id":
        await _finish_registration(update, context, text)
        return

    user = db.get_user(update.effective_user.id)

    if user is None:
        # Koi bhi pehla message registration shuru kar deta hai
        context.user_data["reg_state"] = "name"
        await update.message.reply_text(
            "Namaste! Office Attendance Bot me swagat hai. 👋\n"
            "Pehle registration karte hain — aapka **naam** likhein:"
        )
        return

    if user["status"] != "approved":
        await update.message.reply_text(
            "Aapka registration admin ke paas pending hai. Approve hone tak wait karein."
        )
        return

    if text not in MENU_LABELS:
        await _send_menu(update, context, "Neeche diye gaye buttons ka istemal karein.")
        return

    user = await _approved_user(update, context)
    if user is None:
        return

    if text == LABEL_IN:
        await _do_check_in(update, context, user)
    elif text == LABEL_OUT:
        await _do_check_out(update, context, user)
    elif text in BREAK_TYPES:
        await _do_break(update, context, user, text)
    elif text == LABEL_END:
        await _do_end_break(update, context, user)
    elif text == LABEL_MY:
        await my_attendance(update, context)

"""Flask web admin app for Merry Team."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

import database as db
from config import SECRET_KEY, TIMEZONE
from handlers.employee import menu_keyboard
from notifier import send_sync
from reports import csv_bytes, monthly_summary, xlsx_bytes
from utils import (
    TZ,
    BREAK_NAMES,
    date_of,
    duration_str,
    hhmm_str,
    is_late,
    month_str,
    parse_hhmm,
    to_local,
    today_str,
    valid_month,
)

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_globals():
    return {
        "current_date": today_str(),
        "timezone_name": TIMEZONE,
        "admin_user": session.get("admin"),
    }


def _parse_date(value: str | None) -> str:
    if value:
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            pass
    return today_str()


def _recent_dates(days: int) -> tuple[str, ...]:
    return tuple(
        (datetime.now(TZ) - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)
    )


# ---------- auth ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = db.get_admin(username)
        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()
            session["admin"] = admin["username"]
            flash(f"Swagat hai, {admin['username']}!", "success")
            target = request.args.get("next") or url_for("dashboard")
            if not target.startswith("/"):
                target = url_for("dashboard")
            return redirect(target)
        flash("Galat username ya password.", "error")
    if session.get("admin"):
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Log out ho gaya.", "info")
    return redirect(url_for("login"))


# ---------- dashboard ----------

@app.route("/")
@login_required
def dashboard():
    date = today_str()
    late_after = db.get_setting("late_after", "09:30")
    att_by_user = {row["user_id"]: row for row in db.attendance_for_dates((date,))}
    present, absent = [], []
    for user in db.approved_users():
        att = att_by_user.get(user["telegram_id"])
        if att is None:
            absent.append(user)
        else:
            present.append(
                {
                    "user": user,
                    "att": att,
                    "late": is_late(att["check_in"], late_after),
                }
            )

    today_breaks = [b for b in db.breaks_for_month(month_str()) if b["date"] == date]
    active_breaks = [b for b in today_breaks if b["end_time"] is None]
    late_count = sum(1 for item in present if item["late"])
    pending_count = len(db.users_with_status("pending"))

    return render_template(
        "dashboard.html",
        date=date,
        present=present,
        absent=absent,
        pending_count=pending_count,
        late_count=late_count,
        active_breaks=active_breaks,
        recent=db.attendance_for_dates(_recent_dates(7))[:8],
        late_after=late_after,
        break_names=BREAK_NAMES,
        hhmm_str=hhmm_str,
        duration_str=duration_str,
    )


# ---------- approvals ----------

@app.route("/pending")
@login_required
def pending():
    return render_template(
        "pending.html", rows=db.users_with_status("pending"), date_of=date_of
    )


@app.post("/pending/<int:tid>/approve")
@login_required
def approve(tid: int):
    user = db.get_user(tid)
    if user and user["status"] == "pending":
        db.set_user_status(tid, "approved")
        sent = send_sync(
            tid,
            "🎉 Aapka registration approve ho gaya!\nAb Telegram par menu use karke attendance karein.",
            menu_keyboard(),
        )
        flash(
            f"{user['name']} approve ho gaya."
            + ("" if sent else " (Telegram notify nahi ho paya)"),
            "success",
        )
    return redirect(url_for("pending"))


@app.post("/pending/<int:tid>/reject")
@login_required
def reject(tid: int):
    user = db.get_user(tid)
    if user and user["status"] == "pending":
        db.set_user_status(tid, "rejected")
        send_sync(tid, "Aapka registration reject ho gaya. Kisi admin se baat karein.")
        flash(f"{user['name']} reject kar diya.", "info")
    return redirect(url_for("pending"))


# ---------- employees ----------

@app.route("/employees")
@login_required
def employees():
    date = today_str()
    att_by_user = {row["user_id"]: row for row in db.attendance_for_dates((date,))}
    return render_template(
        "employees.html",
        users=db.users_with_status(),
        att_by_user=att_by_user,
        hhmm_str=hhmm_str,
    )


@app.route("/employee/<int:tid>")
@login_required
def employee_detail(tid: int):
    user = db.get_user(tid)
    if user is None:
        abort(404)
    late_after = db.get_setting("late_after", "09:30")
    rows = [r for r in db.attendance_for_dates(_recent_dates(30)) if r["user_id"] == tid]
    breaks = [b for b in db.breaks_for_month(month_str()) if b["user_id"] == tid]
    return render_template(
        "employee_detail.html",
        user=user,
        rows=rows,
        breaks=breaks,
        late_after=late_after,
        is_late=is_late,
        hhmm_str=hhmm_str,
        duration_str=duration_str,
        break_names=BREAK_NAMES,
    )


# ---------- reports ----------

@app.route("/today")
@login_required
def today_report():
    date = _parse_date(request.args.get("date"))
    late_after = db.get_setting("late_after", "09:30")
    att_by_user = {row["user_id"]: row for row in db.attendance_for_dates((date,))}
    present, absent = [], []
    for user in db.approved_users():
        att = att_by_user.get(user["telegram_id"])
        if att is None:
            absent.append(user)
        else:
            present.append(
                {
                    "user": user,
                    "att": att,
                    "late": is_late(att["check_in"], late_after),
                }
            )
    return render_template(
        "today.html",
        date=date,
        present=present,
        absent=absent,
        hhmm_str=hhmm_str,
        duration_str=duration_str,
    )


@app.route("/breaks")
@login_required
def breaks_report():
    date = _parse_date(request.args.get("date"))
    rows = [row for row in db.breaks_for_month(date[:7]) if row["date"] == date]
    totals: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    running = []
    for row in rows:
        key = (row["employee_id"], row["name"])
        totals[key][row["type"]] += row["duration_seconds"] or 0
        if row["end_time"] is None:
            running.append(row)
    return render_template(
        "breaks.html",
        date=date,
        totals=totals,
        running=running,
        break_names=BREAK_NAMES,
        hhmm_str=hhmm_str,
        duration_str=duration_str,
    )


@app.route("/late")
@login_required
def late_report():
    date = _parse_date(request.args.get("date"))
    late_after = db.get_setting("late_after", "09:30")
    threshold = parse_hhmm(late_after) or (9, 30)
    late_rows = []
    for row in db.attendance_for_dates((date,)):
        if is_late(row["check_in"], late_after):
            local = to_local(row["check_in"])
            minutes = local.hour * 60 + local.minute - (threshold[0] * 60 + threshold[1])
            late_rows.append({"row": row, "minutes": minutes})
    late_rows.sort(key=lambda item: item["row"]["check_in"], reverse=True)
    return render_template(
        "late.html",
        date=date,
        late_after=late_after,
        late_rows=late_rows,
        hhmm_str=hhmm_str,
    )


@app.route("/month")
@login_required
def month_report():
    month = request.args.get("month") or month_str()
    if not valid_month(month):
        month = month_str()
    stats, totals = monthly_summary(month)
    return render_template(
        "month.html",
        month=month,
        stats=stats,
        totals=totals,
        duration_str=duration_str,
    )


@app.route("/export/<string:fmt>")
@login_required
def export(fmt: str):
    month = request.args.get("month") or month_str()
    if not valid_month(month):
        month = month_str()
    if fmt == "csv":
        stream = csv_bytes(month)
        filename = f"merry_team_attendance_{month}.csv"
        mimetype = "text/csv; charset=utf-8"
    elif fmt == "xlsx":
        stream = xlsx_bytes(month)
        filename = f"merry_team_attendance_{month}.xlsx"
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        abort(404)
    return send_file(stream, as_attachment=True, download_name=filename, mimetype=mimetype)


# ---------- settings ----------

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        value = request.form.get("late_after", "").strip()
        if parse_hhmm(value):
            db.set_setting("late_after", value)
            flash(f"Late cutoff {value} set ho gaya.", "success")
        else:
            flash("Time format galat hai. HH:MM me likhein, jaise 09:30.", "error")
        return redirect(url_for("settings"))
    return render_template(
        "settings.html",
        late_after=db.get_setting("late_after", "09:30"),
        admins=db.list_admins(),
        timezone_name=TIMEZONE,
    )

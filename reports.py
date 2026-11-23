"""Shared report builders used by the web admin app."""
from __future__ import annotations

import csv
import io
from collections import defaultdict

import database as db
from utils import BREAK_NAMES, duration_str, hhmm_str, is_late

HEADERS = ["Date", "Employee ID", "Name", "Check In", "Check Out", "Working Time", "Status"]
BREAK_HEADERS = ["Date", "Employee ID", "Name", "Break Type", "Start", "End", "Duration"]


def _attendance_rows(month: str):
    late_after = db.get_setting("late_after", "09:30")
    rows = []
    for row in db.attendance_for_month(month):
        rows.append(
            [
                row["date"],
                row["employee_id"],
                row["name"],
                hhmm_str(row["check_in"]),
                hhmm_str(row["check_out"]) if row["check_out"] else "",
                duration_str(row["work_seconds"]),
                "Late" if is_late(row["check_in"], late_after) else "On Time",
            ]
        )
    return rows


def _break_rows(month: str):
    rows = []
    for row in db.breaks_for_month(month):
        rows.append(
            [
                row["date"],
                row["employee_id"],
                row["name"],
                BREAK_NAMES.get(row["type"], row["type"]),
                hhmm_str(row["start_time"]),
                hhmm_str(row["end_time"]) if row["end_time"] else "Running",
                duration_str(row["duration_seconds"]),
            ]
        )
    return rows


def csv_bytes(month: str) -> io.BytesIO:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(HEADERS)
    writer.writerows(_attendance_rows(month))
    return io.BytesIO(buffer.getvalue().encode("utf-8-sig"))


def xlsx_bytes(month: str) -> io.BytesIO:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Attendance"
    sheet.append(HEADERS)
    for row in _attendance_rows(month):
        sheet.append(row)

    break_sheet = workbook.create_sheet("Breaks")
    break_sheet.append(BREAK_HEADERS)
    for row in _break_rows(month):
        break_sheet.append(row)

    for ws in (sheet, break_sheet):
        for cell in ws[1]:
            cell.font = Font(bold=True)
        ws.freeze_panes = "A2"
        for column in ws.columns:
            width = max(len(str(cell.value or "")) for cell in column) + 2
            ws.column_dimensions[column[0].column_letter].width = min(width, 40)

    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


def monthly_summary(month: str) -> tuple[list[dict], dict]:
    """Return per-employee stats and grand totals for a month."""
    late_after = db.get_setting("late_after", "09:30")
    attendance = db.attendance_for_month(month)
    break_totals: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row in db.breaks_for_month(month):
        break_totals[row["user_id"]][row["type"]] += row["duration_seconds"] or 0

    stats: dict[int, dict] = {}
    for row in attendance:
        entry = stats.setdefault(
            row["user_id"],
            {
                "name": row["name"],
                "employee_id": row["employee_id"],
                "days": 0,
                "work": 0.0,
                "late": 0,
                "tea": 0.0,
                "lunch": 0.0,
                "washroom": 0.0,
                "other": 0.0,
            },
        )
        entry["days"] += 1
        entry["work"] += row["work_seconds"] or 0
        if is_late(row["check_in"], late_after):
            entry["late"] += 1

    result = []
    for uid, entry in stats.items():
        breaks = break_totals.get(uid, {})
        for kind in ("tea", "lunch", "washroom", "other"):
            entry[kind] = breaks.get(kind, 0)
        result.append(entry)
    result.sort(key=lambda item: item["name"])

    totals = {
        "employees": len(result),
        "days": sum(item["days"] for item in result),
        "work": sum(item["work"] for item in result),
        "late": sum(item["late"] for item in result),
    }
    return result, totals

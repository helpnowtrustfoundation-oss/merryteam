"""Localized strings for the admin dashboard and the Telegram employee menu.

English (Hinglish UI, as it was originally) is the default; 中文 is the
optional second language. Both the web session and each Telegram user keep
their own choice, so restart does not reset it.
"""
from __future__ import annotations

DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ("en", "zh")
LANG_LABELS = {"en": "English", "zh": "中文"}

# Canonical menu actions. Telegram buttons are rendered from MENU_LABELS.
MENU_ACTIONS = ("in", "out", "tea", "washroom", "lunch", "other", "end", "my")
BREAK_ACTIONS = ("tea", "washroom", "lunch", "other")

MENU_LABELS = {
    "en": {
        "in": "🟢 Check In",
        "out": "🔴 Check Out",
        "tea": "🍵 Tea Break",
        "washroom": "🚺 Washroom Break",
        "lunch": "🍱 Lunch Break",
        "other": "☕ Other Break",
        "end": "✅ End Break",
        "my": "📊 My Attendance",
    },
    "zh": {
        "in": "🟢 上班打卡",
        "out": "🔴 下班打卡",
        "tea": "🍵 茶歇",
        "washroom": "🚺 洗手间休息",
        "lunch": "🍱 午餐休息",
        "other": "☕ 其他休息",
        "end": "✅ 结束休息",
        "my": "📊 我的考勤",
    },
}

TEXT = {
    "en": {
        # web shell
        "brand.sub": "Attendance Admin",
        "nav.dashboard": "Dashboard",
        "nav.approvals": "Approvals",
        "nav.employees": "Employees",
        "nav.reports": "REPORTS",
        "nav.today": "Today",
        "nav.breaks": "Breaks",
        "nav.late": "Late comers",
        "nav.monthly": "Monthly",
        "nav.system": "SYSTEM",
        "nav.settings": "Settings",
        "nav.logout": "Logout",
        "topbar.reports": "📊 Reports",
        "web.language_saved": "Language set to {label}.",
        "action.remove": "Remove",
        "action.restore": "Restore",
        "confirm.remove": "Mark {name} as inactive? Attendance records will be kept.",
        "flash.employee_removed": "{name} removed (inactive). Attendance records kept.",
        "flash.employee_restored": "{name} restored to active.",
        # dashboard
        "heading.dashboard": "Dashboard",
        "card.present": "Present today",
        "card.present.hint": "of {total} approved employees",
        "card.absent": "Absent today",
        "card.absent.hint": "abhi tak check-in nahi kiya",
        "card.late": "Late check-ins",
        "card.late.hint": "cutoff {cutoff}",
        "card.pending": "Pending approvals",
        "card.pending.hint": "review karein →",
        "panel.present": "🟢 Present — {date}",
        "panel.absent": "🔴 Absent — {date}",
        "panel.active_breaks": "☕ Abhi chal rahe breaks",
        "panel.recent": "🕒 Recent activity",
        "full_report": "Poori report",
        "table.employee": "Employee",
        "table.id": "ID",
        "table.check_in": "Check In",
        "table.check_out": "Check Out",
        "table.status": "Status",
        "table.break": "Break",
        "table.start": "Start",
        "table.date": "Date",
        "table.work": "Work",
        "badge.late": "Late",
        "badge.on_time": "On time",
        "badge.inside": "Andar",
        "empty.no_checkin": "Aaj abhi koi check-in nahi hua.",
        "empty.all_present": "Sab approved employees present hain. 🎉",
        "empty.no_break": "Koi break abhi chal nahi raha.",
        "break.tea": "Tea Break",
        "break.washroom": "Washroom Break",
        "break.lunch": "Lunch Break",
        "break.other": "Other Break",
        # telegram bot
        "bot.welcome_back": "Namaste {name}! 👋\nNiche se kaam chunin.",
        "bot.pending": "Aapka registration admin ke paas pending hai. Approve hone tak wait karein.",
        "bot.rejected": "Aapka registration reject ho chuka hai. Kisi admin se baat karein.",
        "bot.welcome": "Namaste! *Merry Team — Office Attendance Bot* me swagat hai. 👋\nAapka **naam** likhein:",
        "bot.first_message": "Namaste! Office Attendance Bot me swagat hai. 👋\nPehle registration karte hain — aapka **naam** likhein:",
        "bot.cancel_done": "Registration cancel ho gaya. Dobare /start se shuru karein.",
        "bot.cancel_none": "Kuch cancel karne ke liye nahi hai.",
        "bot.name_invalid": "Naam 2 se 60 characters ka hona chahiye. Dobare likhein:",
        "bot.name_thanks": "Thanks {name}. Ab aapka **Employee ID** likhein:",
        "bot.emp_invalid": "Employee ID sirf letters, numbers, '-' ya '_' se ban sakti hai (2-32 characters). Dobara likhein:",
        "bot.emp_taken": "Ye employee ID pehle se registered hai. Koi doosri ID likhein:",
        "bot.reg_saved": "✅ Registration save ho gaya!\n\nNaam: {name}\nEmployee ID: {employee_id}\n\nAdmin ke approve karne ka intezaar karein.",
        "bot.admin_new_reg": "🆕 Naya registration:\nName: {name}\nEmployee ID: {employee_id}\nTelegram ID: {telegram_id}\n\nAdmin web panel me approve karein.",
        "bot.approved": "🎉 Aapka registration approve ho gaya!\nAb Telegram par menu use karke attendance karein.",
        "bot.not_registered": "Pehle /start se register karein.",
        "bot.not_approved": "Aapka account abhi approve nahi hua hai. Admin ke approve ka intezaar karein.",
        "bot.duplicate_checkin": "Aap aaj pehle hi {time} par check-in kar chuke hain.",
        "bot.duplicate_checkout": "Aaj ka Check Out pehle hi {time} par ho chuka hai.",
        "bot.field.check_in": "Check In",
        "bot.field.check_out": "Check Out",
        "bot.checkin_ok": "✅ Check In: {time}\n\nBreak ke liye neeche ka button dabayein.",
        "bot.checkin_first": "Pehle Check In karein.",
        "bot.checked_out_break": "Aaj ka Check Out ho chuka hai. Naya break nahi le sakte.",
        "bot.break_running": "Ek break pehle se chal raha hai: {break_name} ({time} se). Pehle **End Break** dabayein.",
        "bot.break_started": "⏸️ {break_name} start: {time}\nWapas aane par **End Break** dabayein.",
        "bot.no_break_att": "Koi active break nahi mila. Pehle Check In karein.",
        "bot.no_break": "Koi break abhi chal nahi raha hai.",
        "bot.break_ended": "✅ {break_name} khatam: {time}\nDuration: {duration}",
        "bot.auto_end_note": "\n(Chal raha break auto-end kar diya gaya.)",
        "bot.checkout_done": "🏁 Check Out: {time}\nCheck In: {in_time}\nTotal break: {total_break}\nNet working time: *{work}*{note}",
        "bot.attendance_title": "*📊 My Attendance — {name}*",
        "bot.no_checkin_today": "Aaj abhi check-in nahi kiya.",
        "bot.today": "*Aaj ({date})*",
        "bot.check_out_pending": "abhi tak nahi",
        "bot.total_break": "• Total break: {value}",
        "bot.working_time": "• Working time: {value}",
        "bot.breaks_header": "*Breaks:*",
        "bot.break_running_short": "chal raha hai",
        "bot.break_active": "_Ek break abhi chal raha hai._",
        "bot.last_7": "*Pichhle 7 din:*",
        "bot.use_buttons": "Neeche diye gaye buttons ka istemal karein.",
        "bot.language_prompt": "Zuban chunein / Choose language:",
        "bot.language_saved": "Language set to {label}. Naya menu niche hai.",
        "bot.help": "*🤖 Merry Team — Office Attendance Bot*\n\n*Employee:*\n/start — registration / menu\n/language — English / 中文\n/attendance — apni attendance dekhein\n/cancel — registration cancel karein\n\nMenu se Check In, breaks, End Break aur Check Out karein.\n\nAdmin panel alag web app par hai (username/password se login).",
    },
    "zh": {
        # web shell
        "brand.sub": "考勤管理后台",
        "nav.dashboard": "仪表盘",
        "nav.approvals": "审批",
        "nav.employees": "员工",
        "nav.reports": "报表",
        "nav.today": "今日考勤",
        "nav.breaks": "休息记录",
        "nav.late": "迟到名单",
        "nav.monthly": "月度汇总",
        "nav.system": "系统",
        "nav.settings": "设置",
        "nav.logout": "退出登录",
        "topbar.reports": "📊 报表",
        "web.language_saved": "语言已设置为 {label}。",
        "action.remove": "移除",
        "action.restore": "恢复",
        "confirm.remove": "将 {name} 设为离职？考勤记录会保留。",
        "flash.employee_removed": "{name} 已移除（停用），考勤记录已保留。",
        "flash.employee_restored": "{name} 已恢复为在职。",
        # dashboard
        "heading.dashboard": "仪表盘",
        "card.present": "今日出勤",
        "card.present.hint": "共 {total} 名已批准员工",
        "card.absent": "今日缺勤",
        "card.absent.hint": "尚未打卡",
        "card.late": "迟到打卡",
        "card.late.hint": "截止时间 {cutoff}",
        "card.pending": "待审批",
        "card.pending.hint": "查看详情 →",
        "panel.present": "🟢 出勤 — {date}",
        "panel.absent": "🔴 缺勤 — {date}",
        "panel.active_breaks": "☕ 当前进行中的休息",
        "panel.recent": "🕒 最近动态",
        "full_report": "完整报表",
        "table.employee": "员工",
        "table.id": "编号",
        "table.check_in": "上班打卡",
        "table.check_out": "下班打卡",
        "table.status": "状态",
        "table.break": "休息类型",
        "table.start": "开始时间",
        "table.date": "日期",
        "table.work": "工作时长",
        "badge.late": "迟到",
        "badge.on_time": "准时",
        "badge.inside": "在岗",
        "empty.no_checkin": "今天还没有人打卡。",
        "empty.all_present": "所有已批准员工都已出勤。🎉",
        "empty.no_break": "当前没有进行中的休息。",
        "break.tea": "茶歇",
        "break.washroom": "洗手间休息",
        "break.lunch": "午餐休息",
        "break.other": "其他休息",
        # telegram bot
        "bot.welcome_back": "你好，{name}！👋\n请选择下面的操作。",
        "bot.pending": "你的注册正在等待管理员审批，请稍候。",
        "bot.rejected": "你的注册已被拒绝，请联系管理员。",
        "bot.welcome": "你好！欢迎使用 *Merry Team — 考勤机器人*。👋\n请输入你的**姓名**：",
        "bot.first_message": "你好！欢迎使用考勤机器人。👋\n请先注册——请输入你的**姓名**：",
        "bot.cancel_done": "注册已取消，请重新发送 /start。",
        "bot.cancel_none": "没有需要取消的操作。",
        "bot.name_invalid": "姓名需为 2–60 个字符，请重新输入：",
        "bot.name_thanks": "谢谢 {name}。请输入你的**员工编号**：",
        "bot.emp_invalid": "员工编号只能包含字母、数字、“-”或“_”（2–32 个字符），请重新输入：",
        "bot.emp_taken": "该员工编号已被注册，请换一个：",
        "bot.reg_saved": "✅ 注册已保存！\n\n姓名：{name}\n员工编号：{employee_id}\n\n请等待管理员审批。",
        "bot.admin_new_reg": "🆕 新注册：\n姓名：{name}\n员工编号：{employee_id}\nTelegram ID：{telegram_id}\n\n请在网页后台审批。",
        "bot.approved": "🎉 你的注册已通过！\n现在可以使用下方菜单打卡了。",
        "bot.not_registered": "请先发送 /start 注册。",
        "bot.not_approved": "你的账号尚未通过审批，请等待管理员批准。",
        "bot.duplicate_checkin": "你今天已在 {time} 打过上班卡。",
        "bot.duplicate_checkout": "今天已在 {time} 打过下班卡。",
        "bot.field.check_in": "上班打卡",
        "bot.field.check_out": "下班打卡",
        "bot.checkin_ok": "✅ 上班打卡：{time}\n\n如需休息请点击下面的按钮。",
        "bot.checkin_first": "请先打上班卡。",
        "bot.checked_out_break": "今天已下班，不能再开始休息。",
        "bot.break_running": "已有休息进行中：{break_name}（{time} 开始）。请先点击**结束休息**。",
        "bot.break_started": "⏸️ {break_name} 开始：{time}\n返回后请点击**结束休息**。",
        "bot.no_break_att": "未找到进行中的休息，请先打上班卡。",
        "bot.no_break": "当前没有进行中的休息。",
        "bot.break_ended": "✅ {break_name} 结束：{time}\n时长：{duration}",
        "bot.auto_end_note": "\n（进行中的休息已自动结束。）",
        "bot.checkout_done": "🏁 下班打卡：{time}\n上班打卡：{in_time}\n休息总时长：{total_break}\n实际工作时长：*{work}*{note}",
        "bot.attendance_title": "*📊 我的考勤 — {name}*",
        "bot.no_checkin_today": "今天尚未打卡。",
        "bot.today": "*今天（{date}）*",
        "bot.check_out_pending": "尚未下班",
        "bot.total_break": "• 休息总时长：{value}",
        "bot.working_time": "• 工作时长：{value}",
        "bot.breaks_header": "*休息记录：*",
        "bot.break_running_short": "进行中",
        "bot.break_active": "_当前有休息正在进行中。_",
        "bot.last_7": "*最近 7 天：*",
        "bot.use_buttons": "请使用下面的按钮。",
        "bot.language_prompt": "请选择语言 / Choose language:",
        "bot.language_saved": "语言已设置为 {label}。新菜单如下。",
        "bot.help": "*🤖 Merry Team — 考勤机器人*\n\n*员工功能：*\n/start — 注册 / 菜单\n/language — English / 中文\n/attendance — 查看我的考勤\n/cancel — 取消注册\n\n通过菜单进行上班打卡、休息、结束休息和下班打卡。\n\n管理员后台在独立的网页应用上（需用户名 / 密码登录）。",
    },
}


def normalize_lang(lang: str | None) -> str:
    """Return a supported language code, falling back to English."""
    return lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def t(key: str, lang: str | None = None, **kwargs) -> str:
    """Translate *key* into *lang*, substituting any {placeholders}."""
    code = normalize_lang(lang)
    text = TEXT[code].get(key, TEXT[DEFAULT_LANGUAGE].get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            pass
    return text


def menu_labels(lang: str | None = None) -> dict[str, str]:
    return MENU_LABELS[normalize_lang(lang)]


def menu_rows(lang: str | None = None) -> list[list[str]]:
    labels = list(menu_labels(lang).values())
    return [labels[i : i + 2] for i in range(0, len(labels), 2)]


def action_for_label(label: str) -> str | None:
    """Resolve a button text in either language to its canonical action."""
    for labels in MENU_LABELS.values():
        for action, text in labels.items():
            if text == label:
                return action
    return None


def break_name(action: str, lang: str | None = None) -> str:
    return t(f"break.{action}", lang)

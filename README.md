# Merry Team — Office Attendance Bot

Employee attendance aur break tracking. **Employee Telegram par**, **admin browser me** (username/password login se).

## Features

**Employee (Telegram)**
- Koi bhi message → naam + employee ID registration (ya `/start`)
- Admin approval ke baad 8-button menu
- Check In / Check Out
- Tea, Washroom, Lunch, Other break start + End Break
- My Attendance (aaj + pichhle 7 din)

**Admin (Web app)**
- Login / logout, multiple admin accounts
- Dashboard: present, absent, late, pending approvals, active breaks
- Naye employees ka approve / reject (Telegram par notification bhi jati hai)
- Employee list aur detail (30 din attendance + breaks)
- Reports: Today, Breaks, Late comers, Monthly
- CSV aur Excel (2 sheets) download
- Settings me late cutoff time badalna
- **English ⇄ 中文**: dashboard ke topbar me language switcher; Telegram par `/language` se menu aur messages Chinese me

Timestamps UTC me store, **Asia/Kolkata (IST)** me display.

---

## Local setup

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

`.env` me bharlein:

```
BOT_TOKEN=your_token_here
ADMIN_IDS=123456789
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-password
SECRET_KEY=long-random-string
TIMEZONE=Asia/Kolkata
DB_PATH=attendance.db
PORT=5000
```

- **BOT_TOKEN**: [@BotFather](https://t.me/BotFather) → `/newbot` → token
- **ADMIN_IDS**: [@userinfobot](https://t.me/userinfobot) se Telegram ID — inhe naye registration ki notification milti hai
- **ADMIN_USERNAME / ADMIN_PASSWORD**: web admin login. Pehli baar app chalne par ye account auto ban jata hai
- **SECRET_KEY**: koi lambi random string (login session signing ke liye)

Chalane ke liye:

```powershell
py -3 main.py
```

Phir browser me kholein: **http://localhost:5000/login**

> Agar `python` command available hai to `python main.py` bhi chalega.

### Naya admin banayein

```powershell
py -3 manage_admin.py add rahul
py -3 manage_admin.py list
py -3 manage_admin.py remove rahul
```

`add` password interactively puchhega (hash karke store hota hai).

---

## Deploy on Render

1. Code ko GitHub repo me push karein.
2. Render Dashboard → **New + → Web Service** → repo select karein.
3. `render.yaml` settings auto-fill karega. Manually:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
4. Environment variables: `BOT_TOKEN`, `ADMIN_IDS`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `SECRET_KEY`, `DATABASE_URL`.
5. **Database — do options:**
   - **Free plan (disk nahi):** [Neon](https://neon.tech) ya [Supabase](https://supabase.com) ka free PostgreSQL banaayein aur uska connection string `DATABASE_URL` me daalein:
     ```
     postgresql://user:password@host/dbname?sslmode=require
     ```
     App automatically PostgreSQL use karega aur data persist rahega.
   - **Paid Starter plan:** persistent disk `/data` mount hoti hai aur DB `DB_PATH=/data/attendance.db` me likha jayega.
   - ⚠️ `DATABASE_URL` khali aur disk nahi dono ho to app local SQLite par chalega, par **restart/deploy par data reset** ho jayega.
6. Deploy ke baad:
   - Web admin: `https://<your-service>.onrender.com/login`
   - Telegram: bot ko `/start` karke test karein

Web app aur Telegram bot **ek hi process** me chalte hain (bot background thread me polling karta hai).

---

## Files

| File | Kaam |
|---|---|
| `main.py` | entry point — web + bot dono start karta hai |
| `webapp.py` | Flask routes aur login |
| `templates/`, `static/` | admin panel UI |
| `bot.py` | Telegram bot handlers registration |
| `config.py` | `.env` se settings |
| `i18n.py` | Dashboard aur bot menu ke English/Chinese labels |
| `database.py` | SQLite / PostgreSQL schema + queries |
| `handlers/employee.py` | registration + attendance flow |
| `reports.py` | CSV / Excel report builders |
| `notifier.py` | web se Telegram par message bhejna |
| `manage_admin.py` | admin accounts CLI |
| `utils.py` | time, formatting, constants |
| `render.yaml` | Render deploy config |

## Notes

- Ek din me ek hi check-in; duplicate block hota hai.
- Ek waqt me sirf ek break active ho sakta hai.
- Check Out ke waqt koi break chal raha ho to wo auto-end ho jata hai.
- Working time = (Check Out − Check In) − saare breaks ka total.
- `late_after` setting SQLite `settings` table me save hoti hai — restart ke baad bhi rehti hai.
- Telegram par sirf employee flow hai; saara admin kaam web app par hai.

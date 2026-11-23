"""CLI to manage web admin accounts.

Examples:
    py -3 manage_admin.py add rahul
    py -3 manage_admin.py list
    py -3 manage_admin.py remove rahul
"""
from __future__ import annotations

import sys
from getpass import getpass

from werkzeug.security import generate_password_hash

import database as db


def main() -> None:
    db.init_db()
    if len(sys.argv) < 2:
        print(__doc__)
        return

    action = sys.argv[1].lower()

    if action == "add":
        if len(sys.argv) < 3:
            print("Usage: py -3 manage_admin.py add <username>")
            return
        username = sys.argv[2].strip()
        if not username:
            print("Username khali nahi ho sakta.")
            return
        if db.get_admin(username):
            print("Ye username pehle se hai.")
            return
        password = getpass("Password: ")
        confirm = getpass("Password dobara: ")
        if password != confirm:
            print("Password match nahi kiya.")
            return
        if len(password) < 6:
            print("Password kam se kam 6 characters ka hona chahiye.")
            return
        db.add_admin(username, generate_password_hash(password))
        print(f"✅ Admin '{username}' ban gaya.")

    elif action == "list":
        rows = db.list_admins()
        if not rows:
            print("Koi admin nahi hai. Pehle 'add' chalayein ya .env me ADMIN_PASSWORD set karein.")
        for row in rows:
            print(f"• {row['username']}")

    elif action == "remove":
        if len(sys.argv) < 3:
            print("Usage: py -3 manage_admin.py remove <username>")
            return
        removed = db.remove_admin(sys.argv[2].strip())
        print("Admin hata diya." if removed else "Ye admin nahi mila.")

    else:
        print(__doc__)


if __name__ == "__main__":
    main()

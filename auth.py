"""Minimal local research-prototype authentication. Do not expose to the public internet."""
import argparse
import getpass
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from report_database import DATABASE_PATH, initialize_database

ITERATIONS = 600_000

def initialize_auth():
    initialize_database()
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('victim','investigator')),
            salt TEXT NOT NULL, password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL)""")
        cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
        if "staff_id" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN staff_id TEXT")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_staff_id ON users(staff_id)")

def _valid_email(email):
    return bool(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email)) and len(email) <= 254

def create_user(name, email, password, role='victim', *, authorized=False, staff_id=None):
    initialize_auth()
    name, email = name.strip(), email.strip().lower()
    if role not in ('victim', 'investigator') or (role == 'investigator' and not authorized):
        raise ValueError('Investigator accounts cannot be publicly registered.')
    if not (2 <= len(name) <= 100) or not _valid_email(email):
        raise ValueError('Enter a valid name and email.')
    if len(password) < 12 or len(password) > 128:
        raise ValueError('Password must contain 12–128 characters.')
    if role == 'investigator':
        if not staff_id or not re.fullmatch(r'[A-Za-z0-9_-]{12,32}', staff_id.strip()):
            raise ValueError('Staff ID must be 12–32 letters, numbers, hyphens or underscores.')
        staff_id = staff_id.strip().upper()
    else:
        staff_id = None
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
    with sqlite3.connect(DATABASE_PATH) as conn:
        try:
            cur = conn.execute("""INSERT INTO users (email, full_name, role, salt, password_hash, created_at, staff_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (email, name, role, salt.hex(), digest.hex(), datetime.now(timezone.utc).isoformat(), staff_id))
        except sqlite3.IntegrityError:
            raise ValueError('Email or Staff ID already exists.') from None
        return cur.lastrowid

def authenticate(identifier, password, role="victim"):
    if role not in ("victim", "investigator"):
        return None
    initialize_auth()
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute('SELECT * FROM users WHERE email = ? COLLATE NOCASE AND role = ?', (identifier.strip(), role)).fetchone() if role == 'victim' else conn.execute('SELECT * FROM users WHERE staff_id = ? COLLATE NOCASE AND role = ?', (identifier.strip(), role)).fetchone()
    # Always perform a KDF, even for unknown users.
    salt = bytes.fromhex(row['salt']) if row else b'\x00' * 16
    expected = bytes.fromhex(row['password_hash']) if row else b'\x00' * 32
    actual = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
    if not row or not hmac.compare_digest(expected, actual):
        return None
    return {'id': row['id'], 'email': row['email'], 'name': row['full_name'], 'role': row['role'], 'staff_id': row['staff_id']}

def get_user(user_id):
    initialize_auth()
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute('SELECT id, email, full_name, role, staff_id FROM users WHERE id = ?', (user_id,)).fetchone()
    return {'id': row['id'], 'email': row['email'], 'name': row['full_name'], 'role': row['role'], 'staff_id': row['staff_id']} if row else None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create an authorized local investigator account')
    parser.add_argument('command', choices=['create-investigator', 'set-staff-id'])
    args = parser.parse_args()
    print('Create local investigator account (run only on your trusted computer).')
    if args.command == 'set-staff-id':
        initialize_auth()
        email = input('Existing investigator email: ').strip()
        staff_id = input('New Staff ID (12–32 characters): ').strip().upper()
        if not re.fullmatch(r'[A-Za-z0-9_-]{12,32}', staff_id):
            raise SystemExit('Invalid Staff ID.')
        with sqlite3.connect(DATABASE_PATH) as conn:
            try:
                cur = conn.execute("UPDATE users SET staff_id = ? WHERE email = ? COLLATE NOCASE AND role = 'investigator'", (staff_id, email))
            except sqlite3.IntegrityError:
                raise SystemExit('Staff ID already exists.') from None
            if not cur.rowcount:
                raise SystemExit('Investigator account not found.')
        print('Staff ID assigned. Existing password remains unchanged.')
        raise SystemExit(0)
    name = input('Full name: ')
    email = input('Email: ')
    staff_id = input('Staff ID (12–32 characters): ')
    password = getpass.getpass('Password (12+ characters): ')
    confirm = getpass.getpass('Confirm password: ')
    if password != confirm:
        raise SystemExit('Passwords do not match.')
    try:
        create_user(name, email, password, role='investigator', authorized=True, staff_id=staff_id)
        print('Investigator account created.')
    except ValueError as exc:
        raise SystemExit(str(exc))

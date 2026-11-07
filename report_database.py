import sqlite3
from pathlib import Path
from datetime import datetime, timezone
DATABASE_PATH = Path("local_vault") / "victim_reports.db"

def initialize_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("""CREATE TABLE IF NOT EXISTS victim_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            victim_name TEXT NOT NULL, victim_email TEXT NOT NULL,
            platform TEXT NOT NULL, scam_url TEXT,
            description TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Pending',
            submitted_at TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS report_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT, report_id INTEGER NOT NULL,
            file_path TEXT NOT NULL, original_filename TEXT NOT NULL,
            sha256 TEXT NOT NULL, captured_at TEXT NOT NULL,
            FOREIGN KEY (report_id) REFERENCES victim_reports(id))""")
        columns = {row[1] for row in conn.execute('PRAGMA table_info(victim_reports)')}
        if 'user_id' not in columns:
            conn.execute('ALTER TABLE victim_reports ADD COLUMN user_id INTEGER')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_victim_reports_user ON victim_reports(user_id)')
        conn.commit()

def save_report(victim_name, victim_email, platform, scam_url, description, user_id=None):
    initialize_database()
    if user_id is None:
        raise ValueError('Authenticated victim account is required.')
    if platform not in ('Carousell', 'Telegram'):
        raise ValueError('Unsupported platform.')
    submitted_at = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.execute("""INSERT INTO victim_reports
            (victim_name, victim_email, platform, scam_url, description, submitted_at, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (victim_name, victim_email, platform, scam_url, description, submitted_at, user_id))
        return cursor.lastrowid

def get_all_reports():
    initialize_database()
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('SELECT * FROM victim_reports ORDER BY id DESC').fetchall()
        return [dict(row) for row in rows]

def get_reports_for_user(user_id):
    initialize_database()
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('SELECT * FROM victim_reports WHERE user_id = ? ORDER BY id DESC', (user_id,)).fetchall()
        return [dict(row) for row in rows]

def save_report_evidence(report_id, evidence_data):
    initialize_database()
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("""INSERT INTO report_evidence
            (report_id, file_path, original_filename, sha256, captured_at)
            VALUES (?, ?, ?, ?, ?)""",
            (report_id, evidence_data['file_path'], evidence_data['original_filename'],
             evidence_data['sha256'], evidence_data['captured_at']))

def get_report_evidence(report_id):
    initialize_database()
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('SELECT * FROM report_evidence WHERE report_id = ? ORDER BY id DESC', (report_id,)).fetchall()
        return [dict(row) for row in rows]

def update_report_status(report_id, new_status):
    if new_status not in ('Pending', 'Under Investigation', 'Resolved'):
        raise ValueError('Invalid report status.')
    initialize_database()
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.execute('UPDATE victim_reports SET status = ? WHERE id = ?', (new_status, report_id))
        return cursor.rowcount > 0

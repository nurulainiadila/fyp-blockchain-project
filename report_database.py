
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DATABASE_PATH = Path("local_vault") / "victim_reports.db"


# ==========================================
# INITIALIZE DATABASE
# ==========================================

def initialize_database():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS victim_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                victim_name TEXT NOT NULL,
                victim_email TEXT NOT NULL,
                platform TEXT NOT NULL,
                scam_url TEXT,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                submitted_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS report_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                captured_at TEXT NOT NULL,
                FOREIGN KEY (report_id)
                    REFERENCES victim_reports(id)
            )
        """)

        conn.commit()


# ==========================================
# SAVE VICTIM REPORT
# ==========================================

def save_report(
    victim_name,
    victim_email,
    platform,
    scam_url,
    description
):
    initialize_database()

    submitted_at = datetime.now(
        timezone.utc
    ).isoformat()

    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.execute("""
            INSERT INTO victim_reports (
                victim_name,
                victim_email,
                platform,
                scam_url,
                description,
                submitted_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            victim_name,
            victim_email,
            platform,
            scam_url,
            description,
            submitted_at
        ))

        conn.commit()

        return cursor.lastrowid


# ==========================================
# GET ALL VICTIM REPORTS
# ==========================================

def get_all_reports():
    initialize_database()

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT
                id,
                victim_name,
                victim_email,
                platform,
                scam_url,
                description,
                status,
                submitted_at
            FROM victim_reports
            ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in rows]


# ==========================================
# SAVE UPLOADED EVIDENCE
# ==========================================

def save_report_evidence(report_id, evidence_data):
    initialize_database()

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("""
            INSERT INTO report_evidence (
                report_id,
                file_path,
                original_filename,
                sha256,
                captured_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            report_id,
            evidence_data["file_path"],
            evidence_data["original_filename"],
            evidence_data["sha256"],
            evidence_data["captured_at"]
        ))

        conn.commit()


# ==========================================
# GET EVIDENCE FOR A SPECIFIC REPORT
# ==========================================

def get_report_evidence(report_id):
    initialize_database()

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT
                id,
                report_id,
                file_path,
                original_filename,
                sha256,
                captured_at
            FROM report_evidence
            WHERE report_id = ?
            ORDER BY id DESC
        """, (report_id,)).fetchall()

        return [dict(row) for row in rows]


# ==========================================
# UPDATE REPORT STATUS
# ==========================================

def update_report_status(report_id, new_status):
    allowed_statuses = [
        "Pending",
        "Under Investigation",
        "Resolved"
    ]

    if new_status not in allowed_statuses:
        raise ValueError("Invalid report status.")

    initialize_database()

    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.execute("""
            UPDATE victim_reports
            SET status = ?
            WHERE id = ?
        """, (
            new_status,
            report_id
        ))

        conn.commit()

        return cursor.rowcount > 0

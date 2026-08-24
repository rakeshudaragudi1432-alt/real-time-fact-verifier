"""
SQLite Database Layer
Stores verification history records across Weather, Sports, Movies, and Science domains.
"""

import sqlite3
import os
from typing import List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "fact_verifier.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verification_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_claim TEXT NOT NULL,
            detected_domain TEXT NOT NULL,
            extracted_location TEXT,
            result TEXT NOT NULL,
            evidence TEXT,
            explanation TEXT,
            source TEXT,
            source_url TEXT,
            verification_time TEXT NOT NULL
        )
    """)
    # Create database indexes for optimized stats & history lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_domain ON verification_history(detected_domain)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_result ON verification_history(result)")

    conn.commit()
    conn.close()


def save_verification(record: Dict[str, Any]) -> int:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO verification_history 
        (user_claim, detected_domain, extracted_location, result, evidence, explanation, source, source_url, verification_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record.get("claim", ""),
        record.get("detected_domain", "UNKNOWN"),
        record.get("detected_location", None),
        record.get("result", "UNABLE TO VERIFY"),
        record.get("evidence", ""),
        record.get("explanation", ""),
        record.get("source", "System"),
        record.get("source_url", None),
        record.get("verification_time", "")
    ))
    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()
    return inserted_id


def get_history(limit: int = 100) -> List[Dict[str, Any]]:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM verification_history ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    history = [dict(row) for row in rows]
    conn.close()
    return history


def clear_history() -> bool:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM verification_history")
    conn.commit()
    conn.close()
    return True


def get_statistics() -> Dict[str, int]:
    """
    Computes live verification statistics dynamically from SQLite DB records.
    """
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM verification_history")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verification_history WHERE result LIKE '%VERIFIED%' AND result NOT LIKE '%NOT%'")
    verified = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verification_history WHERE result LIKE '%FALSE%' OR result LIKE '%NOT VERIFIED%'")
    not_verified = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verification_history WHERE result LIKE '%UNCERTAIN%' OR result LIKE '%UNABLE%'")
    uncertain = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verification_history WHERE UPPER(detected_domain) = 'WEATHER'")
    weather_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verification_history WHERE UPPER(detected_domain) = 'SPORTS'")
    sports_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verification_history WHERE UPPER(detected_domain) = 'MOVIES'")
    movies_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verification_history WHERE UPPER(detected_domain) = 'SCIENCE'")
    science_count = cursor.fetchone()[0]

    conn.close()

    return {
        "total": total,
        "verified": verified,
        "not_verified": not_verified,
        "uncertain": uncertain,
        "weather": weather_count,
        "sports": sports_count,
        "movies": movies_count,
        "science": science_count
    }


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")

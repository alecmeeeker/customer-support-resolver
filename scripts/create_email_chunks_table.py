#!/usr/bin/env python3
"""
Create email chunks table in SQLite.
Note: Vector data is stored in LanceDB, not in this table.
This script is kept for backwards compatibility but setup_all_tables.py
handles all table creation.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_connection


def main():
    """Verify email chunk tracking is set up correctly."""
    conn = get_connection()
    cur = conn.cursor()

    # Verify classified_emails has chunks_created column
    cur.execute("PRAGMA table_info(classified_emails)")
    columns = [row[1] for row in cur.fetchall()]

    if 'chunks_created' not in columns:
        print("Adding chunks_created column to classified_emails...")
        cur.execute("ALTER TABLE classified_emails ADD COLUMN chunks_created INTEGER DEFAULT 0")
        conn.commit()

    # Show statistics
    cur.execute("SELECT COUNT(*) FROM classified_emails")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM classified_emails WHERE chunks_created = 1")
    chunked = cur.fetchone()[0]

    print(f"Current statistics:")
    print(f"   Total emails: {total}")
    print(f"   Chunked emails: {chunked}")
    print(f"   Vector data stored in LanceDB (data/vectors/)")

    conn.close()


if __name__ == "__main__":
    main()

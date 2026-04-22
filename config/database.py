import sqlite3
import lancedb
import os

DATA_DIR = os.environ.get('LIMROSE_DATA_DIR',
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data'))


def get_connection():
    """Get SQLite connection with WAL mode, proper timeout, and foreign key enforcement.

    Returns a connection with sqlite3.Row factory for dict-like row access.
    Configured with 30-second busy timeout to handle concurrent access.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    db_path = os.path.join(DATA_DIR, 'limrose.db')
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_vector_db():
    """Get LanceDB connection for vector operations."""
    vector_path = os.path.join(DATA_DIR, 'vectors')
    os.makedirs(vector_path, exist_ok=True)
    return lancedb.connect(vector_path)

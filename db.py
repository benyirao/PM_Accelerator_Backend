from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().with_name("weather.db")
SCHEMA = Path(__file__).resolve().with_name("schema.sql").read_text(encoding="utf-8")

def init_db():
    """Initialize tables if they don't exist."""
    conn = connect_db()
    try:
        with conn:
            conn.executescript(SCHEMA)
    finally:
        conn.close()


def connect_db():
    """Return the connection to the DB."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

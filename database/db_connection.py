"""MySQL connection helpers for CampusConnect AI."""
import os
import re
from contextlib import contextmanager
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

load_dotenv(BASE_DIR / ".env")


def get_db_name() -> str:
    name = os.getenv("DB_NAME", "campusconnect_ai")
    if not re.fullmatch(r"[A-Za-z0-9_]{1,64}", name):
        raise ValueError("DB_NAME may only contain letters, digits and underscores.")
    return name


def _config(with_database: bool = True) -> dict:
    cfg = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "charset": "utf8mb4",
        "connection_timeout": 10,
    }
    if with_database:
        cfg["database"] = get_db_name()
    return cfg


@contextmanager
def get_connection(with_database: bool = True):
    """Yield a MySQL connection and always close it."""
    conn = mysql.connector.connect(**_config(with_database))
    try:
        yield conn
    finally:
        conn.close()


def fetch_all(sql: str, params=None) -> list:
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(sql, params or ())
            return cur.fetchall()
        finally:
            cur.close()


def fetch_one(sql: str, params=None):
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params=None) -> tuple:
    """Run a write statement. Returns (last_insert_id, affected_rows)."""
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, params or ())
            conn.commit()
            return cur.lastrowid, cur.rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()


def _schema_statements() -> list:
    lines = [
        line for line in SCHEMA_PATH.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith("--")
    ]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]


def init_db() -> None:
    """Create the database and all tables if they do not exist."""
    with get_connection(with_database=False) as conn:
        cur = conn.cursor()
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{get_db_name()}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        cur.close()
    with get_connection() as conn:
        cur = conn.cursor()
        for statement in _schema_statements():
            cur.execute(statement)
        conn.commit()
        cur.close()

"""SQLite database for Moradbakhti-KI KMU Plugin.

Customer and order storage — replaces flat-file bestellungen/.
Thread-safe, auto-creates tables, uses KMU_DATA_DIR for DB location.
"""

import json
import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional


def _get_db_path() -> Path:
    data_dir = os.environ.get("KMU_DATA_DIR", "/tmp/kmu-spike-data").strip()
    return Path(data_dir) / "kunden.db"


# ---------------------------------------------------------------------------
# Thread-local connections (SQLite requires same-thread usage)
# ---------------------------------------------------------------------------
_connections = threading.local()


def _get_conn() -> sqlite3.Connection:
    """Get or create a thread-local SQLite connection."""
    if not hasattr(_connections, "conn") or _connections.conn is None:
        db_path = _get_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _ensure_tables(conn)
        _connections.conn = conn
    return _connections.conn


def _ensure_tables(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist (idempotent)."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS kunden (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            telefon TEXT,
            erstellt_am TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS bestellungen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kunde_id INTEGER NOT NULL REFERENCES kunden(id),
            produkt TEXT NOT NULL,
            menge INTEGER NOT NULL DEFAULT 1,
            abholdatum TEXT NOT NULL,
            notiz TEXT,
            erstellt_am TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );

        CREATE INDEX IF NOT EXISTS idx_bestellungen_kunde
            ON bestellungen(kunde_id, abholdatum);
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def kunde_lookup_or_create(
    chat_id: str, name: Optional[str] = None, telefon: Optional[str] = None
) -> dict:
    """Find existing customer by chat_id, or create a new one.

    Returns dict with keys: id, chat_id, name, telefon, erstellt_am, is_new
    """
    conn = _get_conn()

    row = conn.execute(
        "SELECT id, chat_id, name, telefon, erstellt_am FROM kunden WHERE chat_id = ?",
        (chat_id,),
    ).fetchone()

    if row:
        # Existing customer — update name/telefon if provided
        updates = []
        params = []
        if name and name != row["name"]:
            updates.append("name = ?")
            params.append(name)
        if telefon and telefon != row["telefon"]:
            updates.append("telefon = ?")
            params.append(telefon)
        if updates:
            params.append(chat_id)
            conn.execute(
                f"UPDATE kunden SET {', '.join(updates)} WHERE chat_id = ?",
                params,
            )
            conn.commit()

        return {
            "id": row["id"],
            "chat_id": row["chat_id"],
            "name": name or row["name"],
            "telefon": telefon or row["telefon"],
            "erstellt_am": row["erstellt_am"],
            "is_new": False,
        }

    # New customer
    if not name:
        return {"error": "Name erforderlich für neue Kunden."}
    if not telefon:
        return {"error": "Telefonnummer erforderlich für neue Kunden."}

    cursor = conn.execute(
        "INSERT INTO kunden (chat_id, name, telefon) VALUES (?, ?, ?)",
        (chat_id, name, telefon),
    )
    conn.commit()

    return {
        "id": cursor.lastrowid,
        "chat_id": chat_id,
        "name": name,
        "telefon": telefon,
        "erstellt_am": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "is_new": True,
    }


def bestellung_einfuegen(
    kunde_id: int,
    produkt: str,
    menge: int,
    abholdatum: str,
    notiz: Optional[str] = None,
) -> dict:
    """Insert a new order. Returns the created row as dict."""
    conn = _get_conn()
    cursor = conn.execute(
        "INSERT INTO bestellungen (kunde_id, produkt, menge, abholdatum, notiz) "
        "VALUES (?, ?, ?, ?, ?)",
        (kunde_id, produkt, menge, abholdatum, notiz or None),
    )
    conn.commit()
    return {
        "id": cursor.lastrowid,
        "kunde_id": kunde_id,
        "produkt": produkt,
        "menge": menge,
        "abholdatum": abholdatum,
        "notiz": notiz or None,
    }


def meine_bestellungen(chat_id: str, abholdatum: Optional[str] = None) -> list[dict]:
    """Get all orders for a customer, optionally filtered by date."""
    conn = _get_conn()

    kunde = conn.execute(
        "SELECT id FROM kunden WHERE chat_id = ?", (chat_id,)
    ).fetchone()

    if not kunde:
        return []

    if abholdatum:
        rows = conn.execute(
            "SELECT id, produkt, menge, abholdatum, notiz, erstellt_am "
            "FROM bestellungen WHERE kunde_id = ? AND abholdatum = ? "
            "ORDER BY erstellt_am DESC",
            (kunde["id"], abholdatum),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, produkt, menge, abholdatum, notiz, erstellt_am "
            "FROM bestellungen WHERE kunde_id = ? "
            "ORDER BY erstellt_am DESC LIMIT 20",
            (kunde["id"],),
        ).fetchall()

    return [dict(r) for r in rows]


def tagesbestellungen(abholdatum: str) -> list[dict]:
    """Get ALL orders for a specific date (for the business owner)."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT b.id, b.produkt, b.menge, b.abholdatum, b.notiz, b.erstellt_am, "
        "k.name as kunden_name, k.telefon "
        "FROM bestellungen b JOIN kunden k ON b.kunde_id = k.id "
        "WHERE b.abholdatum = ? "
        "ORDER BY b.erstellt_am",
        (abholdatum,),
    ).fetchall()
    return [dict(r) for r in rows]

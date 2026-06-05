"""Tool handlers for Moradbakhti-KI KMU Plugin — what runs when called."""

import json
import os
from datetime import date, datetime
from pathlib import Path

from . import db
from .hooks import _get_customer_id


def _get_data_dir() -> str:
    """Resolve KMU_DATA_DIR with fallback."""
    env = os.environ.get("KMU_DATA_DIR", "").strip()
    if env:
        return env
    return "/tmp/kmu-spike-data"


def _validate_date(datum_str: str) -> bool:
    """Check YYYY-MM-DD format and that date is not in the past."""
    try:
        dt = datetime.strptime(datum_str, "%Y-%m-%d").date()
        return dt >= date.today()
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# bestellung_aufnehmen — SQLite-backed
# ---------------------------------------------------------------------------


def bestellung_aufnehmen(args: dict, **kwargs) -> str:
    """Save a customer order to the SQLite database.

    Automatically identifies the customer via their chat_id (Telegram)
    or session_id (CLI fallback). New customers are created on first order.
    """
    del kwargs

    kunden_name = (args.get("kunden_name") or "").strip()
    produkt = (args.get("produkt") or "").strip()
    datum_str = (args.get("datum") or "").strip()
    menge = args.get("menge") or 1
    telefon = (args.get("telefon") or "").strip()
    notiz = (args.get("notiz") or "").strip()
    abholzeit = (args.get("abholzeit") or "").strip() or None

    customer_id = _get_customer_id()
    if not customer_id:
        # CLI fallback: use KMU_TEST_CUSTOMER_ID or session-based default
        import os as _os
        customer_id = _os.environ.get("KMU_TEST_CUSTOMER_ID")
        if not customer_id:
            data_dir = _get_data_dir()
            customer_id = f"cli:{data_dir}"
    if not customer_id:
        return json.dumps({
            "success": False,
            "error": "Keine Kunden-ID verfügbar (Session-Fehler).",
        })

    # Validation
    errors = []
    if not produkt:
        errors.append("produkt fehlt")
    if not datum_str:
        errors.append("datum fehlt")
    elif not _validate_date(datum_str):
        errors.append(
            f"Ungültiges Datum '{datum_str}'. Format: YYYY-MM-DD, "
            "Datum darf nicht in der Vergangenheit liegen."
        )
    try:
        menge = int(menge)
        if menge < 1:
            errors.append("menge muss mindestens 1 sein")
    except (TypeError, ValueError):
        errors.append("menge muss eine Zahl sein")

    if errors:
        return json.dumps({"success": False, "errors": errors})

    # Lookup or create customer
    kunde = db.kunde_lookup_or_create(customer_id, kunden_name or None, telefon or None)
    if "error" in kunde:
        # New customer missing required fields
        return json.dumps({
            "success": False,
            "error": kunde["error"],
            "missing_fields": (
                ["kunden_name"] if not kunden_name else []
            ) + (["telefon"] if not telefon else []),
        })

    # Insert order
    order = db.bestellung_einfuegen(kunde["id"], produkt, menge, datum_str, abholzeit, notiz or None)

    return json.dumps({
        "success": True,
        "bestellung": {
            "id": order["id"],
            "kunden_name": kunde["name"],
            "produkt": produkt,
            "menge": menge,
            "datum": datum_str,
            "abholzeit": abholzeit,
            "telefon": kunde["telefon"],
            "notiz": notiz or None,
        },
        "kunde": {
            "name": kunde["name"],
            "is_new": kunde["is_new"],
            "telefon": kunde["telefon"],
        },
    })


# ---------------------------------------------------------------------------
# meine_bestellungen — Kunde sieht nur seine eigenen
# ---------------------------------------------------------------------------


def meine_bestellungen(args: dict, **kwargs) -> str:
    """Show the current customer their own orders.

    Automatically scoped to the caller's chat_id — cannot see other
    customers' data. Optionally filtered by abholdatum.
    """
    del kwargs

    customer_id = _get_customer_id()
    logger.debug("[moradbakhti-kmu] meine_bestellungen: customer_id=%r", customer_id)
    if not customer_id:
        import os as _os
        customer_id = _os.environ.get("KMU_TEST_CUSTOMER_ID")
        if not customer_id:
            customer_id = f"cli:{_get_data_dir()}"
    if not customer_id:
        return json.dumps({
            "success": False,
            "error": "Keine Kunden-ID verfügbar.",
        })

    abholdatum = (args.get("abholdatum") or "").strip() or None

    orders = db.meine_bestellungen(customer_id, abholdatum)
    if not orders:
        msg = (
            f"Keine Bestellungen für den {abholdatum} gefunden."
            if abholdatum
            else "Sie haben noch keine Bestellungen."
        )
        return json.dumps({"success": True, "bestellungen": [], "hinweis": msg})

    return json.dumps({
        "success": True,
        "anzahl": len(orders),
        "bestellungen": [
            {
                "id": o["id"],
                "produkt": o["produkt"],
                "menge": o["menge"],
                "abholdatum": o["abholdatum"],
                "notiz": o.get("notiz"),
                "erstellt_am": o["erstellt_am"],
            }
            for o in orders
        ],
    })


# ---------------------------------------------------------------------------
# preise_abfragen — unchanged (reads produkte.md)
# ---------------------------------------------------------------------------


def preise_abfragen(args: dict, **kwargs) -> str:
    """Read the price list from $KMU_DATA_DIR/produkte.md."""
    del kwargs

    data_dir = Path(_get_data_dir())
    produkty_file = data_dir / "produkte.md"

    if not produkty_file.exists():
        return json.dumps({
            "success": False,
            "error": f"Preisliste nicht gefunden: {produkty_file}",
        })

    try:
        content = produkty_file.read_text(encoding="utf-8")
    except OSError as e:
        return json.dumps({
            "success": False,
            "error": f"Kann Preisliste nicht lesen: {e}",
        })

    filter_term = (args.get("produkt_filter") or "").strip().lower()

    if not filter_term:
        return json.dumps({
            "success": True,
            "file": str(produkty_file),
            "preisliste": content,
        })

    lines = content.split("\n")
    filtered = []
    in_matching_section = False
    for line in lines:
        line_lower = line.lower()
        if line.startswith("## "):
            in_matching_section = filter_term in line_lower
            if in_matching_section:
                filtered.append(line)
            continue
        if in_matching_section or filter_term in line_lower:
            if line.strip():
                filtered.append(line)

    if not filtered:
        return json.dumps({
            "success": True,
            "file": str(produkty_file),
            "preisliste": f"Keine Produkte für '{args.get('produkt_filter')}' gefunden.",
        })

    return json.dumps({
        "success": True,
        "file": str(produkty_file),
        "preisliste": "\n".join(filtered),
    })


# ---------------------------------------------------------------------------
# tagesbestellungen — Chef-Tool (auth-gated)
# ---------------------------------------------------------------------------


def tagesbestellungen(args: dict, **kwargs) -> str:
    """Show ALL orders for a date — owner only.

    Access controlled via platform_toolsets: only the Chef-Bot has
    the moradbakhti_kmu_chef toolset with this tool.
    """
    del kwargs

    # Date logic
    from datetime import date as _date
    abholdatum = (args.get("abholdatum") or "").strip()
    if not abholdatum:
        abholdatum = _date.today().strftime("%Y-%m-%d")

    orders = db.tagesbestellungen(abholdatum)

    if not orders:
        return json.dumps({
            "success": True,
            "abholdatum": abholdatum,
            "anzahl": 0,
            "bestellungen": [],
            "hinweis": f"Keine Bestellungen für den {abholdatum}.",
        })

    return json.dumps({
        "success": True,
        "abholdatum": abholdatum,
        "anzahl": len(orders),
        "bestellungen": [
            {
                "kunden_name": o["kunden_name"],
                "produkt": o["produkt"],
                "menge": o["menge"],
                "telefon": o["telefon"],
                "abholzeit": o.get("abholzeit"),
                "uhrzeit": o["erstellt_am"],
                "notiz": o.get("notiz"),
            }
            for o in orders
        ],
    })


# ---------------------------------------------------------------------------
# bestellung_aendern — Chef-Tool
# ---------------------------------------------------------------------------


def bestellung_aendern(args: dict, **kwargs) -> str:
    """Update an existing order — owner only."""
    del kwargs

    bestell_id = args.get("bestell_id")
    feld = (args.get("feld") or "").strip().lower()
    wert = (args.get("wert") or "").strip()

    if not bestell_id:
        return json.dumps({"success": False, "error": "bestell_id fehlt"})
    if not feld:
        return json.dumps({"success": False, "error": "feld fehlt"})

    try:
        bestell_id = int(bestell_id)
    except (TypeError, ValueError):
        return json.dumps({"success": False, "error": "bestell_id muss eine Zahl sein"})

    result = db.bestellung_aendern(bestell_id, feld, wert)
    return json.dumps(result)

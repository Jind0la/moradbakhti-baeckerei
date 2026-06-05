"""Moradbakhti-KI KMU Plugin — registration."""

import logging
from pathlib import Path

from . import schemas, tools, hooks

logger = logging.getLogger(__name__)


def register(ctx):
    """Wire schemas to handlers, register hooks, and bundle skills."""

    logger.info("[moradbakhti-kmu] register() called")

    # --- Kunden-Tools (Toolset: moradbakhti_kmu_kunden) ---
    ctx.register_tool(
        name="bestellung_aufnehmen",
        toolset="moradbakhti_kmu_kunden",
        schema=schemas.BESTELLUNG_AUFNEHMEN,
        handler=tools.bestellung_aufnehmen,
        description=(
            "Kundenbestellung in SQLite-Datenbank speichern. "
            "Automatische Kundenerkennung per Chat-ID. "
            "Stammkunden: Name+Telefon optional. Neukunden: beides erforderlich. "
            "Erwartet mindestens: produkt, datum (YYYY-MM-DD). "
            "Optional: kunden_name, menge, telefon, notiz."
        ),
    )

    ctx.register_tool(
        name="meine_bestellungen",
        toolset="moradbakhti_kmu_kunden",
        schema=schemas.MEINE_BESTELLUNGEN,
        handler=tools.meine_bestellungen,
        description=(
            "EIGENE Bestellungen des aktuellen Kunden anzeigen. "
            "Automatisch auf die Chat-ID beschränkt — NIE andere Kunden. "
            "Optional nach Abholdatum filtern."
        ),
    )

    ctx.register_tool(
        name="preise_abfragen",
        toolset="moradbakhti_kmu_kunden",
        schema=schemas.PREISE_ABFRAGEN,
        handler=tools.preise_abfragen,
        description=(
            "Preisliste aus $KMU_DATA_DIR/produkte.md lesen. "
            "Immer VOR Preisauskünften aufrufen. NIE Preise aus dem Gedächtnis. "
            "Optional nach Produktnamen filtern."
        ),
    )

    # --- Chef-Tools (Toolset: moradbakhti_kmu_chef) ---
    ctx.register_tool(
        name="tagesbestellungen",
        toolset="moradbakhti_kmu_chef",
        schema=schemas.TAGESBESTELLUNGEN,
        handler=tools.tagesbestellungen,
        description=(
            "ALLE Bestellungen für ein Datum — NUR für den Inhaber. "
            "Zeigt Name, Produkt, Menge, Telefon und Uhrzeit aller Kunden."
        ),
    )

    # --- Hooks (5-Layer Defense — aktiv für beide Profile) ---
    ctx.register_hook("pre_tool_call", hooks.on_pre_tool_call)
    ctx.register_hook("pre_gateway_dispatch", hooks.on_pre_gateway_dispatch)
    ctx.register_hook("pre_llm_call", hooks.on_pre_llm_call)
    ctx.register_hook("post_tool_call", hooks.on_post_tool_call)
    ctx.register_hook("transform_llm_output", hooks.on_transform_llm_output)

    # --- Bundled Skills ---
    _plugin_dir = Path(__file__).parent
    _skills_dir = _plugin_dir / "skills"
    if _skills_dir.is_dir():
        for child in sorted(_skills_dir.iterdir()):
            skill_md = child / "SKILL.md"
            if child.is_dir() and skill_md.exists():
                ctx.register_skill(child.name, skill_md)
                logger.info("[moradbakhti-kmu] Registered skill: %s", child.name)

    logger.info(
        "[moradbakhti-kmu] v2.2.0 loaded — "
        "4 tools (2 toolsets), 5 hooks, 1 skill"
    )

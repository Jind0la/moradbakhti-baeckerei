"""Tool schemas for Moradbakhti-KI KMU Plugin — what the LLM sees."""

BESTELLUNG_AUFNEHMEN = {
    "name": "bestellung_aufnehmen",
    "description": (
        "Nimmt eine Kundenbestellung entgegen und speichert sie in der "
        "Kundendatenbank. Automatische Kundenerkennung: Stammkunden werden "
        "anhand ihrer Chat-ID wiedererkannt, Name und Telefon sind dann "
        "optional. Neue Kunden brauchen Name + Telefon. "
        "Verwende dieses Tool, wenn ein Kunde etwas bestellen möchte. "
        "Frage VORHER mindestens produkt und datum ab. "
        "NIE Preise nennen, die nicht in der Preisliste stehen."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "kunden_name": {
                "type": "string",
                "description": (
                    "Name des Kunden. Bei Stammkunden optional (wird aus DB ergänzt). "
                    "Bei Neukunden erforderlich."
                ),
            },
            "produkt": {
                "type": "string",
                "description": "Gewünschtes Produkt (z.B. '10 Brötchen', 'Dinkelvollkornbrot')",
            },
            "datum": {
                "type": "string",
                "description": "Abholdatum im Format YYYY-MM-DD",
            },
            "menge": {
                "type": "integer",
                "description": "Anzahl (Standard: 1)",
            },
            "telefon": {
                "type": "string",
                "description": (
                    "Telefonnummer. Bei Stammkunden optional, bei Neukunden erforderlich."
                ),
            },
            "notiz": {
                "type": "string",
                "description": "Optionale Zusatznotiz (Allergene, Sonderwünsche)",
            },
            "abholzeit": {
                "type": "string",
                "description": (
                    "Optionale Abholzeit (z.B. '10:00', 'vormittags', 'nach 14 Uhr'). "
                    "NUR erfragen wenn der Kunde eine bestimmte Uhrzeit nennt."
                ),
            },
        },
        "required": ["produkt", "datum"],
    },
}

MEINE_BESTELLUNGEN = {
    "name": "meine_bestellungen",
    "description": (
        "Zeigt dem Kunden SEINE EIGENEN Bestellungen an — NUR die des aktuellen "
        "Chats. Kann NIE Bestellungen anderer Kunden sehen. "
        "Verwende dieses Tool wenn ein Kunde fragt 'Was habe ich bestellt?', "
        "'Was liegt für mich bereit?' oder 'Meine Bestellung für Samstag?'."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "abholdatum": {
                "type": "string",
                "description": (
                    "Optional. Datum im Format YYYY-MM-DD um nur Bestellungen "
                    "für einen bestimmten Tag zu sehen. Leer lassen für alle "
                    "eigenen Bestellungen."
                ),
            },
        },
        "required": [],
    },
}

PREISE_ABFRAGEN = {
    "name": "preise_abfragen",
    "description": (
        "Liest die Produkt- und Preisliste aus $KMU_DATA_DIR/produkte.md. "
        "Verwende dieses Tool IMMER wenn ein Kunde nach Preisen, Produkten oder "
        "dem Sortiment fragt — BEVOR du eine Antwort gibst. "
        "NENNE NIE Preise aus dem Gedächtnis. NUR was in der Datei steht. "
        "Wenn ein Produkt nicht in der Datei steht, sage ehrlich: "
        "'Das haben wir nicht im Sortiment.' "
        "Optional kannst du nach einem bestimmten Produktnamen filtern."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "produkt_filter": {
                "type": "string",
                "description": (
                    "Optionaler Suchbegriff um nur bestimmte Produkte zu finden "
                    "(z.B. 'Brot', 'Brötchen', 'Kuchen'). Leer lassen für die "
                    "komplette Preisliste."
                ),
            },
        },
        "required": [],
    },
}

TAGESBESTELLUNGEN = {
    "name": "tagesbestellungen",
    "description": (
        "ALLE Bestellungen für ein bestimmtes Abholdatum anzeigen — NUR für "
        "den Geschäftsinhaber. Zeigt Name, Produkt, Menge, Telefon und Uhrzeit. "
        "Verwende dieses Tool wenn der Chef fragt: 'Was liegt heute an?', "
        "'Bestellungen für Samstag?' oder 'Tagesübersicht für den 7.6.'."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "abholdatum": {
                "type": "string",
                "description": (
                    "Abholdatum im Format YYYY-MM-DD. Wenn leer: heute."
                ),
            },
        },
        "required": [],
    },
}

BESTELLUNG_AENDERN = {
    "name": "bestellung_aendern",
    "description": (
        "Eine bestehende Bestellung ändern — NUR für den Inhaber. "
        "Du brauchst die Bestell-ID (aus der Tagesübersicht). "
        "Änderbare Felder: produkt, menge, abholdatum, abholzeit, notiz. "
        "Verwende dieses Tool wenn der Chef sagt: 'Ändere Bestellung Nr. 3 auf 10 Brötchen' "
        "oder 'Schieb Bestellung 5 auf 14 Uhr'."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "bestell_id": {
                "type": "integer",
                "description": "ID der Bestellung (aus tagesbestellungen)",
            },
            "feld": {
                "type": "string",
                "enum": ["produkt", "menge", "abholdatum", "abholzeit", "notiz"],
                "description": "Welches Feld soll geändert werden?",
            },
            "wert": {
                "type": "string",
                "description": "Neuer Wert für das Feld",
            },
        },
        "required": ["bestell_id", "feld", "wert"],
    },
}

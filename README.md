# Moradbakhti-KI Bäckerei Agent

Kompletter KI-Assistent für Bäckereien — Kunden-Bot + Chef-Bot.  
**Moradbakhti-KI — Null-Setup, Managed Hosting, DSGVO-konform.**

---

## 🚀 Installation (2 Minuten)

```bash
git clone https://github.com/Jind0la/moradbakhti-baeckerei.git
cd moradbakhti-baeckerei
./install.sh schmidt    # → Profile: schmidt-kunden + schmidt-chef
```

Dann `.env` ausfüllen, SOUL.md anpassen, Gateway starten. Fertig.

---

## 📦 Was installiert wird

| Profil | Für wen | Kann |
|---|---|---|
| `[name]-kunden` | Kunden (Telegram-Bot) | Bestellungen, Preise, eigene Bestellungen einsehen |
| `[name]-chef` | Inhaber (Telegram-Bot) | Tagesübersicht, alle Bestellungen |

**Beide teilen sich EIN Datenverzeichnis** (`$KMU_DATA_DIR`).

---

## 🔒 Sicherheit

- **Kunde kann NUR eigene Daten sehen** (Chat-ID-Isolation)
- **Chef sieht alle Bestellungen** (separater Bot, anderer Token)
- **Prompt-Injection wird aktiv geblockt** (5-Layer-Defense)
- **Keine Admin-Tools im Kunden-Bot** (platform_toolsets-Hardlimit)

---

## 🛠 Updates

```bash
cd moradbakhti-baeckerei
git pull
./install.sh schmidt    # Überschreibt Skills + Config, nie Kundendaten
```

---

## 📋 Voraussetzungen

- Hermes Agent >= 0.15.0
- DeepSeek API-Key (https://platform.deepseek.com/api_keys)
- Zwei Telegram-Bot-Tokens (@BotFather)
- Ein Verzeichnis für Kundendaten (z.B. `/opt/baeckerei-data`)

#!/bin/bash
# Moradbakhti-KI Bäckerei Agent — Installation
# Klone dieses Repo und führe dieses Skript aus.
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🥐 Moradbakhti-KI Bäckerei Agent"
echo "================================="
echo ""

# Plugin kopieren (keine Symlinks — Hermes Distribution akzeptiert nur echte Dateien)
echo "📦 Plugin kopieren..."
for profile in kunden chef; do
    rm -rf "$REPO_DIR/$profile/plugins"
    mkdir -p "$REPO_DIR/$profile/plugins"
    cp -r "$REPO_DIR/plugin/moradbakhti-kmu" "$REPO_DIR/$profile/plugins/"
    find "$REPO_DIR/$profile/plugins" -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
done

# Profile installieren
echo ""
echo "👤 Kunden-Bot installieren..."
hermes profile install "$REPO_DIR/kunden" --name "${1:-baeckerei}-kunden" --alias -y

echo ""
echo "👨‍🍳 Chef-Bot installieren..."
hermes profile install "$REPO_DIR/chef" --name "${1:-baeckerei}-chef" --alias -y

echo ""
echo "✅ Fertig!"
echo ""
echo "Nächste Schritte:"
echo "  1. .env.EXAMPLE → .env kopieren und API-Keys eintragen:"
echo "     cp ~/.hermes/profiles/${1:-baeckerei}-kunden/.env.EXAMPLE ~/.hermes/profiles/${1:-baeckerei}-kunden/.env"
echo "     cp ~/.hermes/profiles/${1:-baeckerei}-chef/.env.EXAMPLE ~/.hermes/profiles/${1:-baeckerei}-chef/.env"
echo ""
echo "  2. SOUL.md anpassen (Name, Adresse, Öffnungszeiten)"
echo ""
echo "  3. Preisliste anlegen unter \$KMU_DATA_DIR/produkte.md"
echo ""
echo "  4. Gateway starten:"
echo "     ${1:-baeckerei}-kunden gateway start"
echo "     ${1:-baeckerei}-chef gateway start"

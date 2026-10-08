#!/usr/bin/env bash
# =============================================================================
# install.sh - התקנת תפריט ההתחלה של NEXY
# =============================================================================
set -e

DEST="/usr/lib/nexy/startmenu"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> מתקין תלויות Python..."
pip3 install --quiet pygobject 2>/dev/null || true

echo "==> מעתיק קבצים ל-$DEST..."
sudo mkdir -p "$DEST"
sudo cp "$SCRIPT_DIR"/*.py "$DEST/"
sudo cp "$SCRIPT_DIR"/style.css "$DEST/"
sudo chmod +x "$DEST/main.py"

echo "==> מתקין קובץ .desktop..."
sudo cp "$SCRIPT_DIR/nexy-startmenu.desktop" \
    /usr/share/applications/nexy-startmenu.desktop

echo "==> מגדיר הפעלה אוטומטית..."
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/nexy-startmenu.desktop << 'EOF'
[Desktop Entry]
Name=NEXY Start Menu Daemon
Exec=python3 /usr/lib/nexy/startmenu/main.py
Type=Application
Hidden=false
X-GNOME-Autostart-enabled=true
EOF

echo ""
echo "==> קישור למקש Super (X11)..."
echo "    הוסף לקובץ ~/.config/nexy/keybindings.conf:"
echo "    super = python3 /usr/lib/nexy/startmenu/main.py"
echo ""
echo "    לסביבת OpenBox — הוסף ל-~/.config/openbox/rc.xml:"
echo '    <keybind key="Super_L">'
echo '      <action name="Execute">'
echo '        <command>python3 /usr/lib/nexy/startmenu/main.py</command>'
echo '      </action>'
echo '    </keybind>'
echo ""
echo "    לסביבת GNOME — הוסף קיצור מקלדת מותאם ב-gsettings:"
echo '    gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings \
      "['"'"'/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/nexy/'"'"']"'
echo '    gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:\
      /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/nexy/ \
      name "NEXY Start Menu"'
echo '    gsettings set .../command "python3 /usr/lib/nexy/startmenu/main.py"'
echo '    gsettings set .../binding "Super_L"'
echo ""
echo "✓ ההתקנה הושלמה!"
echo "  הפעלה ידנית: python3 /usr/lib/nexy/startmenu/main.py"

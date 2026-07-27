#!/usr/bin/env bash
# Automatic Installation Script for Click to Claude
# Workspace: /home/ari_prezo/Bureau/Click

set -e

SCRIPT_DIR="/home/ari_prezo/Bureau/Click"
SCRIPT_PATH="$SCRIPT_DIR/click_claude.py"

echo "=========================================================="
echo "🚀 Installing Click to Claude (Pins & Context Engine)"
echo "=========================================================="

# 1. Make script executable
chmod +x "$SCRIPT_PATH" 2>/dev/null || true

# 2. Install required packages
echo "📦 Installing system dependencies (xclip, xdotool, scrot, tesseract-ocr, python3-tk, python3-pil)..."
sudo apt update && sudo apt install -y xclip xdotool scrot tesseract-ocr libnotify-bin python3-tk python3-pil python3-pil.imagetk

# 3. Install .desktop shortcut
echo "🖥️ Registering desktop application shortcut..."
mkdir -p ~/.local/share/applications
cp "$SCRIPT_DIR/click_claude.desktop" ~/.local/share/applications/
chmod +x ~/.local/share/applications/click_claude.desktop 2>/dev/null || true

# 4. Configure GNOME keyboard shortcut via Python
echo "⌨️ Configuring global keyboard shortcut (Super + C)..."
python3 - << 'EOF'
import subprocess
import os

try:
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
    if "GNOME" in desktop or "Ubuntu" in desktop or "Pop" in desktop:
        key_path = "org.gnome.settings-daemon.plugins.media-keys"
        custom_path = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom-click-claude/"
        
        res = subprocess.run(["gsettings", "get", key_path, "custom-keybindings"], capture_output=True, text=True)
        current = res.stdout.strip()
        
        if custom_path not in current:
            if current == "@as []" or current == "[]" or not current:
                new_val = f"['{custom_path}']"
            else:
                clean_current = current.rstrip("]").strip()
                new_val = f"{clean_current}, '{custom_path}']"
            subprocess.run(["gsettings", "set", key_path, "custom-keybindings", new_val], check=False)
        
        binding_base = f"{key_path}.custom-keybinding:{custom_path}"
        script_cmd = f"python3 /home/ari_prezo/Bureau/Click/click_claude.py"
        
        subprocess.run(["gsettings", "set", binding_base, "name", "Click to Claude"], check=False)
        subprocess.run(["gsettings", "set", binding_base, "command", script_cmd], check=False)
        subprocess.run(["gsettings", "set", binding_base, "binding", "<Super>c"], check=False)
        print("✅ Shortcut 'Super + C' (Windows + C) successfully configured!")
except Exception as e:
    print(f"Shortcut notice: Manual setup available in Settings -> Keyboard ({e})")
EOF

echo "=========================================================="
echo "🎉 Installation completed!"
echo ""
echo "💡 How to use:"
echo "1. Press 'Super + C' (Windows Key + C)"
echo "2. Select any region on your screen"
echo "3. Add numbered pins (1, 2, 3...) or redact sensitive data"
echo "4. Click '🚀 SEND TO CLAUDE': Claude mini-window opens and auto-pastes!"
echo "=========================================================="

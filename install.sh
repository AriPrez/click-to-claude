#!/usr/bin/env bash
# Script d'installation automatique pour Click to Claude
# Workspace: /home/ari_prezo/Bureau/Click

set -e

SCRIPT_DIR="/home/ari_prezo/Bureau/Click"
SCRIPT_PATH="$SCRIPT_DIR/click_claude.py"

echo "=========================================================="
echo "🚀 Installation de Click to Claude (avec Barre d'Annotation)"
echo "=========================================================="

# 1. Rendre le script exécutable
chmod +x "$SCRIPT_PATH" 2>/dev/null || true

# 2. Installation des paquets requis
echo "📦 Installation des dépendances système (xclip, xdotool, scrot, tesseract-ocr, python3-tk, python3-pil)..."
sudo apt update && sudo apt install -y xclip xdotool scrot tesseract-ocr libnotify-bin python3-tk python3-pil python3-pil.imagetk

# 3. Installation du fichier .desktop
echo "🖥️ Intégration du raccourci d'application..."
mkdir -p ~/.local/share/applications
cp "$SCRIPT_DIR/click_claude.desktop" ~/.local/share/applications/
chmod +x ~/.local/share/applications/click_claude.desktop 2>/dev/null || true

# 4. Configuration du raccourci sous GNOME via Python
echo "⌨️ Configuration automatique du raccourci clavier..."
python3 - << 'EOF'
import subprocess
import os

try:
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
    if "GNOME" in desktop or "Ubuntu" in desktop or "Pop" in desktop:
        key_path = "org.gnome.settings-daemon.plugins.media-keys"
        custom_path = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom-click-claude/"
        
        # Récupérer la liste des raccourcis
        res = subprocess.run(["gsettings", "get", key_path, "custom-keybindings"], capture_output=True, text=True)
        current = res.stdout.strip()
        
        if custom_path not in current:
            if current == "@as []" or current == "[]" or not current:
                new_val = f"['{custom_path}']"
            else:
                # Retirer le crochet fermant et ajouter notre raccourci
                clean_current = current.rstrip("]").strip()
                new_val = f"{clean_current}, '{custom_path}']"
            subprocess.run(["gsettings", "set", key_path, "custom-keybindings", new_val], check=False)
        
        binding_base = f"{key_path}.custom-keybinding:{custom_path}"
        script_cmd = f"python3 /home/ari_prezo/Bureau/Click/click_claude.py"
        
        subprocess.run(["gsettings", "set", binding_base, "name", "Click to Claude"], check=False)
        subprocess.run(["gsettings", "set", binding_base, "command", script_cmd], check=False)
        subprocess.run(["gsettings", "set", binding_base, "binding", "<Super>c"], check=False)
        print("✅ Raccourci 'Super + C' (Windows + C) configuré avec succès !")
except Exception as e:
    print(f"Information raccourci : Configuration manuelle possible dans les Paramètres -> Raccourcis ({e})")
EOF

echo "=========================================================="
echo "🎉 Installation terminée !"
echo ""
echo "💡 Comment l'utiliser :"
echo "1. Appuyez sur 'Super + C' (Touche Windows + C)"
echo "2. Sélectionnez une zone avec votre souris"
echo "3. La fenêtre d'annotation s'ouvre : Masquez les infos sensibles ou surlignez du texte"
echo "4. Cliquez sur '🚀 ENVOYER À CLAUDE' : Le mini-onglet s'ouvre et colle (Ctrl+V) l'image !"
echo "=========================================================="

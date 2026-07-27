#!/usr/bin/env bash
# Installer for Ubuntu, Debian, Pop!_OS, and derivatives.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/click_claude.py"
EDITOR_PATH="$SCRIPT_DIR/editor_ui.py"
INSTALL_DIR="$HOME/.local/lib/click-to-claude"
INSTALL_MAIN="$INSTALL_DIR/click_claude.py"
INSTALL_BIN="$HOME/.local/bin/click-to-claude"
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_PATH="$DESKTOP_DIR/click-to-claude.desktop"
LEGACY_DESKTOP_PATH="$DESKTOP_DIR/click_claude.desktop"

if [[ ! -f "$SCRIPT_PATH" || ! -f "$EDITOR_PATH" ]]; then
    echo "Error: click_claude.py or editor_ui.py is missing." >&2
    exit 1
fi

if ! command -v apt-get >/dev/null 2>&1; then
    echo "This installer currently supports apt-based distributions only." >&2
    echo "See README.md for the required packages and manual installation." >&2
    exit 1
fi

echo "Installing Click to Claude..."

base_packages=(
    gnome-screenshot
    libnotify-bin
    maim
    python3-pil
    python3-pil.imagetk
    python3-tk
    scrot
    x11-utils
    xclip
    xdotool
)

sudo apt-get update
sudo apt-get install -y "${base_packages[@]}"

# These packages enable wlroots-based Wayland capture/clipboard support. Some
# older apt repositories do not provide all of them, so keep X11 install usable.
sudo apt-get install -y grim slurp wl-clipboard || {
    echo "Wayland helper packages were unavailable; X11 support is still installed."
}

install -Dm755 "$SCRIPT_PATH" "$INSTALL_MAIN"
install -Dm644 "$EDITOR_PATH" "$INSTALL_DIR/editor_ui.py"
mkdir -p "$(dirname -- "$INSTALL_BIN")"
{
    printf '#!/usr/bin/env bash\n'
    printf 'exec python3 %q "$@"\n' "$INSTALL_MAIN"
} > "$INSTALL_BIN"
chmod 755 "$INSTALL_BIN"
mkdir -p "$DESKTOP_DIR"
sed "s|^Exec=.*|Exec=$INSTALL_BIN|" \
    "$SCRIPT_DIR/click_claude.desktop" > "$DESKTOP_PATH"
chmod 644 "$DESKTOP_PATH"
rm -f -- "$LEGACY_DESKTOP_PATH"

if command -v desktop-file-validate >/dev/null 2>&1; then
    desktop-file-validate "$DESKTOP_PATH"
fi

echo "Configuring the GNOME shortcut Super+C when supported..."
python3 - "$INSTALL_BIN" <<'PY'
import ast
import os
import subprocess
import sys

command = sys.argv[1]
desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
if not any(name in desktop.upper() for name in ("GNOME", "UBUNTU", "POP")):
    print("Non-GNOME desktop detected; configure the global shortcut manually.")
    raise SystemExit(0)

schema = "org.gnome.settings-daemon.plugins.media-keys"
custom_path = (
    "/org/gnome/settings-daemon/plugins/media-keys/"
    "custom-keybindings/custom-click-to-claude/"
)
legacy_path = (
    "/org/gnome/settings-daemon/plugins/media-keys/"
    "custom-keybindings/custom-click-claude/"
)

result = subprocess.run(
    ["gsettings", "get", schema, "custom-keybindings"],
    capture_output=True,
    text=True,
    check=False,
)
raw_value = result.stdout.strip()
if raw_value.startswith("@as "):
    raw_value = raw_value[4:]
try:
    current = ast.literal_eval(raw_value) if raw_value else []
except (SyntaxError, ValueError):
    current = []
current = [path for path in current if path != legacy_path]
if custom_path not in current:
    current.append(custom_path)

subprocess.run(
    ["gsettings", "set", schema, "custom-keybindings", repr(current)],
    check=True,
)
binding_schema = f"{schema}.custom-keybinding:{custom_path}"
for key, value in (
    ("name", "Click to Claude"),
    ("command", command),
    ("binding", "<Super>c"),
):
    subprocess.run(
        ["gsettings", "set", binding_schema, key, value],
        check=True,
    )
print("GNOME shortcut Super+C configured.")
PY

echo
echo "Installation complete."
echo "Run: $INSTALL_BIN"
echo "Diagnostics: $INSTALL_BIN --diagnose"
echo "If Super+C is already in use, change it in Settings > Keyboard > Shortcuts."

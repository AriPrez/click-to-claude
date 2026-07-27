#!/usr/bin/env bash

set -euo pipefail

INSTALL_BIN="$HOME/.local/bin/click-to-claude"
DESKTOP_PATH="$HOME/.local/share/applications/click-to-claude.desktop"
LEGACY_DESKTOP_PATH="$HOME/.local/share/applications/click_claude.desktop"
PROFILE_DIR="$HOME/.local/share/click-to-claude"

rm -f -- "$INSTALL_BIN" "$DESKTOP_PATH" "$LEGACY_DESKTOP_PATH"

if command -v gsettings >/dev/null 2>&1; then
    python3 - <<'PY'
import ast
import subprocess

schema = "org.gnome.settings-daemon.plugins.media-keys"
removed_paths = {
    (
        "/org/gnome/settings-daemon/plugins/media-keys/"
        "custom-keybindings/custom-click-to-claude/"
    ),
    (
        "/org/gnome/settings-daemon/plugins/media-keys/"
        "custom-keybindings/custom-click-claude/"
    ),
}
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
updated = [path for path in current if path not in removed_paths]
if updated != current:
    subprocess.run(
        ["gsettings", "set", schema, "custom-keybindings", repr(updated)],
        check=False,
    )
PY
fi

echo "Click to Claude launchers and GNOME shortcut were removed."
echo "Browser login data was preserved at: $PROFILE_DIR"
echo "Remove that directory manually if you also want to delete the dedicated profile."

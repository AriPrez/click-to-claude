# Click to Claude

Capture a Linux screen region, add numbered pins or redactions, and paste the
annotated image plus structured context into a dedicated Claude web-app window.
No Anthropic API key is required.

## Why it is useful

- Select exactly the part of the screen you want to discuss.
- Add numbered pins with one question per location.
- See a zoomed Pin Lens thumbnail for every numbered point.
- Move, reorder, or remove pins individually.
- Draw arrows and highlights alongside privacy masks.
- Undo and redo annotation changes.
- Zoom and pan without changing the exported screenshot resolution.
- Export the annotated result as a standalone PNG.
- Redact secrets before clipboard transfer.
- Add a general request and optional source-window context.
- Review the exact generated text before it is pasted.
- Keep automatic paste isolated from ordinary browser windows.

Click to Claude never presses Claude's final Send button. You can review the
image and prompt in Claude before submitting them.

## Compatibility

| Environment | Capture | Clipboard | Automatic paste |
| --- | --- | --- | --- |
| Ubuntu/Debian X11 | Supported | `xclip` | Supported with Chromium and `xdotool` |
| GNOME Wayland | Desktop-dependent | `wl-copy` | Only when the dedicated window is visible through XWayland |
| wlroots Wayland | `grim` + `slurp` | `wl-copy` | Only when the dedicated window is visible through XWayland |
| KDE | Manual shortcut setup | X11 or Wayland backend | Same X11/XWayland limitation |

Automatic paste is deliberately disabled if the dedicated Claude window cannot
be identified positively. In that case, the annotated image remains available
for manual paste.

## Installation

On Ubuntu, Debian, Pop!_OS, or another apt-based distribution:

```bash
git clone https://github.com/AriPrez/click-to-claude.git
cd click-to-claude
bash install.sh
```

The installer:

1. Installs the screenshot, clipboard, Tkinter, and Pillow dependencies.
2. Installs `click-to-claude` into `~/.local/bin`.
3. Adds the desktop launcher.
4. Registers `Super+C` on GNOME-based desktops.

On other desktops, assign `click-to-claude` to a global shortcut manually.

The first automatic launch uses a dedicated Chromium profile stored under
`~/.local/share/click-to-claude`. Sign in to Claude once in that window.

Run a read-only environment check at any time:

```bash
click-to-claude --diagnose
```

To remove the launchers while preserving the dedicated browser login:

```bash
bash uninstall.sh
```

## Usage

1. Press `Super+C`, or run `click-to-claude`.
2. Select a screen region.
3. Add pins and comments, or switch to **Redact Area** and draw masks.
4. Use **Select** to move pins or select any annotation for deletion.
5. Add arrows, highlights, and an optional general request.
6. Choose whether to include the source-window title.
7. Select **Review & Paste**, inspect the generated text, then approve the paste.
8. Review the result in Claude and submit it yourself.

### Visual Prompt Studio shortcuts

| Shortcut | Action |
| --- | --- |
| `V` | Select |
| `P` | Add pin |
| `A` | Arrow |
| `H` | Highlight |
| `R` | Redact |
| `Ctrl+Z` / `Ctrl+Y` | Undo / redo |
| `Delete` | Remove selected annotation |
| Mouse wheel | Zoom |
| Middle-button drag | Pan |
| `Ctrl+Enter` | Open final review |
| `Ctrl+S` | Export annotated PNG |
| `Esc` | Cancel |

## Privacy and safety

- Captures are created inside a private temporary directory and deleted when the
  program exits.
- Window-title context can be disabled before review.
- Paste is allowed only into a Chromium window created with Click to Claude's
  dedicated class and profile.
- The program does not claim that data was sent; it only reports that paste
  commands completed.

The dedicated browser profile still contains its own Claude login data. The
uninstaller preserves it intentionally and prints its location.

## Development

Python 3.10 or newer is required.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest
```

The CI runs linting and tests across Python 3.10, 3.12, and 3.13.

## Current limitations

- Full Wayland automation is restricted by the compositor's security model.
- Automatic paste currently targets Chromium-family browsers.
- Text labels, freehand drawing, and automatic redaction suggestions are not yet
  implemented.
- Clipboard automation can confirm the operating-system commands, not that the
  Claude composer accepted every item.

## License

MIT. See [LICENSE](LICENSE).

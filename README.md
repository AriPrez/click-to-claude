# Click to Claude

Capture a Linux screen region, add numbered pins or redactions, and paste the
annotated image plus structured context into a dedicated Claude web-app window.
No Anthropic API key is required.

## Why it is useful

- Select exactly the part of the screen you want to discuss.
- Add numbered pins with one question per location.
- Redact secrets before OCR or clipboard transfer.
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

1. Installs the screenshot, clipboard, OCR, Tkinter, and Pillow dependencies.
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
4. Add an optional general request.
5. Choose whether to include OCR text and the source-window title. OCR is off
   by default and is mainly useful for code, logs, or very small text.
6. Select **Send to Claude**, review the generated text, then approve the paste.
7. Review the result in Claude and submit it yourself.

`Esc` cancels the editor. `Ctrl+Enter` opens the final review.

## Privacy and safety

- Captures are created inside a private temporary directory and deleted when the
  program exits.
- OCR runs only after redactions have been burned into the image.
- Window-title and OCR context can be disabled independently.
- Optional OCR is labelled as reference data rather than instructions.
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
- The annotation editor has reset, but not yet per-action undo/redo.
- Clipboard automation can confirm the operating-system commands, not that the
  Claude composer accepted every item.

## License

MIT. See [LICENSE](LICENSE).

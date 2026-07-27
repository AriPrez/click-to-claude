# Changelog

## 0.5.2 - 2026-07-27

### Fixed

- Detect the Claude composer from the rendered window instead of clicking a
  fixed vertical position that no longer matches Claude's new-chat layout.
- Reload a uniformly blank Claude page once, then wait for the composer before
  attempting any paste.
- Keep the reviewed prompt in the desktop's secondary selection while the PNG
  remains in the regular clipboard, enabling full manual recovery without
  writing private prompt text to disk.

## 0.5.1 - 2026-07-27

### Fixed

- Focus the Claude message composer before pasting instead of relying only on
  browser-window activation.
- Verify that the clipboard exposes the capture as `image/png`.
- Allow more time for Claude to consume an image before replacing clipboard
  contents with the reviewed prompt.
- Restore the PNG image to the clipboard after automation so manual `Ctrl+V`
  remains available as a fallback.

## 0.5.0 - 2026-07-27

### Changed

- Reworked the editor into a calmer desktop workspace with neutral surfaces,
  clearer typography, and one primary accent color.
- Simplified the header, tool rail, question cards, status bar, and
  user-facing labels.
- Redesigned the review dialog so its privacy message and confirmation action
  remain immediately visible.
- Updated the static preview and medical demo to match the new interface.

## 0.4.1 - 2026-07-27

### Added

- Dual-scale Pin Lens cards showing both the exact detail and its broader visual
  context.

### Changed

- The medical demo now uses smooth contextual zooms and a more realistic
  heart-analysis request focused on the mitral apparatus and a coronary vessel.

## 0.4.0 - 2026-07-27

### Added

- Original application icon and a privacy-safe Visual Prompt Studio preview.
- Precision pins with an unobstructed target, crosshair, leader line,
  edge-aware numbered badge, coordinates, and a more focused Pin Lens.
- Medical and scientific explanation goals plus a reproducible synthetic
  medical demo in GIF and MP4 formats.
- Security policy, structured issue forms, pull request checklist, and
  Dependabot configuration.
- Troubleshooting guidance for review confirmation, fail-safe paste, shortcuts,
  and Wayland.

### Changed

- Package metadata now advertises its supported platform, Python version, and
  project links.
- The Linux desktop launcher now installs and uses the project icon.
- Precision zoom now reaches 800%, stays focused under the cursor, and preserves
  the pin's grab offset while it is moved.

## 0.3.1 - 2026-07-27

### Removed

- OCR prompt injection, its editor toggle, and the Tesseract installation
  requirement. The attached screenshot is now the single visual source.

## 0.3.0 - 2026-07-27

### Added

- Visual Prompt Studio with a vertical tool rail and persistent privacy status.
- Pin Lens cards with local thumbnails, reordering, movement, and deletion.
- Reversible arrows, highlights, redactions, zoom, pan, undo, and redo.
- Standalone annotated PNG export.

### Changed

- The review dialog keeps its confirmation controls visible and focused.

## 0.2.0 - 2026-07-27

### Added

- Dedicated Chromium class and profile for safe window targeting.
- X11 and Wayland clipboard detection.
- `grim`/`slurp` capture support.
- Private, automatically cleaned temporary captures.
- Prompt review, general request, and privacy toggles.
- Adaptive Tesseract language selection and untrusted OCR delimiters.
- `--diagnose` and `--version`.
- Portable installer, uninstaller, tests, lint configuration, and CI.

### Changed

- Success notifications now describe a completed paste attempt, never a sent
  Claude message.
- Missing UI or system dependencies now stop safely instead of continuing.

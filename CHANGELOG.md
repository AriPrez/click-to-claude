# Changelog

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

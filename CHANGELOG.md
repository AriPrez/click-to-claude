# Changelog

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
- OCR is disabled by default and uses a shorter reference-data label.
- The review dialog keeps its confirmation controls visible and focused.

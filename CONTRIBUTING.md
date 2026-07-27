# Contributing

Thank you for improving Click to Claude.

## Local setup

```bash
git clone https://github.com/YOUR_USERNAME/click-to-claude.git
cd click-to-claude
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

Before opening a pull request:

```bash
ruff check .
ruff format --check .
pytest
python click_claude.py --diagnose
```

Do not use real passwords, API keys, private window titles, or personal
screenshots in fixtures or bug reports.

## Pull requests

1. Create a focused branch.
2. Add or update tests for behavior changes.
3. Keep browser targeting fail-safe: an unknown window must always be rejected.
4. Document changes to supported desktops, sessions, or dependencies.
5. Explain any privacy or clipboard implications in the pull request.

Useful areas include Wayland portal support, undo/redo in the annotation editor,
accessibility, additional safe browser targets, packaging, and translations.

## Summary

Describe the user-visible change and why it is needed.

## Validation

- [ ] `ruff check .`
- [ ] `ruff format --check .`
- [ ] `pytest`
- [ ] `python click_claude.py --diagnose`

## Safety review

- [ ] Unknown browser windows are rejected instead of targeted.
- [ ] Captures and temporary files are cleaned up.
- [ ] Fixtures, screenshots, logs, and window titles contain no private data.
- [ ] Clipboard, browser-profile, Wayland, or dependency changes are documented.

Mark non-applicable items and explain why.

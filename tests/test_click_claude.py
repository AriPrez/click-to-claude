from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image, ImageDraw

import click_claude


def test_build_prompt_respects_privacy_choices():
    prompt = click_claude.build_prompt(
        topic="Debug",
        pin_comments=["Fix this", ""],
        general_request="Explain the failure",
        source_window="",
        timestamp=datetime(2026, 7, 27, 12, 30),
    )

    assert "Explain the failure" in prompt
    assert "Pin (1): Fix this" in prompt
    assert "Pin (2): [Indicated area on image]" in prompt
    assert "Source window" not in prompt
    assert "2026-07-27 12:30" in prompt


@patch("click_claude.subprocess.check_output")
@patch("click_claude.shutil.which", return_value="/usr/bin/xprop")
def test_window_class_requires_dedicated_identity(_which, check_output):
    check_output.return_value = 'WM_CLASS(STRING) = "google-chrome", "Google-chrome"\n'
    assert not click_claude.window_has_expected_class("42")

    check_output.return_value = 'WM_CLASS(STRING) = "click-to-claude", "ClickToClaude"\n'
    assert click_claude.window_has_expected_class("42")


@patch("click_claude.window_has_expected_class", return_value=False)
def test_paste_is_blocked_for_an_unverified_window(_window_check):
    result = click_claude.paste_in_claude("42", "private prompt")

    assert not result.success
    assert "blocked" in result.message.lower()


def test_xdotool_shell_values_only_accepts_integer_fields():
    output = "WINDOW=42\nX=120\nY=-20\nSCREEN=0\nBROKEN=value\n"

    assert click_claude._xdotool_shell_values(output) == {
        "WINDOW": 42,
        "X": 120,
        "Y": -20,
        "SCREEN": 0,
    }


def test_composer_detection_finds_a_wide_panel_at_any_vertical_position():
    image = Image.new("RGB", (725, 1003), "#20201f")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((14, 351, 700, 506), radius=28, fill="#2c2c2a")

    assert click_claude._find_composer_center(image) == (362, 428)


def test_composer_detection_rejects_a_blank_page():
    image = Image.new("RGB", (725, 1003), "white")

    assert click_claude._find_composer_center(image) is None


@patch("click_claude.time.sleep")
@patch("click_claude.copy_image_to_clipboard")
@patch("click_claude.copy_text_to_clipboard")
@patch("click_claude.copy_text_to_primary")
@patch("click_claude.run_command")
@patch("click_claude.focus_claude_composer", return_value=True)
@patch("click_claude.window_has_expected_class", return_value=True)
def test_paste_focuses_composer_and_restores_image_clipboard(
    _window_check,
    focus_composer,
    run_command,
    copy_primary,
    copy_text,
    copy_image,
    _sleep,
):
    run_command.return_value = MagicMock(returncode=0)
    copy_primary.return_value = click_claude.ActionResult(True, "recovery copied")
    copy_text.return_value = click_claude.ActionResult(True, "text copied")
    copy_image.return_value = click_claude.ActionResult(True, "image restored")

    result = click_claude.paste_in_claude(
        "42",
        prompt_text="Explain the diagram",
        image_path="/tmp/capture.png",
    )

    assert result.success
    assert "Ctrl+V restores the PNG image" in result.message
    assert "Shift+Insert restores the review text" in result.message
    focus_composer.assert_called_once_with("42")
    copy_primary.assert_called_once_with("Explain the diagram")
    copy_text.assert_called_once_with("Explain the diagram")
    copy_image.assert_called_once_with("/tmp/capture.png")
    paste_commands = [
        call.args[0]
        for call in run_command.call_args_list
        if call.args[0][:2] == ["xdotool", "key"]
    ]
    assert paste_commands == [
        ["xdotool", "key", "--window", "42", "ctrl+v"],
        ["xdotool", "key", "--window", "42", "ctrl+v"],
    ]


@patch("click_claude.shutil.which", return_value=None)
def test_capture_reports_missing_backend(_which, tmp_path):
    result = click_claude.capture_screen(str(tmp_path / "capture.png"))

    assert not result.success
    assert "No supported screenshot tool" in result.message


@patch("click_claude.shutil.which")
def test_wayland_clipboard_is_preferred(which, monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    which.side_effect = lambda command: (
        f"/usr/bin/{command}"
        if command
        in {
            "wl-copy",
            "xclip",
        }
        else None
    )

    assert click_claude.clipboard_backend() == "wl-copy"


def test_main_always_removes_the_temporary_capture():
    capture_path = {}

    def fake_capture(image_path):
        capture_path["value"] = image_path
        Path(image_path).write_bytes(b"private screenshot")
        return click_claude.ActionResult(True, "captured")

    with (
        patch("click_claude.get_active_window_context", return_value="Editor"),
        patch("click_claude.capture_screen", side_effect=fake_capture),
        patch("click_claude.launch_pins_ui", return_value=(True, "prompt")),
        patch(
            "click_claude.copy_image_to_clipboard",
            return_value=click_claude.ActionResult(True, "copied"),
        ),
        patch(
            "click_claude.open_or_focus_claude",
            return_value=click_claude.BrowserResult(False, "", "manual paste"),
        ),
        patch("click_claude.send_notification"),
        patch("sys.argv", ["click-to-claude"]),
    ):
        assert click_claude.main() == 1

    assert not Path(capture_path["value"]).exists()

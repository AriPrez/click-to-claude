#!/usr/bin/env python3
"""
Click to Claude - Screenshot, Numbered Pins (1, 2, 3), Context & Auto-Paste (No API)
"""

import argparse
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

APP_NAME = "Click to Claude"
APP_VERSION = "0.5.1"
APP_WINDOW_CLASS = "ClickToClaude"
CLAUDE_URL = "https://claude.ai/new"
CHROME_PROFILE_DIR = Path.home() / ".local" / "share" / "click-to-claude" / "chrome-profile"
IMAGE_PASTE_SETTLE_SECONDS = 1.8
TEXT_PASTE_SETTLE_SECONDS = 0.8


@dataclass(frozen=True)
class ActionResult:
    success: bool
    message: str


@dataclass(frozen=True)
class BrowserResult:
    success: bool
    window_id: str
    message: str


def run_command(command, **kwargs):
    """Run an external command without opening a shell."""
    return subprocess.run(command, check=False, **kwargs)


def send_notification(title, message):
    try:
        run_command(["notify-send", "-i", "camera-photo", title, message])
    except OSError:
        return


def get_active_window_context():
    """Detects the name and title of the application window where the user was working."""
    if not shutil.which("xdotool"):
        return "Linux Application"
    try:
        wid = subprocess.check_output(["xdotool", "getactivewindow"], text=True).strip()
        title = subprocess.check_output(["xdotool", "getwindowname", wid], text=True).strip()
        return title if title else "Linux Desktop"
    except (OSError, subprocess.SubprocessError):
        return "Linux Application"


def capture_screen(image_path):
    """Capture a selected screen region using the first supported backend."""
    time.sleep(0.3)
    print("Select a region on your screen...")

    if (
        os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
        and shutil.which("slurp")
        and shutil.which("grim")
    ):
        selection = run_command(["slurp"], capture_output=True, text=True)
        if selection.returncode == 0 and selection.stdout.strip():
            result = run_command(["grim", "-g", selection.stdout.strip(), image_path])
            if (
                result.returncode == 0
                and os.path.exists(image_path)
                and os.path.getsize(image_path) > 0
            ):
                return ActionResult(True, "Captured with grim/slurp.")

    commands = []
    if shutil.which("gnome-screenshot"):
        commands.append(["gnome-screenshot", "-a", "-f", image_path])
    if shutil.which("maim"):
        commands.append(["maim", "-s", image_path])
    if shutil.which("scrot"):
        commands.append(["scrot", "-s", "-o", image_path])

    for command in commands:
        try:
            result = run_command(command)
        except OSError:
            continue
        if (
            result.returncode == 0
            and os.path.exists(image_path)
            and os.path.getsize(image_path) > 0
        ):
            return ActionResult(True, f"Captured with {command[0]}.")

    if not commands:
        return ActionResult(False, "No supported screenshot tool is installed.")
    return ActionResult(False, "Capture cancelled or all screenshot tools failed.")


def clipboard_backend():
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if session_type == "wayland" and shutil.which("wl-copy"):
        return "wl-copy"
    if shutil.which("xclip"):
        return "xclip"
    if shutil.which("wl-copy"):
        return "wl-copy"
    return None


def clipboard_contains_image():
    """Confirm that the current clipboard advertises PNG image data."""
    backend = clipboard_backend()
    try:
        if backend == "xclip":
            result = run_command(
                ["xclip", "-selection", "clipboard", "-t", "TARGETS", "-o"],
                capture_output=True,
                text=True,
            )
        elif backend == "wl-copy" and shutil.which("wl-paste"):
            result = run_command(
                ["wl-paste", "--list-types"],
                capture_output=True,
                text=True,
            )
        else:
            return False
    except OSError:
        return False
    return result.returncode == 0 and "image/png" in result.stdout.casefold()


def copy_image_to_clipboard(image_path):
    """Copy a PNG image to the available desktop clipboard."""
    if not os.path.exists(image_path):
        return ActionResult(False, "The captured image no longer exists.")
    backend = clipboard_backend()
    if not backend:
        return ActionResult(False, "Install xclip (X11) or wl-clipboard (Wayland).")
    try:
        if backend == "xclip":
            result = run_command(
                ["xclip", "-selection", "clipboard", "-t", "image/png", "-i", image_path]
            )
        else:
            with open(image_path, "rb") as image_file:
                result = run_command(
                    ["wl-copy", "--type", "image/png"],
                    stdin=image_file,
                )
    except OSError as error:
        return ActionResult(False, f"Clipboard error: {error}")
    if result.returncode != 0:
        return ActionResult(False, f"{backend} could not copy the image.")
    for _attempt in range(5):
        if clipboard_contains_image():
            return ActionResult(True, f"PNG image copied and verified with {backend}.")
        time.sleep(0.08)
    return ActionResult(False, "The clipboard did not expose the capture as image/png.")


def copy_text_to_clipboard(text):
    """Copy plain text to the available desktop clipboard."""
    backend = clipboard_backend()
    if not backend:
        return ActionResult(False, "Install xclip (X11) or wl-clipboard (Wayland).")
    command = (
        ["xclip", "-selection", "clipboard", "-t", "text/plain"]
        if backend == "xclip"
        else ["wl-copy", "--type", "text/plain;charset=utf-8"]
    )
    try:
        result = run_command(command, input=text.encode("utf-8"))
    except OSError as error:
        return ActionResult(False, f"Clipboard error: {error}")
    return ActionResult(result.returncode == 0, f"Text copied with {backend}.")


def get_claude_window():
    """Return only a window created with Click to Claude's dedicated class."""
    if not shutil.which("xdotool"):
        return None
    try:
        output = subprocess.check_output(
            ["xdotool", "search", "--onlyvisible", "--class", f"^{APP_WINDOW_CLASS}$"], text=True
        ).strip()
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        for wid in reversed(lines):
            if window_has_expected_class(wid):
                return wid
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def window_has_expected_class(window_id):
    """Verify WM_CLASS independently before allowing a paste."""
    if not shutil.which("xprop"):
        return False
    try:
        output = subprocess.check_output(
            ["xprop", "-id", window_id, "WM_CLASS"],
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    class_names = re.findall(r'"([^"]+)"', output)
    return any(class_name.casefold() == APP_WINDOW_CLASS.casefold() for class_name in class_names)


def find_chromium_browser():
    for executable in (
        "google-chrome-stable",
        "google-chrome",
        "chromium",
        "chromium-browser",
    ):
        path = shutil.which(executable)
        if path:
            return path
    return None


def activate_window(window_id):
    if not window_id or not shutil.which("xdotool"):
        return False
    result = run_command(["xdotool", "windowactivate", "--sync", window_id])
    return result.returncode == 0


def _xdotool_shell_values(output):
    values = {}
    for line in output.splitlines():
        key, separator, value = line.partition("=")
        if separator and value.strip().lstrip("-").isdigit():
            values[key.strip()] = int(value.strip())
    return values


def focus_claude_composer(window_id):
    """Focus the lower-center composer area in the verified app window."""
    if not activate_window(window_id):
        return False

    geometry = run_command(
        ["xdotool", "getwindowgeometry", "--shell", window_id],
        capture_output=True,
        text=True,
    )
    if geometry.returncode != 0:
        return False
    dimensions = _xdotool_shell_values(geometry.stdout)
    width = dimensions.get("WIDTH", 0)
    height = dimensions.get("HEIGHT", 0)
    if width < 240 or height < 320:
        return False

    cursor = run_command(
        ["xdotool", "getmouselocation", "--shell"],
        capture_output=True,
        text=True,
    )
    cursor_position = _xdotool_shell_values(cursor.stdout) if cursor.returncode == 0 else {}

    run_command(["xdotool", "key", "--window", window_id, "Escape"])
    target_x = width // 2
    target_y = max(120, height - 145)
    focused = run_command(
        [
            "xdotool",
            "mousemove",
            "--sync",
            "--window",
            window_id,
            str(target_x),
            str(target_y),
            "click",
            "1",
        ]
    )

    if "X" in cursor_position and "Y" in cursor_position:
        run_command(
            [
                "xdotool",
                "mousemove",
                "--sync",
                str(cursor_position["X"]),
                str(cursor_position["Y"]),
            ]
        )
    return focused.returncode == 0


def open_or_focus_claude():
    """Open or focus the isolated Claude web-app window."""
    wid = get_claude_window()
    if wid:
        activate_window(wid)
        time.sleep(0.4)
        return BrowserResult(True, wid, "Dedicated Claude window focused.")

    browser = find_chromium_browser()
    if not browser:
        if shutil.which("xdg-open"):
            run_command(["xdg-open", CLAUDE_URL])
        return BrowserResult(
            False,
            "",
            "No compatible Chromium browser found; Claude was opened without auto-paste.",
        )

    CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    chrome_cmd = [
        browser,
        f"--app={CLAUDE_URL}",
        f"--class={APP_WINDOW_CLASS}",
        f"--user-data-dir={CHROME_PROFILE_DIR}",
        "--window-size=580,820",
        "--window-position=940,100",
    ]
    if not shutil.which("xdotool"):
        run_command(chrome_cmd)
        return BrowserResult(
            False,
            "",
            "xdotool is unavailable; Claude was opened without auto-paste.",
        )

    print("Launching Claude mini-app window in Google Chrome...")
    try:
        subprocess.Popen(chrome_cmd)
        for _ in range(25):
            time.sleep(0.2)
            wid = get_claude_window()
            if wid:
                activate_window(wid)
                time.sleep(0.4)
                return BrowserResult(True, wid, "Dedicated Claude window opened.")
    except OSError as error:
        return BrowserResult(False, "", f"Could not launch the browser: {error}")

    return BrowserResult(
        False,
        "",
        "The dedicated Claude window could not be identified safely.",
    )


def paste_in_claude(wid=None, prompt_text=None, image_path=None):
    """Paste only into the positively identified Click to Claude window."""
    target_wid = wid or get_claude_window()
    if not target_wid:
        return ActionResult(False, "Safe Claude target not found.")

    if not window_has_expected_class(target_wid):
        return ActionResult(False, "Paste blocked: the target is not Click to Claude.")
    if not focus_claude_composer(target_wid):
        return ActionResult(False, "Could not focus the Claude message composer.")
    time.sleep(0.35)

    image_paste = run_command(["xdotool", "key", "--window", target_wid, "ctrl+v"])
    if image_paste.returncode != 0:
        return ActionResult(False, "The image paste command failed.")
    time.sleep(IMAGE_PASTE_SETTLE_SECONDS)

    if prompt_text:
        copied = copy_text_to_clipboard(prompt_text)
        if not copied.success:
            if image_path:
                copy_image_to_clipboard(image_path)
            return copied
        time.sleep(0.25)
        text_paste = run_command(["xdotool", "key", "--window", target_wid, "ctrl+v"])
        if text_paste.returncode != 0:
            if image_path:
                copy_image_to_clipboard(image_path)
            return ActionResult(False, "The prompt paste command failed.")
        time.sleep(TEXT_PASTE_SETTLE_SECONDS)

    if image_path:
        restored = copy_image_to_clipboard(image_path)
        if restored.success:
            return ActionResult(
                True,
                "Paste commands completed; the PNG image remains in the clipboard.",
            )
    return ActionResult(True, "Image and prompt paste commands completed.")


def build_prompt(
    topic,
    pin_comments,
    general_request="",
    source_window="",
    timestamp=None,
):
    """Build the text accompanying the annotated screenshot."""
    timestamp = timestamp or datetime.now()
    lines = [
        "AUTOMATIC CONTEXT:",
        f"- Topic: {topic}",
    ]
    if source_window:
        lines.append(f"- Source window: {source_window}")
    lines.extend((f"- Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M')}", ""))

    if general_request.strip():
        lines.extend(("GENERAL REQUEST:", general_request.strip(), ""))

    if pin_comments:
        lines.append("QUESTIONS BY NUMBERED PIN:")
        for number, comment in enumerate(pin_comments, start=1):
            note = comment.strip() or "[Indicated area on image]"
            lines.append(f"- Pin ({number}): {note}")
        lines.append("")

    if pin_comments:
        lines.append(
            "Analyze the image and answer the general request, then each numbered pin clearly."
        )
    else:
        lines.append("Analyze the image and answer the general request clearly.")
    return "\n".join(lines)


def _launch_legacy_pins_ui(image_path, active_window_title):
    """
    Tkinter interface to place numbered pins (1, 2, 3...),
    redact sensitive data, select topic context, and write pin-by-pin questions.
    """
    try:
        import tkinter as tk
        from tkinter import ttk

        from PIL import Image, ImageDraw, ImageFont, ImageTk
    except ImportError as error:
        raise RuntimeError("The annotation interface requires python3-tk and Pillow.") from error

    original_img = Image.open(image_path).convert("RGBA")
    edited_img = original_img.copy()
    draw = ImageDraw.Draw(edited_img)

    root = tk.Tk()
    root.title("Click to Claude - Pins & Context Engine")
    root.configure(bg="#181825")
    root.attributes("-topmost", True)

    mode = tk.StringVar(value="pin")
    topic_var = tk.StringVar(value="🐛 Debug & Code Fix")
    include_title_var = tk.BooleanVar(value=True)
    pins = []
    start_x, start_y = None, None
    rect_id = None

    max_w, max_h = 750, 520
    img_w, img_h = edited_img.size
    scale = min(max_w / img_w, max_h / img_h, 1.0)
    display_w = int(img_w * scale)
    display_h = int(img_h * scale)

    resized_display = edited_img.resize((display_w, display_h), Image.Resampling.LANCZOS)
    tk_img = ImageTk.PhotoImage(resized_display)

    main_frame = tk.Frame(root, bg="#181825")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    left_frame = tk.Frame(main_frame, bg="#181825")
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    toolbar = tk.Frame(left_frame, bg="#1e1e2e", pady=6, padx=8)
    toolbar.pack(fill=tk.X, side=tk.TOP)

    btn_pin = tk.Button(
        toolbar,
        text="📍 Add Pin (1, 2, 3)",
        bg="#89b4fa",
        fg="#11111b",
        font=("Helvetica", 10, "bold"),
        relief=tk.FLAT,
    )
    btn_pin.pack(side=tk.LEFT, padx=4)

    btn_mask = tk.Button(
        toolbar,
        text="⬛ Redact Area",
        bg="#f38ba8",
        fg="#11111b",
        font=("Helvetica", 10, "bold"),
        relief=tk.FLAT,
    )
    btn_mask.pack(side=tk.LEFT, padx=4)

    def set_mode(selected_mode):
        mode.set(selected_mode)
        btn_pin.configure(relief=tk.SUNKEN if selected_mode == "pin" else tk.FLAT)
        btn_mask.configure(relief=tk.SUNKEN if selected_mode == "mask" else tk.FLAT)

    btn_pin.configure(command=lambda: set_mode("pin"))
    btn_mask.configure(command=lambda: set_mode("mask"))
    set_mode("pin")

    def reset_all():
        nonlocal edited_img, draw, pins
        pins.clear()
        edited_img = original_img.copy()
        draw = ImageDraw.Draw(edited_img)
        for child in pins_scroll_frame.winfo_children():
            child.destroy()
        update_canvas()

    btn_reset = tk.Button(
        toolbar,
        text="🔄 Reset",
        bg="#45475a",
        fg="#cdd6f4",
        font=("Helvetica", 9),
        relief=tk.FLAT,
        command=reset_all,
    )
    btn_reset.pack(side=tk.LEFT, padx=4)

    canvas = tk.Canvas(
        left_frame,
        width=display_w,
        height=display_h,
        bg="#181825",
        highlightthickness=0,
    )
    canvas.pack(pady=5)
    canvas_img_id = canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)

    right_frame = tk.Frame(main_frame, bg="#1e1e2e", width=340, padx=10, pady=10)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))

    lbl_ctx_title = tk.Label(
        right_frame,
        text="🎯 Topic / Goal",
        fg="#cdd6f4",
        bg="#1e1e2e",
        font=("Helvetica", 10, "bold"),
    )
    lbl_ctx_title.pack(anchor="w", pady=(0, 2))

    topics = [
        "🐛 Debug & Code Fix",
        "💻 Refactoring & Optimization",
        "🎨 UI Design & Layout",
        "📄 Text Explanation & Docs",
        "⚙️ Terminal / Log Analysis",
        "💡 General Question",
    ]
    combo_topic = ttk.Combobox(
        right_frame,
        textvariable=topic_var,
        values=topics,
        state="readonly",
        font=("Helvetica", 9),
    )
    combo_topic.pack(fill=tk.X, pady=(0, 10))

    lbl_app_info = tk.Label(
        right_frame,
        text=f"📱 Source: {active_window_title[:35]}...",
        fg="#a6adc8",
        bg="#1e1e2e",
        font=("Helvetica", 8, "italic"),
    )
    lbl_app_info.pack(anchor="w", pady=(0, 8))

    lbl_request = tk.Label(
        right_frame,
        text="💬 General Request",
        fg="#cdd6f4",
        bg="#1e1e2e",
        font=("Helvetica", 10, "bold"),
    )
    lbl_request.pack(anchor="w", pady=(0, 4))

    general_request = tk.Text(
        right_frame,
        height=3,
        wrap=tk.WORD,
        bg="#181825",
        fg="#cdd6f4",
        insertbackground="#cdd6f4",
        relief=tk.FLAT,
        font=("Helvetica", 9),
    )
    general_request.pack(fill=tk.X, pady=(0, 6))

    privacy_frame = tk.Frame(right_frame, bg="#1e1e2e")
    privacy_frame.pack(fill=tk.X, pady=(0, 8))
    tk.Checkbutton(
        privacy_frame,
        text="Include window title",
        variable=include_title_var,
        bg="#1e1e2e",
        fg="#a6adc8",
        selectcolor="#313244",
        activebackground="#1e1e2e",
        activeforeground="#cdd6f4",
    ).pack(anchor="w")
    lbl_pins_title = tk.Label(
        right_frame,
        text="📍 Pin Notes & Questions",
        fg="#cdd6f4",
        bg="#1e1e2e",
        font=("Helvetica", 10, "bold"),
    )
    lbl_pins_title.pack(anchor="w", pady=(0, 5))

    pins_container = tk.Frame(right_frame, bg="#1e1e2e")
    pins_container.pack(fill=tk.BOTH, expand=True)
    pins_canvas = tk.Canvas(pins_container, bg="#1e1e2e", highlightthickness=0)
    scrollbar = ttk.Scrollbar(
        pins_container,
        orient="vertical",
        command=pins_canvas.yview,
    )
    pins_scroll_frame = tk.Frame(pins_canvas, bg="#1e1e2e")

    pins_scroll_frame.bind(
        "<Configure>", lambda e: pins_canvas.configure(scrollregion=pins_canvas.bbox("all"))
    )
    pins_canvas.create_window((0, 0), window=pins_scroll_frame, anchor="nw")
    pins_canvas.configure(yscrollcommand=scrollbar.set)

    pins_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    user_confirmed = [False]
    final_prompt = [""]

    def confirm_prompt(prompt):
        approved = [False]
        preview = tk.Toplevel(root)
        preview.title("Review data before pasting")
        preview.configure(bg="#181825")
        preview.transient(root)
        preview.resizable(True, True)

        screen_width = preview.winfo_screenwidth()
        screen_height = preview.winfo_screenheight()
        width = min(720, max(480, screen_width - 80))
        height = min(560, max(360, screen_height - 80))
        x_position = max(0, (screen_width - width) // 2)
        y_position = max(0, (screen_height - height) // 2)
        preview.geometry(f"{width}x{height}+{x_position}+{y_position}")

        tk.Label(
            preview,
            text="Review the exact text that will be pasted with the image",
            fg="#cdd6f4",
            bg="#181825",
            font=("Helvetica", 10, "bold"),
        ).pack(anchor="w", padx=12, pady=(12, 6))

        buttons = tk.Frame(preview, bg="#181825")
        buttons.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=12)

        def close_preview(is_approved=False):
            if not preview.winfo_exists():
                return
            approved[0] = is_approved
            try:
                preview.grab_release()
            except tk.TclError:
                pass
            preview.destroy()
            if root.winfo_exists():
                root.attributes("-topmost", True)
                root.lift()

        tk.Button(
            buttons,
            text="← Back",
            command=close_preview,
            bg="#45475a",
            fg="#cdd6f4",
            relief=tk.FLAT,
            padx=16,
            pady=10,
        ).pack(side=tk.LEFT)

        confirm_button = tk.Button(
            buttons,
            text="✓ CONFIRM AND PASTE",
            command=lambda: close_preview(True),
            bg="#a6e3a1",
            fg="#11111b",
            activebackground="#94e2d5",
            font=("Helvetica", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            default=tk.ACTIVE,
        )
        confirm_button.pack(side=tk.RIGHT)

        tk.Label(
            preview,
            text="Nothing is sent automatically. You will still review it in Claude.",
            fg="#a6adc8",
            bg="#181825",
            font=("Helvetica", 8, "italic"),
        ).pack(side=tk.BOTTOM, anchor="e", padx=12)

        prompt_preview = tk.Text(
            preview,
            wrap=tk.WORD,
            bg="#1e1e2e",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            relief=tk.FLAT,
        )
        prompt_preview.insert("1.0", prompt)
        prompt_preview.configure(state=tk.DISABLED)
        prompt_preview.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        root.attributes("-topmost", False)
        preview.attributes("-topmost", True)
        preview.protocol("WM_DELETE_WINDOW", close_preview)
        preview.bind("<Escape>", lambda _event: close_preview())
        preview.bind("<Control-Return>", lambda _event: close_preview(True))
        confirm_button.bind("<Return>", lambda _event: close_preview(True))
        preview.update_idletasks()
        preview.lift()
        preview.focus_force()
        confirm_button.focus_set()
        preview.grab_set()
        preview.wait_window()
        return approved[0]

    def send_action():
        edited_img.convert("RGB").save(image_path, "PNG")
        pin_comments = [pin["entry"].get() for pin in pins]
        final_prompt[0] = build_prompt(
            topic=topic_var.get(),
            pin_comments=pin_comments,
            general_request=general_request.get("1.0", tk.END),
            source_window=active_window_title if include_title_var.get() else "",
        )
        if not confirm_prompt(final_prompt[0]):
            return
        user_confirmed[0] = True
        root.destroy()

    btn_send = tk.Button(
        right_frame,
        text="🚀 SEND TO CLAUDE",
        bg="#a6e3a1",
        fg="#11111b",
        font=("Helvetica", 11, "bold"),
        relief=tk.FLAT,
        command=send_action,
        pady=8,
    )
    btn_send.pack(
        side=tk.BOTTOM,
        fill=tk.X,
        pady=(10, 0),
        before=pins_container,
    )

    def update_canvas():
        nonlocal tk_img, resized_display
        resized_display = edited_img.resize((display_w, display_h), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized_display)
        canvas.itemconfig(canvas_img_id, image=tk_img)

    def draw_pin_badge(orig_x, orig_y, num):
        radius = max(14, int(14 / scale))
        bbox = [orig_x - radius, orig_y - radius, orig_x + radius, orig_y + radius]
        draw.ellipse(
            bbox,
            fill=(243, 139, 168, 255),
            outline=(255, 255, 255, 255),
            width=max(2, int(2 / scale)),
        )

        try:
            font = ImageFont.truetype(
                "DejaVuSans-Bold.ttf",
                max(16, int(16 / scale)),
            )
        except OSError:
            font = ImageFont.load_default()

        text_str = str(num)
        draw.text((orig_x, orig_y), text_str, fill=(17, 17, 27, 255), anchor="mm", font=font)

    def add_pin(x, y):
        num = len(pins) + 1
        orig_x = int(x / scale)
        orig_y = int(y / scale)

        draw_pin_badge(orig_x, orig_y, num)
        update_canvas()

        pin_item_frame = tk.Frame(pins_scroll_frame, bg="#313244", pady=4, padx=6)
        pin_item_frame.pack(fill=tk.X, pady=4, expand=True)

        lbl_badge = tk.Label(
            pin_item_frame,
            text=f"({num})",
            fg="#f38ba8",
            bg="#313244",
            font=("Helvetica", 10, "bold"),
        )
        lbl_badge.pack(side=tk.LEFT, padx=(0, 4))

        entry_comment = tk.Entry(
            pin_item_frame,
            bg="#1e1e2e",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            font=("Helvetica", 9),
            relief=tk.FLAT,
            width=22,
        )
        entry_comment.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry_comment.focus_set()

        pins.append({"num": num, "x": orig_x, "y": orig_y, "entry": entry_comment})

    def on_press(event):
        nonlocal start_x, start_y, rect_id
        start_x, start_y = event.x, event.y
        if mode.get() == "pin":
            add_pin(event.x, event.y)
        elif mode.get() == "mask":
            rect_id = canvas.create_rectangle(
                start_x,
                start_y,
                start_x,
                start_y,
                fill="#11111b",
                outline="#f38ba8",
                width=2,
            )

    def on_drag(event):
        if mode.get() == "mask" and rect_id:
            canvas.coords(rect_id, start_x, start_y, event.x, event.y)

    def on_release(event):
        nonlocal rect_id
        if mode.get() == "mask" and rect_id:
            canvas.delete(rect_id)
            rect_id = None
            orig_x1 = int(min(start_x, event.x) / scale)
            orig_y1 = int(min(start_y, event.y) / scale)
            orig_x2 = int(max(start_x, event.x) / scale)
            orig_y2 = int(max(start_y, event.y) / scale)
            draw.rectangle([orig_x1, orig_y1, orig_x2, orig_y2], fill=(17, 17, 27, 255))
            update_canvas()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", lambda _event: root.destroy())
    root.bind("<Control-Return>", lambda _event: send_action())

    root.mainloop()
    return user_confirmed[0], final_prompt[0]


def launch_pins_ui(image_path, active_window_title):
    """Launch the screenshot editor, with the compact editor as fallback."""
    try:
        from editor_ui import ScreenshotEditor
    except ModuleNotFoundError as error:
        if error.name != "editor_ui":
            raise
        return _launch_legacy_pins_ui(image_path, active_window_title)

    editor = ScreenshotEditor(
        image_path=image_path,
        active_window_title=active_window_title,
        build_prompt=build_prompt,
    )
    return editor.run()


def diagnostic_report():
    """Return a human-readable environment report without capturing anything."""
    session = os.environ.get("XDG_SESSION_TYPE", "unknown")
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "unknown")
    tools = (
        "gnome-screenshot",
        "maim",
        "scrot",
        "grim",
        "slurp",
        "xclip",
        "wl-copy",
        "xdotool",
        "xprop",
        "notify-send",
    )
    lines = [
        f"{APP_NAME} {APP_VERSION}",
        f"Session: {session}",
        f"Desktop: {desktop}",
        f"Browser: {find_chromium_browser() or 'not found'}",
        "Tools:",
    ]
    lines.extend(f"  {'OK' if shutil.which(tool) else '--'} {tool}" for tool in tools)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Click to Claude - Context, Pins & Safe Paste")
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="print environment and dependency information, then exit",
    )
    parser.add_argument("--version", action="version", version=APP_VERSION)
    args = parser.parse_args()
    if args.diagnose:
        print(diagnostic_report())
        return 0

    active_window_title = get_active_window_context()

    try:
        with tempfile.TemporaryDirectory(prefix="click-to-claude-") as temp_dir:
            image_path = os.path.join(temp_dir, "capture.png")
            captured = capture_screen(image_path)
            if not captured.success:
                print(captured.message)
                return 1

            try:
                confirmed, prompt_text = launch_pins_ui(
                    image_path,
                    active_window_title,
                )
            except (RuntimeError, OSError) as error:
                message = f"Annotation interface unavailable: {error}"
                print(message)
                send_notification(APP_NAME, message)
                return 1
            if not confirmed:
                print("Sending cancelled by user.")
                return 0

            copied = copy_image_to_clipboard(image_path)
            if not copied.success:
                print(copied.message)
                send_notification(APP_NAME, copied.message)
                return 1

            browser = open_or_focus_claude()
            if not browser.success:
                print(browser.message)
                send_notification(
                    APP_NAME,
                    "Image copied. Open Claude and paste it manually.",
                )
                return 1

            pasted = paste_in_claude(
                browser.window_id,
                prompt_text=prompt_text,
                image_path=image_path,
            )
            if not pasted.success:
                print(pasted.message)
                send_notification(APP_NAME, f"Auto-paste stopped: {pasted.message}")
                return 1

            send_notification(
                f"{APP_NAME} 🚀",
                "Paste completed. The image remains in the clipboard as a fallback.",
            )
            return 0
    except OSError as error:
        print(f"Temporary capture error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

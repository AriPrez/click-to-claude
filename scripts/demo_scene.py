#!/usr/bin/env python3
"""Run a deterministic, privacy-safe product demo for screen recording."""

import sys
import tkinter as tk
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from click_claude import build_prompt  # noqa: E402
from editor_ui import ScreenshotEditor  # noqa: E402


def main():
    image_path = PROJECT_ROOT / "assets" / "demo-medical-heart.png"
    editor = ScreenshotEditor(
        image_path=image_path,
        active_window_title="Synthetic cardiac anatomy — educational demo",
        build_prompt=build_prompt,
    )
    editor.topic.set("🩺 Medical Diagram Explanation")
    editor.include_title.set(False)
    editor.general_request.insert(
        "1.0",
        "Explain each selected structure at a medical-student level. "
        "Use the image only as an educational illustration.",
    )
    editor.root.geometry("1480x900+60+50")

    def focus_target(x_position, y_position, zoom):
        editor._set_zoom(zoom)
        editor.root.update_idletasks()
        scale = editor.base_scale * editor.zoom
        left = max(0, x_position * scale - editor.canvas.winfo_width() / 2)
        top = max(0, y_position * scale - editor.canvas.winfo_height() / 2)
        scroll_width = max(editor.canvas.winfo_width(), editor.display_width)
        scroll_height = max(editor.canvas.winfo_height(), editor.display_height)
        editor.canvas.xview_moveto(left / scroll_width)
        editor.canvas.yview_moveto(top / scroll_height)

    def add_pin(x_position, y_position, comment):
        editor._push_history()
        operation = editor._new_operation(
            "pin",
            x=x_position,
            y=y_position,
        )
        operation["comment"] = comment
        editor.operations.append(operation)
        editor.selected_id = operation["id"]
        editor._after_state_change()

    def add_highlight():
        editor._push_history()
        editor.operations.append(
            editor._new_operation(
                "highlight",
                x1=724,
                y1=420,
                x2=990,
                y2=682,
            )
        )
        editor._after_state_change()

    def show_review():
        editor._sync_comments()
        prompt = build_prompt(
            topic=editor.topic.get(),
            pin_comments=[
                operation.get("comment", "")
                for operation in editor.operations
                if operation["type"] == "pin"
            ],
            general_request=editor.general_request.get("1.0", tk.END),
            source_window="",
        )

        def close_demo():
            for child in editor.root.winfo_children():
                if isinstance(child, tk.Toplevel):
                    child.destroy()
            editor.root.after(250, editor.root.destroy)

        editor.root.after(3000, close_demo)
        editor._confirm_prompt(prompt)

    editor.root.after(700, lambda: focus_target(875, 485, 1.75))
    editor.root.after(
        1900,
        lambda: add_pin(
            875,
            485,
            "Identify this valve and explain how it prevents backflow.",
        ),
    )
    editor.root.after(3900, lambda: focus_target(1084, 557, 1.0))
    editor.root.after(
        4500,
        lambda: add_pin(
            1084,
            557,
            "Which coronary vessel is shown here, and what region does it supply?",
        ),
    )
    editor.root.after(6100, add_highlight)
    editor.root.after(7600, show_review)
    editor.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

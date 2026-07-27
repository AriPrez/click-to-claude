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
        "Analyze the heart in this cross-sectional diagram. Study in particular "
        "the mitral valve apparatus, its chordae tendineae, and the epicardial "
        "coronary vessel marked by the pins. Connect each local detail to the "
        "overall cardiac cycle and state any uncertainty caused by the unlabeled illustration.",
    )
    editor.root.geometry("1480x900+60+50")
    view_state = {"x": 768.0, "y": 512.0, "zoom": 1.0}

    def set_view(x_position, y_position, zoom):
        editor._set_zoom(zoom)
        editor.root.update_idletasks()
        scale = editor.base_scale * editor.zoom
        left = max(0, x_position * scale - editor.canvas.winfo_width() / 2)
        top = max(0, y_position * scale - editor.canvas.winfo_height() / 2)
        scroll_width = max(editor.canvas.winfo_width(), editor.display_width)
        scroll_height = max(editor.canvas.winfo_height(), editor.display_height)
        editor.canvas.xview_moveto(left / scroll_width)
        editor.canvas.yview_moveto(top / scroll_height)
        view_state.update(x=x_position, y=y_position, zoom=zoom)

    def animate_view(
        x_position,
        y_position,
        zoom,
        duration=800,
        steps=8,
        on_complete=None,
    ):
        start_x = view_state["x"]
        start_y = view_state["y"]
        start_zoom = view_state["zoom"]

        for step in range(1, steps + 1):
            progress = step / steps
            eased = progress * progress * (3 - 2 * progress)
            current_x = start_x + (x_position - start_x) * eased
            current_y = start_y + (y_position - start_y) * eased
            current_zoom = start_zoom + (zoom - start_zoom) * eased
            editor.root.after(
                round(duration * progress),
                lambda x=current_x, y=current_y, level=current_zoom: set_view(x, y, level),
            )
        if on_complete:
            editor.root.after(duration + 80, on_complete)

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

        editor.root.after(3300, close_demo)
        editor._confirm_prompt(prompt)

    def add_coronary_pin():
        add_pin(
            1084,
            557,
            "Examine this surface coronary vessel in context. Describe its course "
            "and explain which orientation or label would be needed to identify "
            "the exact branch reliably.",
        )
        editor.root.after(900, add_highlight)
        editor.root.after(
            1250,
            lambda: animate_view(
                768,
                512,
                0.95,
                duration=700,
                on_complete=lambda: editor.root.after(600, show_review),
            ),
        )

    def zoom_to_coronary():
        animate_view(
            1084,
            557,
            1.55,
            duration=700,
            on_complete=lambda: editor.root.after(250, add_coronary_pin),
        )

    def show_context():
        animate_view(
            768,
            512,
            1.0,
            duration=700,
            on_complete=lambda: editor.root.after(300, zoom_to_coronary),
        )

    def add_mitral_pin():
        add_pin(
            875,
            500,
            "Study this atrioventricular valve apparatus in particular: identify "
            "the visible leaflets and explain how the chordae tendineae prevent "
            "prolapse during systole.",
        )
        editor.root.after(850, show_context)

    def start_demo():
        animate_view(
            875,
            500,
            1.85,
            duration=850,
            on_complete=lambda: editor.root.after(250, add_mitral_pin),
        )

    editor.root.after(500, start_demo)
    editor.root.title("Click to Claude — Visual Prompt Studio — Demo Ready")
    editor.root.update_idletasks()
    editor.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

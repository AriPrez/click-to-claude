from unittest.mock import MagicMock, patch

from PIL import Image

from editor_ui import ScreenshotEditor


def test_distance_to_segment_handles_projection_and_endpoints():
    assert ScreenshotEditor._distance_to_segment(5, 3, 0, 0, 10, 0) == 3
    assert ScreenshotEditor._distance_to_segment(-2, 0, 0, 0, 10, 0) == 2
    assert ScreenshotEditor._distance_to_segment(3, 4, 0, 0, 0, 0) == 5


def test_normalized_box_accepts_reverse_dragging():
    operation = {"x1": 90, "y1": 70, "x2": 10, "y2": 20}

    assert ScreenshotEditor._normalized_box(operation) == (10, 20, 90, 70)


def test_precision_pin_keeps_the_exact_target_pixel_visible():
    editor = ScreenshotEditor.__new__(ScreenshotEditor)
    editor.base_scale = 1.0
    image = Image.new("RGBA", (200, 120), "white")
    operation = {"id": 1, "type": "pin", "x": 100, "y": 60, "comment": ""}

    editor._draw_pin(image, operation, 1)

    assert image.getpixel((100, 60)) == (255, 255, 255, 255)
    assert image.getpixel((124, 47))[:3] == (124, 92, 255)


def test_precision_pin_badge_stays_inside_image_near_edges():
    geometry = ScreenshotEditor._pin_geometry(
        {"x": 195, "y": 5},
        (200, 120),
        1.0,
    )

    assert geometry["badge_x"] < 195
    assert geometry["badge_y"] > 5
    assert geometry["radius"] <= geometry["badge_x"] <= 200 - geometry["radius"]
    assert geometry["radius"] <= geometry["badge_y"] <= 120 - geometry["radius"]


def test_zoom_supports_eight_times_magnification():
    editor = ScreenshotEditor.__new__(ScreenshotEditor)
    editor.zoom = 1.0
    editor._render = MagicMock()
    editor._update_status = MagicMock()

    editor._set_zoom(12)

    assert editor.zoom == 8.0


def test_export_render_applies_vector_annotations_without_selection():
    editor = ScreenshotEditor.__new__(ScreenshotEditor)
    editor.original_image = Image.new("RGBA", (200, 120), "white")
    editor.base_scale = 1.0
    editor.preview_operation = None
    editor.selected_id = 1
    editor.operations = [
        {
            "id": 1,
            "type": "redact",
            "x1": 10,
            "y1": 10,
            "x2": 60,
            "y2": 40,
        },
        {
            "id": 2,
            "type": "highlight",
            "x1": 80,
            "y1": 10,
            "x2": 140,
            "y2": 40,
        },
        {
            "id": 3,
            "type": "arrow",
            "x1": 20,
            "y1": 80,
            "x2": 100,
            "y2": 80,
        },
    ]

    rendered = editor._render_image(show_selection=False)

    assert rendered.getpixel((30, 25))[:3] == (8, 12, 20)
    assert rendered.getpixel((100, 25))[:3] != (255, 255, 255)
    assert rendered.getpixel((50, 80))[:3] == (34, 211, 238)


def test_export_png_saves_the_clean_render(tmp_path):
    editor = ScreenshotEditor.__new__(ScreenshotEditor)
    editor.root = MagicMock()
    editor.status_text = MagicMock()
    editor.status_text.get.return_value = "READY"
    editor._render_image = MagicMock(return_value=Image.new("RGBA", (40, 30), "#7c5cff"))
    destination = tmp_path / "annotated.png"

    with patch(
        "editor_ui.filedialog.asksaveasfilename",
        return_value=str(destination),
    ):
        editor._export_png()

    assert destination.exists()
    assert Image.open(destination).getpixel((10, 10)) == (124, 92, 255)
    editor._render_image.assert_called_once_with(show_selection=False)

#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
SCENE_SCRIPT="$SCRIPT_DIR/demo_scene.py"
MP4_OUTPUT="$PROJECT_ROOT/assets/precision-pin-medical-demo.mp4"
GIF_OUTPUT="$PROJECT_ROOT/assets/precision-pin-medical-demo.gif"

for command_name in Xvfb ffmpeg xdotool xvfb-run; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "Missing demo dependency: $command_name" >&2
        exit 1
    fi
done

xvfb-run -a -s "-screen 0 1600x1000x24 -nolisten tcp" \
    bash -c '
        set -euo pipefail
        output_path="$1"
        scene_script="$2"
        python3 "$scene_script" &
        scene_pid=$!
        window_id=""
        for _attempt in $(seq 1 100); do
            window_id="$(xdotool search --name Demo.Ready 2>/dev/null | tail -n 1 || true)"
            if test -n "$window_id"; then
                break
            fi
            sleep 0.1
        done
        if test -z "$window_id"; then
            kill "$scene_pid" 2>/dev/null || true
            wait "$scene_pid" 2>/dev/null || true
            echo "The demo window did not appear." >&2
            exit 1
        fi
        ffmpeg -loglevel warning -y \
            -f x11grab \
            -draw_mouse 0 \
            -framerate 30 \
            -video_size 1600x1000 \
            -i "$DISPLAY" \
            -t 30 \
            -c:v libx264 \
            -preset medium \
            -crf 23 \
            -pix_fmt yuv420p \
            -movflags +faststart \
            "$output_path" &
        recorder_pid=$!
        wait "$scene_pid"
        kill -INT "$recorder_pid" 2>/dev/null || true
        wait "$recorder_pid" || true
    ' bash "$MP4_OUTPUT" "$SCENE_SCRIPT"

ffmpeg -loglevel warning -y \
    -i "$MP4_OUTPUT" \
    -filter_complex \
    "fps=8,scale=840:-1:flags=lanczos,split[frames][palette_input];[palette_input]palettegen=max_colors=96[palette];[frames][palette]paletteuse=dither=bayer:bayer_scale=3" \
    "$GIF_OUTPUT"

echo "Created:"
echo "  $MP4_OUTPUT"
echo "  $GIF_OUTPUT"

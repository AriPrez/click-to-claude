# 🚀 Click to Claude

> **Instant Linux Screenshot, Numbered Pins & Context Injection Tool for Claude.ai (No API Required)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Linux](https://img.shields.io/badge/Platform-Linux%20%28X11%2FGNOME%2FKDE%29-blue.svg)]()
[![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)]()

**Click to Claude** is an ultra-fast Linux productivity tool that allows you to instantly send any region of your screen to **Claude.ai** with **numbered pin markers (1, 2, 3...)**, **automatic OCR text extraction**, and **active window context** — completely free without requiring an API key!

---

## ✨ Key Features

- ⚡ **1-Click Global Shortcut (`Super + C`)**: Press `Windows + C` anywhere to trigger instant screen region selection.
- 📍 **Numbered Pins (1, 2, 3...)**: Click anywhere on the screenshot to place numbered pin markers and write pin-by-pin questions.
- ⬛ **Sensitive Data Redaction**: Drag to draw black boxes over passwords, API keys, and sensitive tokens before sending.
- 🧠 **Automatic Context Engine**: Automatically detects the source app and window title you were working on (*e.g., VS Code - main.py*).
- 📄 **Automatic OCR Extraction (Tesseract)**: Extracts raw code/text from the screenshot and indexes it in plain text inside the prompt for maximum accuracy.
- 🪟 **Dedicated Mini-App Window**: Launches/focuses a compact, toolbar-free WebApp window for Claude.ai.
- 📋 **100% Automated Paste (`Ctrl+V`)**: Automatically pastes both the annotated image and structured Mega-Prompt without any manual action!

---

## 🛠️ Quick Installation

Open a terminal in the project directory and run:

```bash
cd /home/ari_prezo/Bureau/Click
bash install.sh
```

The script will automatically:
1. Install required Linux dependencies (`xclip`, `xdotool`, `scrot`, `tesseract-ocr`, `python3-tk`, `python3-pil`).
2. Configure the global keyboard shortcut **`Super + C`** (Windows Key + C).

---

## 🎮 How to Use

1. Press **`Super + C`** (Windows Key + C).
2. Click & drag to select a region on your screen.
3. Click anywhere to add numbered pins **(1, 2, 3...)**, type your questions, or redact sensitive areas.
4. Click **`🚀 SEND TO CLAUDE`**!

---

## 📂 Project Structure

- `click_claude.py`: Main Python script (GUI, capture, OCR, window targeting, and auto-paste engine).
- `install.sh`: Automated dependency installer and desktop shortcut registrar.
- `click_claude.desktop`: Desktop application launcher entry.
- `LICENSE`: Open-source MIT License.
- `CONTRIBUTING.md`: Guidelines for open-source contributors.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

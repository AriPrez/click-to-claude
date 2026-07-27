#!/usr/bin/env python3
"""
Click to Claude - Capture, Épingles (1, 2, 3), Contexte Automatique, OCR & Injection (Sans API)
Workspace: /home/ari_prezo/Bureau/Click
"""

import sys
import os
import subprocess
import time
import argparse
from datetime import datetime

TMP_IMG = "/tmp/click_claude.png"

def send_notification(title, message):
    try:
        subprocess.run(["notify-send", "-i", "camera-photo", title, message], check=False)
    except Exception:
        pass

def get_active_window_context():
    """Détecte le nom de l'application et le titre de la fenêtre où l'utilisateur travaillait."""
    try:
        wid = subprocess.check_output(["xdotool", "getactivewindow"], text=True).strip()
        title = subprocess.check_output(["xdotool", "getwindowname", wid], text=True).strip()
        return title if title else "Écran / Bureau Linux"
    except Exception:
        return "Application Linux"

def extract_ocr_text(image_path):
    """Extrait le texte brut ou code présent dans l'image avec Tesseract (si disponible)."""
    try:
        res = subprocess.run(
            ["tesseract", image_path, "stdout", "-l", "eng+fra"],
            capture_output=True, text=True, check=False
        )
        if res.returncode == 0:
            text = res.stdout.strip()
            # Ne garder que si le texte est significatif (plus de 5 caractères)
            if len(text) > 5:
                return text
    except Exception:
        pass
    return None

def capture_screen():
    """Capture d'écran partielle avec scrot."""
    if os.path.exists(TMP_IMG):
        try:
            os.remove(TMP_IMG)
        except OSError:
            pass

    time.sleep(0.3)
    print("Veuillez sélectionner la zone à l'écran...")
    res = subprocess.run(["scrot", "-s", "-o", TMP_IMG], check=False)
    return res.returncode == 0 and os.path.exists(TMP_IMG)

def copy_image_to_clipboard(image_path):
    """Copie l'image PNG dans le presse-papier X11."""
    if not os.path.exists(image_path):
        return False
    res = subprocess.run(
        ["xclip", "-selection", "clipboard", "-t", "image/png", "-i", image_path],
        check=False
    )
    return res.returncode == 0

def copy_text_to_clipboard(text):
    """Copie du texte brut dans le presse-papier X11."""
    p = subprocess.Popen(["xclip", "-selection", "clipboard", "-t", "text/plain"], stdin=subprocess.PIPE)
    p.communicate(input=text.encode('utf-8'))

def get_claude_window():
    """Recherche l'ID de la fenêtre du mini-onglet Claude (exclut Antigravity et VSCode)."""
    try:
        output = subprocess.check_output(
            ["xdotool", "search", "--onlyvisible", "--name", "Claude"],
            text=True
        ).strip()
        lines = [line.strip() for line in output.split('\n') if line.strip()]
        for wid in reversed(lines):
            wname = subprocess.check_output(["xdotool", "getwindowname", wid], text=True).strip()
            if "Antigravity" not in wname and "Visual Studio" not in wname:
                return wid
    except Exception:
        pass
    return None

def open_or_focus_claude():
    """Ouvre une petite fenêtre mini-app dédiée à Claude et s'assure qu'elle est active."""
    wid = get_claude_window()
    if wid:
        subprocess.run(["xdotool", "windowactivate", "--sync", wid], check=False)
        time.sleep(0.4)
        return wid
    
    print("Lancement du mini-onglet Claude dans Google Chrome...")
    chrome_cmd = [
        "google-chrome",
        "--app=https://claude.ai/new",
        "--window-size=580,820",
        "--window-position=940,100"
    ]
    
    try:
        subprocess.Popen(chrome_cmd)
        for _ in range(20):
            time.sleep(0.2)
            wid = get_claude_window()
            if wid:
                subprocess.run(["xdotool", "windowactivate", "--sync", wid], check=False)
                time.sleep(0.4)
                return wid
    except Exception:
        subprocess.run(["xdg-open", "https://claude.ai/new"], check=False)
        time.sleep(2.0)
        
    return get_claude_window()

def paste_in_claude(wid=None, prompt_text=None):
    """Exécute le coller de l'image ET du prompt structuré dans Claude."""
    if not wid:
        send_notification("Click to Claude", "L'image est dans votre presse-papier. Ouvrez Claude pour la coller !")
        return

    subprocess.run(["xdotool", "windowactivate", "--sync", wid], check=False)
    time.sleep(0.5)

    # 1. Coller l'image
    subprocess.run(["xdotool", "key", "ctrl+v"], check=False)
    time.sleep(0.6)

    # 2. Copier et coller le Mega-Prompt structuré
    if prompt_text:
        copy_text_to_clipboard(prompt_text)
        time.sleep(0.2)
        subprocess.run(["xdotool", "key", "ctrl+v"], check=False)

def launch_pins_ui(image_path, active_window_title):
    """
    Interface d'Épinglage avec Sélecteur de Sujet/Contexte et OCR automatique.
    """
    try:
        import tkinter as tk
        from tkinter import ttk
        from PIL import Image, ImageTk, ImageDraw, ImageFont
    except ImportError:
        return True, ""

    original_img = Image.open(image_path).convert("RGBA")
    edited_img = original_img.copy()
    draw = ImageDraw.Draw(edited_img)

    root = tk.Tk()
    root.title("Click to Claude - Contexte Enrichi & Épingles (1, 2, 3...)")
    root.configure(bg="#181825")
    root.attributes('-topmost', True)

    mode = tk.StringVar(value="pin")
    topic_var = tk.StringVar(value="🐛 Debug & Correction de Code")
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
        toolbar, text="📍 Épingle (1, 2, 3)", bg="#89b4fa", fg="#11111b",
        font=("Helvetica", 10, "bold"), relief=tk.FLAT,
        command=lambda: mode.set("pin")
    )
    btn_pin.pack(side=tk.LEFT, padx=4)

    btn_mask = tk.Button(
        toolbar, text="⬛ Masquer Zone", bg="#f38ba8", fg="#11111b",
        font=("Helvetica", 10, "bold"), relief=tk.FLAT,
        command=lambda: mode.set("mask")
    )
    btn_mask.pack(side=tk.LEFT, padx=4)

    def reset_all():
        nonlocal edited_img, draw, pins
        pins.clear()
        edited_img = original_img.copy()
        draw = ImageDraw.Draw(edited_img)
        for child in pins_scroll_frame.winfo_children():
            child.destroy()
        update_canvas()

    btn_reset = tk.Button(
        toolbar, text="🔄 Effacer", bg="#45475a", fg="#cdd6f4",
        font=("Helvetica", 9), relief=tk.FLAT, command=reset_all
    )
    btn_reset.pack(side=tk.LEFT, padx=4)

    canvas = tk.Canvas(left_frame, width=display_w, height=display_h, bg="#181825", highlightthickness=0)
    canvas.pack(pady=5)
    canvas_img_id = canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)

    # Panneau de droite (Contexte + Questions)
    right_frame = tk.Frame(main_frame, bg="#1e1e2e", width=340, padx=10, pady=10)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))

    # Zone 1 : Sélection du sujet / contexte
    lbl_ctx_title = tk.Label(right_frame, text="🎯 Sujet / Objectif", fg="#cdd6f4", bg="#1e1e2e", font=("Helvetica", 10, "bold"))
    lbl_ctx_title.pack(anchor="w", pady=(0, 2))

    topics = [
        "🐛 Debug & Correction de Code",
        "💻 Refactoring & Optimisation",
        "🎨 Design UI & Intégration",
        "📄 Explication de texte / Docs",
        "⚙️ Analyse de Logs / Terminal",
        "💡 Général / Question"
    ]
    combo_topic = ttk.Combobox(right_frame, textvariable=topic_var, values=topics, state="readonly", font=("Helvetica", 9))
    combo_topic.pack(fill=tk.X, pady=(0, 10))

    # Info application source détectée
    lbl_app_info = tk.Label(
        right_frame, text=f"📱 Source : {active_window_title[:35]}...",
        fg="#a6adc8", bg="#1e1e2e", font=("Helvetica", 8, "italic")
    )
    lbl_app_info.pack(anchor="w", pady=(0, 8))

    # Zone 2 : Questions par repère
    lbl_pins_title = tk.Label(right_frame, text="📍 Questions par Repère", fg="#cdd6f4", bg="#1e1e2e", font=("Helvetica", 10, "bold"))
    lbl_pins_title.pack(anchor="w", pady=(0, 5))

    pins_canvas = tk.Canvas(right_frame, bg="#1e1e2e", highlightthickness=0)
    scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=pins_canvas.yview)
    pins_scroll_frame = tk.Frame(pins_canvas, bg="#1e1e2e")

    pins_scroll_frame.bind(
        "<Configure>",
        lambda e: pins_canvas.configure(scrollregion=pins_canvas.bbox("all"))
    )
    pins_canvas.create_window((0, 0), window=pins_scroll_frame, anchor="nw")
    pins_canvas.configure(yscrollcommand=scrollbar.set)

    pins_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    user_confirmed = [False]
    final_prompt = [""]

    def send_action():
        edited_img.convert("RGB").save(image_path, "PNG")
        
        # Extrait OCR automatique
        ocr_text = extract_ocr_text(image_path)
        
        # Construction du Mega-Prompt enrichi
        lines = [
            "🎯 CONTEXTE DE LA CAPTURE :",
            f"• Sujet : {topic_var.get()}",
            f"• Fenêtre source : {active_window_title}",
            f"• Date/Heure : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            ""
        ]
        
        if pins:
            lines.append("📍 QUESTIONS PAR REPÈRE NUMÉROTÉ :")
            for p in pins:
                num = p['num']
                comment = p['entry'].get().strip()
                if comment:
                    lines.append(f"• Repère ({num}) : {comment}")
                else:
                    lines.append(f"• Repère ({num}) : [Zone indiquée sur l'image]")
            lines.append("")
        
        if ocr_text:
            lines.append("📄 TEXTE EXTRAIT DE LA ZONE (OCR) :")
            lines.append("```")
            lines.append(ocr_text[:800]) # Limiter à 800 caractères max
            lines.append("```")
            lines.append("")

        lines.append("Peux-tu analyser l'image et apporter une réponse claire et structurée repère par repère (1, 2, 3...) ?")
        
        final_prompt[0] = "\n".join(lines)
        user_confirmed[0] = True
        root.destroy()

    btn_send = tk.Button(
        right_frame, text="🚀 ENVOYER À CLAUDE", bg="#a6e3a1", fg="#11111b",
        font=("Helvetica", 11, "bold"), relief=tk.FLAT, command=send_action, pady=8
    )
    btn_send.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

    def update_canvas():
        nonlocal tk_img, resized_display
        resized_display = edited_img.resize((display_w, display_h), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized_display)
        canvas.itemconfig(canvas_img_id, image=tk_img)

    def draw_pin_badge(orig_x, orig_y, num):
        radius = 14
        bbox = [orig_x - radius, orig_y - radius, orig_x + radius, orig_y + radius]
        draw.ellipse(bbox, fill=(243, 139, 168, 255), outline=(255, 255, 255, 255), width=2)
        
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
        except Exception:
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
            pin_item_frame, text=f"({num})", fg="#f38ba8", bg="#313244",
            font=("Helvetica", 10, "bold")
        )
        lbl_badge.pack(side=tk.LEFT, padx=(0, 4))

        entry_comment = tk.Entry(
            pin_item_frame, bg="#1e1e2e", fg="#cdd6f4", insertbackground="#cdd6f4",
            font=("Helvetica", 9), relief=tk.FLAT, width=22
        )
        entry_comment.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry_comment.focus_set()

        pins.append({'num': num, 'x': orig_x, 'y': orig_y, 'entry': entry_comment})

    def on_press(event):
        nonlocal start_x, start_y, rect_id
        start_x, start_y = event.x, event.y
        if mode.get() == "pin":
            add_pin(event.x, event.y)
        elif mode.get() == "mask":
            rect_id = canvas.create_rectangle(start_x, start_y, start_x, start_y, fill="#11111b", outline="#f38ba8", width=2)

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

    root.mainloop()
    return user_confirmed[0], final_prompt[0]

def main():
    parser = argparse.ArgumentParser(description="Click to Claude - Context, Pins & Auto-Paste")
    args = parser.parse_args()

    # 0. Capturer le contexte de l'application active AVANT de prendre le screenshot
    active_window_title = get_active_window_context()

    # 1. Capture d'écran
    captured = capture_screen()
    if not captured:
        print("Capture annulée.")
        return

    # 2. Interface d'Épingles, Sujet & Contexte
    confirmed, prompt_text = launch_pins_ui(TMP_IMG, active_window_title)
    if not confirmed:
        print("Envoi annulé par l'utilisateur.")
        return

    # 3. Copie de l'image
    copied = copy_image_to_clipboard(TMP_IMG)
    if not copied:
        send_notification("Click to Claude", "Erreur : xclip n'est pas disponible.")
        return

    # 4. Ouvrir/focaliser le mini-onglet Claude
    wid = open_or_focus_claude()

    # 5. Coller automatique de l'image ET du Mega-Prompt enrichi
    paste_in_claude(wid, prompt_text=prompt_text)
    send_notification("Click to Claude 🚀", "Capture & Contexte enrichi envoyés à Claude !")

if __name__ == "__main__":
    main()

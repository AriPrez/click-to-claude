"""Modern screenshot annotation editor for Click to Claude."""

import copy
import math
import tkinter as tk
from tkinter import filedialog, ttk

from PIL import Image, ImageDraw, ImageFont, ImageTk

COLORS = {
    "window": "#111318",
    "surface": "#171A21",
    "surface_raised": "#1D212A",
    "surface_hover": "#252A35",
    "canvas": "#0B0D11",
    "border": "#2B303B",
    "border_active": "#5B7FFF",
    "primary": "#5B7FFF",
    "primary_hover": "#7292FF",
    "cyan": "#38BDF8",
    "success": "#4ADE80",
    "danger": "#F87171",
    "warning": "#FBBF24",
    "text": "#F2F4F7",
    "muted": "#A5ADBA",
    "dim": "#737B89",
}

FONT_UI = "Helvetica"
FONT_MONO = "Courier"


class ScreenshotEditor:
    """Stateful screenshot editor with reversible vector annotations."""

    def __init__(
        self,
        image_path,
        active_window_title,
        build_prompt,
    ):
        self.image_path = image_path
        self.active_window_title = active_window_title
        self.build_prompt = build_prompt

        self.original_image = Image.open(image_path).convert("RGBA")
        self.operations = []
        self.undo_stack = []
        self.redo_stack = []
        self.selected_id = None
        self.preview_operation = None
        self.drag_start = None
        self.drag_before = None
        self.drag_changed = False
        self.drag_pin_offset = None
        self.next_id = 1

        self.confirmed = False
        self.final_prompt = ""
        self.pin_vars = {}
        self.pin_images = []
        self.tool_buttons = {}
        self.zoom = 1.0
        self.display_width = 1
        self.display_height = 1
        self.image_offset_x = 0
        self.image_offset_y = 0

        self.root = tk.Tk()
        self.root.title("Click to Claude — Screenshot editor")
        self.root.configure(bg=COLORS["window"])
        self.root.attributes("-topmost", True)
        self.root.minsize(980, 620)

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.window_width = min(1480, max(980, screen_width - 48))
        self.window_height = min(900, max(620, screen_height - 72))
        x_position = max(0, (screen_width - self.window_width) // 2)
        y_position = max(0, (screen_height - self.window_height) // 2)
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x_position}+{y_position}")

        center_width = max(440, self.window_width - 500)
        center_height = max(340, self.window_height - 190)
        image_width, image_height = self.original_image.size
        self.base_scale = min(
            center_width / image_width,
            center_height / image_height,
            1.0,
        )

        self.mode = tk.StringVar(value="pin")
        self.topic = tk.StringVar(value="Debug & code fix")
        self.include_title = tk.BooleanVar(value=True)
        self.status_text = tk.StringVar()
        self.privacy_text = tk.StringVar()
        self.zoom_text = tk.StringVar()

        self._configure_ttk()
        self._build_layout()
        self._bind_shortcuts()
        self._set_mode("pin")
        self._render()
        self._rebuild_pin_cards()
        self._update_status()

    def _configure_ttk(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "App.TCombobox",
            fieldbackground=COLORS["surface_raised"],
            background=COLORS["surface_raised"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["muted"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            padding=9,
            font=(FONT_UI, 9),
        )
        style.map(
            "App.TCombobox",
            fieldbackground=[("readonly", COLORS["surface_raised"])],
            foreground=[("readonly", COLORS["text"])],
            selectbackground=[("readonly", COLORS["surface_raised"])],
            selectforeground=[("readonly", COLORS["text"])],
        )
        style.configure(
            "App.Vertical.TScrollbar",
            background=COLORS["border"],
            troughcolor=COLORS["surface"],
            bordercolor=COLORS["surface"],
            arrowcolor=COLORS["muted"],
        )
        style.configure(
            "App.Horizontal.TScrollbar",
            background=COLORS["border"],
            troughcolor=COLORS["surface"],
            bordercolor=COLORS["surface"],
            arrowcolor=COLORS["muted"],
        )

    def _build_layout(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self._build_header()
        self._build_workspace()
        self._build_footer()

    def _build_header(self):
        header = tk.Frame(
            self.root,
            bg=COLORS["surface"],
            height=64,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        brand = tk.Frame(header, bg=COLORS["surface"])
        brand.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        tk.Label(
            brand,
            text="C",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=(FONT_UI, 15, "bold"),
            width=2,
        ).pack(side=tk.LEFT, padx=(0, 9))
        title_stack = tk.Frame(brand, bg=COLORS["surface"])
        title_stack.pack(side=tk.LEFT)
        tk.Label(
            title_stack,
            text="Click to Claude",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=(FONT_UI, 12, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_stack,
            text="Screenshot editor",
            bg=COLORS["surface"],
            fg=COLORS["dim"],
            font=(FONT_UI, 8),
        ).pack(anchor="w")

        context = tk.Frame(header, bg=COLORS["surface"])
        context.grid(row=0, column=1, padx=12, sticky="e")
        source_title = self.active_window_title.strip() or "Linux application"
        if len(source_title) > 28:
            source_title = f"{source_title[:25]}..."
        self._meta_label(context, source_title).pack(side=tk.LEFT, padx=7)
        self._meta_label(
            context,
            f"{self.original_image.width} × {self.original_image.height}",
            mono=True,
        ).pack(side=tk.LEFT, padx=7)
        self._meta_label(context, "●  Processed locally", accent=True).pack(
            side=tk.LEFT,
            padx=7,
        )

        actions = tk.Frame(header, bg=COLORS["surface"])
        actions.grid(row=0, column=2, padx=18, sticky="e")
        self.undo_button = self._button(
            actions,
            "Undo",
            self._undo,
            compact=True,
        )
        self.undo_button.pack(side=tk.LEFT, padx=4)
        self.redo_button = self._button(
            actions,
            "Redo",
            self._redo,
            compact=True,
        )
        self.redo_button.pack(side=tk.LEFT, padx=4)
        self._button(
            actions,
            "Reset",
            self._reset_all,
            compact=True,
            danger=True,
        ).pack(side=tk.LEFT, padx=(12, 0))

    def _build_workspace(self):
        workspace = tk.Frame(self.root, bg=COLORS["window"])
        workspace.grid(row=1, column=0, sticky="nsew", padx=14, pady=14)
        workspace.grid_rowconfigure(0, weight=1)
        workspace.grid_columnconfigure(1, weight=1)

        self._build_tool_rail(workspace)
        self._build_canvas_area(workspace)
        self._build_inspector(workspace)

    def _build_tool_rail(self, parent):
        rail = tk.Frame(
            parent,
            bg=COLORS["surface"],
            width=68,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        rail.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        rail.grid_propagate(False)

        tools = (
            ("select", "↖", "Select"),
            ("pin", "◎", "Pin"),
            ("arrow", "↗", "Arrow"),
            ("highlight", "▱", "Mark"),
            ("redact", "▰", "Hide"),
            ("pan", "✥", "Pan"),
        )
        for mode, icon, label in tools:
            button = tk.Button(
                rail,
                text=f"{icon}\n{label}",
                command=lambda selected=mode: self._set_mode(selected),
                bg=COLORS["surface"],
                fg=COLORS["muted"],
                activebackground=COLORS["surface_hover"],
                activeforeground=COLORS["text"],
                relief=tk.FLAT,
                bd=0,
                width=6,
                height=3,
                cursor="hand2",
                font=(FONT_UI, 9),
            )
            button.pack(fill=tk.X, padx=6, pady=(8 if mode == "select" else 2, 2))
            self.tool_buttons[mode] = button

        tk.Frame(rail, bg=COLORS["border"], height=1).pack(
            fill=tk.X,
            padx=14,
            pady=(12, 9),
        )
        tk.Label(
            rail,
            text="⌘Z  Undo",
            bg=COLORS["surface"],
            fg=COLORS["dim"],
            font=(FONT_UI, 7),
            justify=tk.CENTER,
        ).pack(pady=4)
        tk.Label(
            rail,
            text="Del  Remove",
            bg=COLORS["surface"],
            fg=COLORS["dim"],
            font=(FONT_UI, 7),
            justify=tk.CENTER,
        ).pack(pady=4)

    def _build_canvas_area(self, parent):
        center = tk.Frame(
            parent,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        center.grid(row=0, column=1, sticky="nsew")
        center.grid_rowconfigure(1, weight=1)
        center.grid_columnconfigure(0, weight=1)

        canvas_header = tk.Frame(center, bg=COLORS["surface_raised"], height=42)
        canvas_header.grid(row=0, column=0, sticky="ew")
        canvas_header.grid_propagate(False)
        canvas_header.grid_columnconfigure(1, weight=1)
        tk.Label(
            canvas_header,
            text="Screenshot",
            bg=COLORS["surface_raised"],
            fg=COLORS["text"],
            font=(FONT_UI, 10, "bold"),
        ).grid(row=0, column=0, padx=14, pady=12, sticky="w")
        tk.Label(
            canvas_header,
            text="Scroll to zoom  ·  Middle-drag to pan",
            bg=COLORS["surface_raised"],
            fg=COLORS["dim"],
            font=(FONT_UI, 8),
        ).grid(row=0, column=1, padx=14, sticky="e")

        viewport = tk.Frame(center, bg=COLORS["canvas"])
        viewport.grid(row=1, column=0, sticky="nsew")
        viewport.grid_rowconfigure(0, weight=1)
        viewport.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            viewport,
            bg=COLORS["canvas"],
            highlightthickness=0,
            cursor="crosshair",
        )
        vertical = ttk.Scrollbar(
            viewport,
            orient=tk.VERTICAL,
            command=self.canvas.yview,
            style="App.Vertical.TScrollbar",
        )
        horizontal = ttk.Scrollbar(
            viewport,
            orient=tk.HORIZONTAL,
            command=self.canvas.xview,
            style="App.Horizontal.TScrollbar",
        )
        self.canvas.configure(
            yscrollcommand=vertical.set,
            xscrollcommand=horizontal.set,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self.canvas_image_id = self.canvas.create_image(
            0,
            0,
            anchor=tk.NW,
        )

        zoom_bar = tk.Frame(center, bg=COLORS["surface_raised"], height=38)
        zoom_bar.grid(row=2, column=0, sticky="ew")
        zoom_bar.grid_propagate(False)
        self._button(
            zoom_bar,
            "-",
            lambda: self._set_zoom(self.zoom - 0.2),
            compact=True,
        ).pack(side=tk.LEFT, padx=(12, 4), pady=5)
        tk.Label(
            zoom_bar,
            textvariable=self.zoom_text,
            bg=COLORS["surface_raised"],
            fg=COLORS["text"],
            width=8,
            font=(FONT_MONO, 8, "bold"),
        ).pack(side=tk.LEFT)
        self._button(
            zoom_bar,
            "+",
            lambda: self._set_zoom(self.zoom + 0.2),
            compact=True,
        ).pack(side=tk.LEFT, padx=4, pady=5)
        self._button(
            zoom_bar,
            "Fit",
            lambda: self._set_zoom(1.0),
            compact=True,
        ).pack(side=tk.LEFT, padx=4, pady=5)

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<ButtonPress-2>", self._start_pan)
        self.canvas.bind("<B2-Motion>", self._drag_pan)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", lambda event: self._zoom_at_cursor(event, 0.1))
        self.canvas.bind("<Button-5>", lambda event: self._zoom_at_cursor(event, -0.1))
        self.canvas.bind("<Configure>", self._position_canvas_image)

    def _build_inspector(self, parent):
        inspector = tk.Frame(
            parent,
            bg=COLORS["surface"],
            width=372,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        inspector.grid(row=0, column=2, sticky="ns", padx=(10, 0))
        inspector.grid_propagate(False)
        inspector.grid_rowconfigure(2, weight=1)
        inspector.grid_columnconfigure(0, weight=1)

        heading = tk.Frame(inspector, bg=COLORS["surface_raised"], height=42)
        heading.grid(row=0, column=0, sticky="ew")
        heading.grid_propagate(False)
        tk.Label(
            heading,
            text="Questions",
            bg=COLORS["surface_raised"],
            fg=COLORS["text"],
            font=(FONT_UI, 10, "bold"),
        ).pack(side=tk.LEFT, padx=14, pady=12)
        self.pin_count_badge = tk.Label(
            heading,
            text="0 pins",
            bg=COLORS["surface_hover"],
            fg=COLORS["muted"],
            font=(FONT_UI, 8),
            padx=8,
            pady=3,
        )
        self.pin_count_badge.pack(side=tk.RIGHT, padx=12)

        prompt_panel = tk.Frame(inspector, bg=COLORS["surface"], padx=12, pady=10)
        prompt_panel.grid(row=1, column=0, sticky="ew")
        tk.Label(
            prompt_panel,
            text="Task",
            bg=COLORS["surface"],
            fg=COLORS["dim"],
            font=(FONT_UI, 8, "bold"),
        ).pack(anchor="w")
        topics = (
            "Debug & code fix",
            "Refactoring & optimization",
            "UI design & layout",
            "Accessibility review",
            "Text explanation & documentation",
            "Terminal & log analysis",
            "Medical diagram explanation",
            "Scientific figure analysis",
            "General question",
        )
        ttk.Combobox(
            prompt_panel,
            textvariable=self.topic,
            values=topics,
            state="readonly",
            style="App.TCombobox",
        ).pack(fill=tk.X, pady=(4, 10))

        tk.Label(
            prompt_panel,
            text="Instructions",
            bg=COLORS["surface"],
            fg=COLORS["dim"],
            font=(FONT_UI, 8, "bold"),
        ).pack(anchor="w")
        self.general_request = tk.Text(
            prompt_panel,
            height=3,
            wrap=tk.WORD,
            bg=COLORS["surface_raised"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            selectbackground=COLORS["primary"],
            relief=tk.FLAT,
            bd=0,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["primary"],
            highlightthickness=1,
            padx=9,
            pady=8,
            font=(FONT_UI, 9),
        )
        self.general_request.pack(fill=tk.X, pady=(4, 0))

        pins_panel = tk.Frame(inspector, bg=COLORS["surface"])
        pins_panel.grid(row=2, column=0, sticky="nsew", padx=12)
        pins_panel.grid_rowconfigure(1, weight=1)
        pins_panel.grid_columnconfigure(0, weight=1)
        tk.Label(
            pins_panel,
            text="Pinned questions",
            bg=COLORS["surface"],
            fg=COLORS["dim"],
            font=(FONT_UI, 8, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(4, 7))

        cards_holder = tk.Frame(pins_panel, bg=COLORS["surface"])
        cards_holder.grid(row=1, column=0, sticky="nsew")
        cards_holder.grid_rowconfigure(0, weight=1)
        cards_holder.grid_columnconfigure(0, weight=1)
        self.cards_canvas = tk.Canvas(
            cards_holder,
            bg=COLORS["surface"],
            highlightthickness=0,
        )
        cards_scroll = ttk.Scrollbar(
            cards_holder,
            orient=tk.VERTICAL,
            command=self.cards_canvas.yview,
            style="App.Vertical.TScrollbar",
        )
        self.cards_frame = tk.Frame(self.cards_canvas, bg=COLORS["surface"])
        self.cards_window_id = self.cards_canvas.create_window(
            (0, 0),
            window=self.cards_frame,
            anchor=tk.NW,
        )
        self.cards_canvas.configure(yscrollcommand=cards_scroll.set)
        self.cards_frame.bind(
            "<Configure>",
            lambda _event: self.cards_canvas.configure(scrollregion=self.cards_canvas.bbox("all")),
        )
        self.cards_canvas.bind(
            "<Configure>",
            lambda event: self.cards_canvas.itemconfigure(
                self.cards_window_id,
                width=event.width,
            ),
        )
        self.cards_canvas.grid(row=0, column=0, sticky="nsew")
        cards_scroll.grid(row=0, column=1, sticky="ns")

        privacy = tk.Frame(inspector, bg=COLORS["surface_raised"], padx=12, pady=10)
        privacy.grid(row=3, column=0, sticky="ew")
        self._checkbutton(
            privacy,
            "Include source window title",
            self.include_title,
        ).pack(anchor="w")
        self.include_title.trace_add("write", lambda *_args: self._update_status())

    def _build_footer(self):
        footer = tk.Frame(
            self.root,
            bg=COLORS["surface"],
            height=64,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)
        footer.grid_columnconfigure(1, weight=1)

        tk.Label(
            footer,
            textvariable=self.status_text,
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=(FONT_UI, 8),
        ).grid(row=0, column=0, padx=18, pady=20, sticky="w")
        tk.Label(
            footer,
            textvariable=self.privacy_text,
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=(FONT_UI, 8),
        ).grid(row=0, column=1, padx=12, sticky="e")

        send = tk.Button(
            footer,
            text="Review",
            command=self._prepare_send,
            bg=COLORS["primary"],
            fg=COLORS["text"],
            activebackground=COLORS["primary_hover"],
            activeforeground=COLORS["text"],
            relief=tk.FLAT,
            bd=0,
            padx=24,
            pady=11,
            cursor="hand2",
            font=(FONT_UI, 10, "bold"),
        )
        self._button(
            footer,
            "Export",
            self._export_png,
        ).grid(row=0, column=2, padx=(8, 0), pady=10)
        send.grid(row=0, column=3, padx=16, pady=10)
        self._add_hover(send, COLORS["primary"], COLORS["primary_hover"])

    def _button(self, parent, text, command, compact=False, danger=False):
        base = COLORS["surface_raised"]
        hover = COLORS["surface_hover"]
        foreground = COLORS["danger"] if danger else COLORS["muted"]
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=base,
            fg=foreground,
            activebackground=hover,
            activeforeground=COLORS["text"],
            relief=tk.FLAT,
            bd=0,
            padx=9 if compact else 14,
            pady=4 if compact else 8,
            cursor="hand2",
            font=(FONT_UI, 8, "bold"),
        )
        self._add_hover(button, base, hover)
        return button

    def _meta_label(self, parent, text, mono=False, accent=False):
        return tk.Label(
            parent,
            text=text,
            bg=COLORS["surface"],
            fg=COLORS["success"] if accent else COLORS["dim"],
            font=(FONT_MONO if mono else FONT_UI, 8),
        )

    def _checkbutton(self, parent, text, variable):
        return tk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            bg=COLORS["surface_raised"],
            fg=COLORS["text"],
            selectcolor=COLORS["surface_raised"],
            activebackground=COLORS["surface_raised"],
            activeforeground=COLORS["text"],
            indicatoron=True,
            anchor="w",
            relief=tk.FLAT,
            offrelief=tk.FLAT,
            overrelief=tk.FLAT,
            padx=2,
            pady=4,
            font=(FONT_UI, 8),
            cursor="hand2",
        )

    @staticmethod
    def _add_hover(widget, base_color, hover_color):
        widget.bind("<Enter>", lambda _event: widget.configure(bg=hover_color))
        widget.bind("<Leave>", lambda _event: widget.configure(bg=base_color))

    def _set_mode(self, mode):
        self.mode.set(mode)
        cursors = {
            "select": "arrow",
            "pin": "crosshair",
            "arrow": "crosshair",
            "highlight": "crosshair",
            "redact": "crosshair",
            "pan": "fleur",
        }
        self.canvas.configure(cursor=cursors.get(mode, "crosshair"))
        for name, button in self.tool_buttons.items():
            active = name == mode
            button.configure(
                bg=COLORS["surface_hover"] if active else COLORS["surface"],
                fg=COLORS["text"] if active else COLORS["muted"],
                highlightbackground=COLORS["primary"] if active else COLORS["surface"],
                highlightthickness=1 if active else 0,
            )
        self._update_status()

    def _bind_shortcuts(self):
        self.root.bind("<Escape>", lambda _event: self.root.destroy())
        self.root.bind("<Control-z>", lambda _event: self._undo())
        self.root.bind("<Control-y>", lambda _event: self._redo())
        self.root.bind("<Control-Shift-Z>", lambda _event: self._redo())
        self.root.bind("<Control-Return>", lambda _event: self._prepare_send())
        self.root.bind("<Control-s>", lambda _event: self._export_png())
        self.root.bind("<Delete>", self._delete_key)
        self.root.bind("<BackSpace>", self._delete_key)
        self.root.bind("v", lambda _event: self._tool_shortcut("select"))
        self.root.bind("p", lambda _event: self._tool_shortcut("pin"))
        self.root.bind("a", lambda _event: self._tool_shortcut("arrow"))
        self.root.bind("h", lambda _event: self._tool_shortcut("highlight"))
        self.root.bind("r", lambda _event: self._tool_shortcut("redact"))

    def _tool_shortcut(self, mode):
        focused = self.root.focus_get()
        if focused and focused.winfo_class() in {"Entry", "Text", "TEntry"}:
            return
        self._set_mode(mode)

    def _delete_key(self, _event=None):
        focused = self.root.focus_get()
        if focused and focused.winfo_class() in {"Entry", "Text", "TEntry"}:
            return
        if self.selected_id is not None:
            self._delete_operation(self.selected_id)

    def _sync_comments(self):
        for operation in self.operations:
            if operation["type"] == "pin" and operation["id"] in self.pin_vars:
                operation["comment"] = self.pin_vars[operation["id"]].get()

    def _push_history(self):
        self._sync_comments()
        self.undo_stack.append(copy.deepcopy(self.operations))
        if len(self.undo_stack) > 60:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def _undo(self):
        if not self.undo_stack:
            return
        self._sync_comments()
        self.redo_stack.append(copy.deepcopy(self.operations))
        self.operations = self.undo_stack.pop()
        self.selected_id = None
        self._after_state_change()

    def _redo(self):
        if not self.redo_stack:
            return
        self._sync_comments()
        self.undo_stack.append(copy.deepcopy(self.operations))
        self.operations = self.redo_stack.pop()
        self.selected_id = None
        self._after_state_change()

    def _reset_all(self):
        if not self.operations:
            return
        self._push_history()
        self.operations = []
        self.selected_id = None
        self._after_state_change()

    def _after_state_change(self):
        maximum_id = max((operation["id"] for operation in self.operations), default=0)
        self.next_id = max(self.next_id, maximum_id + 1)
        self._rebuild_pin_cards()
        self._render()
        self._update_status()

    def _new_operation(self, operation_type, **coordinates):
        operation = {
            "id": self.next_id,
            "type": operation_type,
            **coordinates,
        }
        self.next_id += 1
        if operation_type == "pin":
            operation["comment"] = ""
        return operation

    def _canvas_coordinates(self, event):
        scale = self.base_scale * self.zoom
        x_position = (self.canvas.canvasx(event.x) - self.image_offset_x) / scale
        y_position = (self.canvas.canvasy(event.y) - self.image_offset_y) / scale
        return (
            min(max(0, x_position), self.original_image.width),
            min(max(0, y_position), self.original_image.height),
        )

    def _on_press(self, event):
        if self.mode.get() == "pan":
            self._start_pan(event)
            return

        x_position, y_position = self._canvas_coordinates(event)
        mode = self.mode.get()
        if mode == "pin":
            self._push_history()
            operation = self._new_operation(
                "pin",
                x=x_position,
                y=y_position,
            )
            self.operations.append(operation)
            self.selected_id = operation["id"]
            self._after_state_change()
            return

        if mode == "select":
            self.selected_id = self._find_operation(x_position, y_position)
            self.drag_start = (x_position, y_position)
            self.drag_before = copy.deepcopy(self.operations)
            self.drag_changed = False
            selected = self._operation_by_id(self.selected_id)
            self.drag_pin_offset = (
                (
                    selected["x"] - x_position,
                    selected["y"] - y_position,
                )
                if selected and selected["type"] == "pin"
                else None
            )
            self._rebuild_pin_cards()
            self._render()
            return

        self.drag_start = (x_position, y_position)
        self.preview_operation = self._new_operation(
            mode,
            x1=x_position,
            y1=y_position,
            x2=x_position,
            y2=y_position,
        )
        self._render()

    def _on_drag(self, event):
        if self.mode.get() == "pan":
            self._drag_pan(event)
            return
        if not self.drag_start:
            return

        x_position, y_position = self._canvas_coordinates(event)
        if self.mode.get() == "select" and self.selected_id is not None:
            operation = self._operation_by_id(self.selected_id)
            if operation and operation["type"] == "pin":
                offset_x, offset_y = self.drag_pin_offset or (0, 0)
                operation["x"] = min(
                    max(0, x_position + offset_x),
                    self.original_image.width,
                )
                operation["y"] = min(
                    max(0, y_position + offset_y),
                    self.original_image.height,
                )
                self.drag_changed = True
                self._render()
            return

        if self.preview_operation:
            self.preview_operation["x2"] = x_position
            self.preview_operation["y2"] = y_position
            self._render()

    def _on_release(self, event):
        if self.mode.get() == "pan":
            return
        if self.mode.get() == "select":
            if self.drag_changed and self.drag_before is not None:
                self.undo_stack.append(self.drag_before)
                self.redo_stack.clear()
                self._after_state_change()
            self.drag_start = None
            self.drag_before = None
            self.drag_changed = False
            self.drag_pin_offset = None
            return

        if not self.preview_operation or not self.drag_start:
            return
        x_position, y_position = self._canvas_coordinates(event)
        self.preview_operation["x2"] = x_position
        self.preview_operation["y2"] = y_position
        distance = math.hypot(
            self.preview_operation["x2"] - self.preview_operation["x1"],
            self.preview_operation["y2"] - self.preview_operation["y1"],
        )
        if distance >= max(3, 5 / self.base_scale):
            self._push_history()
            self.operations.append(self.preview_operation)
            self.selected_id = self.preview_operation["id"]
        self.preview_operation = None
        self.drag_start = None
        self._after_state_change()

    def _start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def _drag_pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _on_wheel(self, event):
        direction = 1 if event.delta > 0 else -1
        self._zoom_at_cursor(event, direction * 0.1)

    def _set_zoom(self, zoom):
        self.zoom = min(8.0, max(0.5, round(zoom, 2)))
        self._render()
        self._update_status()

    def _zoom_at_cursor(self, event, delta):
        """Zoom while keeping the image point under the cursor stable."""
        old_scale = self.base_scale * self.zoom
        if old_scale <= 0:
            self._set_zoom(self.zoom + delta)
            return

        image_x = (self.canvas.canvasx(event.x) - self.image_offset_x) / old_scale
        image_y = (self.canvas.canvasy(event.y) - self.image_offset_y) / old_scale
        self._set_zoom(self.zoom + delta)
        self.root.update_idletasks()

        new_scale = self.base_scale * self.zoom
        target_x = self.image_offset_x + image_x * new_scale - event.x
        target_y = self.image_offset_y + image_y * new_scale - event.y
        scroll_width = max(self.canvas.winfo_width(), self.display_width)
        scroll_height = max(self.canvas.winfo_height(), self.display_height)
        if scroll_width > self.canvas.winfo_width():
            self.canvas.xview_moveto(max(0, target_x) / scroll_width)
        if scroll_height > self.canvas.winfo_height():
            self.canvas.yview_moveto(max(0, target_y) / scroll_height)

    def _operation_by_id(self, operation_id):
        return next(
            (operation for operation in self.operations if operation["id"] == operation_id),
            None,
        )

    def _find_operation(self, x_position, y_position):
        hit_radius = max(18, 20 / self.base_scale)
        for operation in reversed(self.operations):
            if operation["type"] == "pin":
                geometry = self._pin_geometry(
                    operation,
                    self.original_image.size,
                    max(self.base_scale, 0.2),
                )
                anchor_distance = math.hypot(
                    operation["x"] - x_position,
                    operation["y"] - y_position,
                )
                badge_distance = math.hypot(
                    geometry["badge_x"] - x_position,
                    geometry["badge_y"] - y_position,
                )
                if anchor_distance <= hit_radius or badge_distance <= geometry["radius"] + 4:
                    return operation["id"]
            elif operation["type"] in {"redact", "highlight"}:
                left, right = sorted((operation["x1"], operation["x2"]))
                top, bottom = sorted((operation["y1"], operation["y2"]))
                if left <= x_position <= right and top <= y_position <= bottom:
                    return operation["id"]
            elif operation["type"] == "arrow":
                distance = self._distance_to_segment(
                    x_position,
                    y_position,
                    operation["x1"],
                    operation["y1"],
                    operation["x2"],
                    operation["y2"],
                )
                if distance <= hit_radius:
                    return operation["id"]
        return None

    @staticmethod
    def _distance_to_segment(px, py, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(px - x1, py - y1)
        projection = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        projection = min(1, max(0, projection))
        closest_x = x1 + projection * dx
        closest_y = y1 + projection * dy
        return math.hypot(px - closest_x, py - closest_y)

    def _delete_operation(self, operation_id):
        if not self._operation_by_id(operation_id):
            return
        self._push_history()
        self.operations = [
            operation for operation in self.operations if operation["id"] != operation_id
        ]
        if self.selected_id == operation_id:
            self.selected_id = None
        self._after_state_change()

    def _move_pin(self, operation_id, direction):
        pin_indices = [
            index for index, operation in enumerate(self.operations) if operation["type"] == "pin"
        ]
        current_position = next(
            (
                position
                for position, index in enumerate(pin_indices)
                if self.operations[index]["id"] == operation_id
            ),
            None,
        )
        if current_position is None:
            return
        target_position = current_position + direction
        if not 0 <= target_position < len(pin_indices):
            return
        self._push_history()
        current_index = pin_indices[current_position]
        target_index = pin_indices[target_position]
        self.operations[current_index], self.operations[target_index] = (
            self.operations[target_index],
            self.operations[current_index],
        )
        self._after_state_change()

    def _render(self):
        rendered = self._render_image(show_selection=True)
        scale = self.base_scale * self.zoom
        display_width = max(1, int(rendered.width * scale))
        display_height = max(1, int(rendered.height * scale))
        resized = rendered.resize(
            (display_width, display_height),
            Image.Resampling.LANCZOS,
        )
        self.tk_image = ImageTk.PhotoImage(resized)
        self.canvas.itemconfigure(self.canvas_image_id, image=self.tk_image)
        self.display_width = display_width
        self.display_height = display_height
        self._position_canvas_image()
        self.zoom_text.set(f"{round(scale * 100)}%")

    def _position_canvas_image(self, _event=None):
        viewport_width = max(1, self.canvas.winfo_width())
        viewport_height = max(1, self.canvas.winfo_height())
        self.image_offset_x = max(0, (viewport_width - self.display_width) // 2)
        self.image_offset_y = max(0, (viewport_height - self.display_height) // 2)
        self.canvas.coords(
            self.canvas_image_id,
            self.image_offset_x,
            self.image_offset_y,
        )
        self.canvas.configure(
            scrollregion=(
                0,
                0,
                max(viewport_width, self.display_width),
                max(viewport_height, self.display_height),
            )
        )

    def _render_image(self, show_selection=False):
        image = self.original_image.copy()
        operations = list(self.operations)
        if self.preview_operation:
            operations.append(self.preview_operation)

        for operation in (item for item in operations if item["type"] != "pin"):
            annotation_scale = max(self.base_scale, 0.2)
            line_width = max(3, int(4 / annotation_scale))
            operation_type = operation["type"]

            if operation_type == "redact":
                draw = ImageDraw.Draw(image)
                box = self._normalized_box(operation)
                draw.rounded_rectangle(
                    box,
                    radius=max(4, int(6 / annotation_scale)),
                    fill=(8, 12, 20, 255),
                    outline=(255, 92, 122, 255),
                    width=line_width,
                )
            elif operation_type == "highlight":
                overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                overlay_draw.rounded_rectangle(
                    self._normalized_box(operation),
                    radius=max(4, int(6 / annotation_scale)),
                    fill=(250, 204, 21, 72),
                    outline=(250, 204, 21, 210),
                    width=line_width,
                )
                image = Image.alpha_composite(image, overlay)
            elif operation_type == "arrow":
                self._draw_arrow(image, operation, line_width)

        pins = [item for item in operations if item["type"] == "pin"]
        for pin_number, operation in enumerate(pins, start=1):
            self._draw_pin(image, operation, pin_number)

        if show_selection and self.selected_id is not None:
            selected = self._operation_by_id(self.selected_id)
            if selected:
                self._draw_selection(image, selected)
        return image

    @staticmethod
    def _normalized_box(operation):
        return (
            min(operation["x1"], operation["x2"]),
            min(operation["y1"], operation["y2"]),
            max(operation["x1"], operation["x2"]),
            max(operation["y1"], operation["y2"]),
        )

    def _draw_pin(self, image, operation, number):
        annotation_scale = max(self.base_scale, 0.2)
        geometry = self._pin_geometry(operation, image.size, annotation_scale)
        radius = geometry["radius"]
        badge_x = geometry["badge_x"]
        badge_y = geometry["badge_y"]
        anchor_x = operation["x"]
        anchor_y = operation["y"]
        line_width = max(2, int(2 / annotation_scale))
        draw = ImageDraw.Draw(image)

        vector_x = badge_x - anchor_x
        vector_y = badge_y - anchor_y
        distance = max(1, math.hypot(vector_x, vector_y))
        unit_x = vector_x / distance
        unit_y = vector_y / distance
        target_radius = max(4, int(4 / annotation_scale))
        draw.line(
            (
                anchor_x + unit_x * target_radius,
                anchor_y + unit_y * target_radius,
                badge_x - unit_x * radius,
                badge_y - unit_y * radius,
            ),
            fill=(34, 211, 238, 255),
            width=line_width,
        )

        crosshair_extent = target_radius * 2.4
        crosshair_gap = target_radius * 1.3
        for start, end in (
            (
                (anchor_x - crosshair_extent, anchor_y),
                (anchor_x - crosshair_gap, anchor_y),
            ),
            (
                (anchor_x + crosshair_gap, anchor_y),
                (anchor_x + crosshair_extent, anchor_y),
            ),
            (
                (anchor_x, anchor_y - crosshair_extent),
                (anchor_x, anchor_y - crosshair_gap),
            ),
            (
                (anchor_x, anchor_y + crosshair_gap),
                (anchor_x, anchor_y + crosshair_extent),
            ),
        ):
            draw.line((start, end), fill=(34, 211, 238, 255), width=line_width)
        draw.ellipse(
            (
                anchor_x - target_radius,
                anchor_y - target_radius,
                anchor_x + target_radius,
                anchor_y + target_radius,
            ),
            outline=(245, 247, 255, 255),
            width=line_width,
        )

        draw.ellipse(
            (
                badge_x - radius,
                badge_y - radius,
                badge_x + radius,
                badge_y + radius,
            ),
            fill=(124, 92, 255, 255),
            outline=(245, 247, 255, 255),
            width=line_width,
        )
        try:
            font = ImageFont.truetype(
                "DejaVuSans-Bold.ttf",
                max(17, int(17 / annotation_scale)),
            )
        except OSError:
            font = ImageFont.load_default()
        draw.text(
            (badge_x, badge_y),
            str(number),
            fill=(245, 247, 255, 255),
            anchor="mm",
            font=font,
        )

    @staticmethod
    def _pin_geometry(operation, image_size, annotation_scale):
        """Place the numbered badge away from its exact target."""
        image_width, image_height = image_size
        radius = max(14, int(14 / annotation_scale))
        offset = radius * 1.7
        anchor_x = operation["x"]
        anchor_y = operation["y"]

        badge_x = anchor_x + offset
        if badge_x + radius > image_width:
            badge_x = anchor_x - offset
        badge_y = anchor_y - offset
        if badge_y - radius < 0:
            badge_y = anchor_y + offset

        badge_x = min(max(radius, badge_x), max(radius, image_width - radius))
        badge_y = min(max(radius, badge_y), max(radius, image_height - radius))
        return {
            "badge_x": badge_x,
            "badge_y": badge_y,
            "radius": radius,
        }

    def _draw_arrow(self, image, operation, width):
        draw = ImageDraw.Draw(image)
        start = (operation["x1"], operation["y1"])
        end = (operation["x2"], operation["y2"])
        draw.line((start, end), fill=(34, 211, 238, 255), width=width)
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        head_length = width * 4.5
        left = (
            end[0] - head_length * math.cos(angle - math.pi / 6),
            end[1] - head_length * math.sin(angle - math.pi / 6),
        )
        right = (
            end[0] - head_length * math.cos(angle + math.pi / 6),
            end[1] - head_length * math.sin(angle + math.pi / 6),
        )
        draw.polygon((end, left, right), fill=(34, 211, 238, 255))

    def _draw_selection(self, image, operation):
        draw = ImageDraw.Draw(image)
        annotation_scale = max(self.base_scale, 0.2)
        width = max(2, int(2 / annotation_scale))
        padding = max(8, int(8 / annotation_scale))
        if operation["type"] == "pin":
            geometry = self._pin_geometry(
                operation,
                image.size,
                annotation_scale,
            )
            radius = geometry["radius"]
            box = (
                min(operation["x"], geometry["badge_x"]) - radius - padding,
                min(operation["y"], geometry["badge_y"]) - radius - padding,
                max(operation["x"], geometry["badge_x"]) + radius + padding,
                max(operation["y"], geometry["badge_y"]) + radius + padding,
            )
        else:
            left, top, right, bottom = self._normalized_box(operation)
            box = (
                left - padding,
                top - padding,
                right + padding,
                bottom + padding,
            )
        draw.rectangle(box, outline=(34, 211, 238, 255), width=width)

    def _rebuild_pin_cards(self):
        self._sync_comments()
        for child in self.cards_frame.winfo_children():
            child.destroy()
        self.pin_vars.clear()
        self.pin_images.clear()

        pins = [operation for operation in self.operations if operation["type"] == "pin"]
        self.pin_count_badge.configure(text=f"{len(pins)} pin{'s' if len(pins) != 1 else ''}")
        if not pins:
            empty = tk.Frame(
                self.cards_frame,
                bg=COLORS["surface_raised"],
                padx=12,
                pady=18,
            )
            empty.pack(fill=tk.X, pady=(0, 8))
            tk.Label(
                empty,
                text="◎",
                bg=COLORS["surface_raised"],
                fg=COLORS["primary"],
                font=(FONT_UI, 20),
            ).pack()
            tk.Label(
                empty,
                text="Place a pin to ask about a precise detail",
                bg=COLORS["surface_raised"],
                fg=COLORS["muted"],
                wraplength=250,
                justify=tk.CENTER,
                font=(FONT_UI, 9),
            ).pack(pady=(4, 0))
            return

        for number, operation in enumerate(pins, start=1):
            selected = operation["id"] == self.selected_id
            background = COLORS["surface_hover"] if selected else COLORS["surface_raised"]
            card = tk.Frame(
                self.cards_frame,
                bg=background,
                highlightbackground=(COLORS["primary"] if selected else COLORS["border"]),
                highlightthickness=1,
                padx=8,
                pady=8,
            )
            card.pack(fill=tk.X, pady=(0, 8))
            card.grid_columnconfigure(0, weight=1)
            card.bind(
                "<Button-1>",
                lambda _event, operation_id=operation["id"]: self._select_operation(operation_id),
            )

            title = tk.Frame(card, bg=background)
            title.grid(row=0, column=0, sticky="ew")
            tk.Label(
                title,
                text=f"Pin {number}",
                bg=background,
                fg=COLORS["text"],
                font=(FONT_UI, 9, "bold"),
            ).pack(side=tk.LEFT)
            tk.Label(
                title,
                text=f"x {round(operation['x'])}  y {round(operation['y'])}",
                bg=background,
                fg=COLORS["dim"],
                font=(FONT_MONO, 7),
            ).pack(side=tk.LEFT, padx=(8, 0))
            for label, direction in (("Up", -1), ("Dn", 1)):
                tk.Button(
                    title,
                    text=label,
                    command=lambda operation_id=operation["id"], move=direction: self._move_pin(
                        operation_id, move
                    ),
                    bg=background,
                    fg=COLORS["muted"],
                    activebackground=COLORS["surface_hover"],
                    activeforeground=COLORS["text"],
                    relief=tk.FLAT,
                    bd=0,
                    cursor="hand2",
                    font=(FONT_UI, 8, "bold"),
                ).pack(side=tk.RIGHT)
            tk.Button(
                title,
                text="×",
                command=lambda operation_id=operation["id"]: self._delete_operation(operation_id),
                bg=background,
                fg=COLORS["danger"],
                activebackground=COLORS["surface_hover"],
                activeforeground=COLORS["danger"],
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                font=(FONT_UI, 10, "bold"),
            ).pack(side=tk.RIGHT, padx=(4, 0))

            lens_strip = tk.Frame(card, bg=background)
            lens_strip.grid(row=1, column=0, sticky="ew", pady=(7, 0))
            for lens_name, is_context in (("Close-up", False), ("Context", True)):
                lens = tk.Frame(lens_strip, bg=background)
                lens.pack(
                    side=tk.LEFT,
                    fill=tk.X,
                    expand=True,
                    padx=((0, 4) if not is_context else (4, 0)),
                )
                tk.Label(
                    lens,
                    text=lens_name,
                    bg=background,
                    fg=COLORS["muted"],
                    font=(FONT_UI, 7, "bold"),
                ).pack(anchor="w", pady=(0, 3))
                thumbnail = self._pin_thumbnail(operation, context=is_context)
                self.pin_images.append(thumbnail)
                thumbnail_label = tk.Label(
                    lens,
                    image=thumbnail,
                    bg=background,
                    highlightbackground=COLORS["border"],
                    highlightthickness=1,
                )
                thumbnail_label.pack(fill=tk.X)
                thumbnail_label.bind(
                    "<Button-1>",
                    lambda _event, operation_id=operation["id"]: self._select_operation(
                        operation_id
                    ),
                )

            variable = tk.StringVar(value=operation.get("comment", ""))
            self.pin_vars[operation["id"]] = variable

            def update_comment(*_args, item=operation, text_variable=variable):
                item["comment"] = text_variable.get()

            variable.trace_add("write", update_comment)
            tk.Label(
                card,
                text="Question",
                bg=background,
                fg=COLORS["muted"],
                font=(FONT_UI, 7, "bold"),
            ).grid(row=2, column=0, sticky="w", pady=(8, 3))
            entry = tk.Entry(
                card,
                textvariable=variable,
                bg=COLORS["surface"],
                fg=COLORS["text"],
                insertbackground=COLORS["text"],
                selectbackground=COLORS["primary"],
                relief=tk.FLAT,
                bd=0,
                highlightbackground=COLORS["border"],
                highlightcolor=COLORS["primary"],
                highlightthickness=1,
                font=(FONT_UI, 8),
            )
            entry.grid(row=3, column=0, sticky="ew", ipady=6)

    @staticmethod
    def _pin_crop_box(operation, image_size, context=False):
        image_width, image_height = image_size
        if context:
            half_width = max(110, int(image_width * 0.14))
            half_height = max(72, int(image_height * 0.11))
        else:
            half_width = max(44, int(image_width * 0.04))
            half_height = max(28, int(image_height * 0.035))
        return (
            max(0, int(operation["x"] - half_width)),
            max(0, int(operation["y"] - half_height)),
            min(image_width, int(operation["x"] + half_width)),
            min(image_height, int(operation["y"] + half_height)),
        )

    def _pin_thumbnail(self, operation, context=False):
        left, top, right, bottom = self._pin_crop_box(
            operation,
            self.original_image.size,
            context=context,
        )
        crop = self.original_image.crop((left, top, right, bottom))
        crop.thumbnail((124, 64), Image.Resampling.LANCZOS)
        background = Image.new("RGBA", (124, 64), (17, 19, 24, 255))
        x_position = (124 - crop.width) // 2
        y_position = (64 - crop.height) // 2
        background.alpha_composite(crop, (x_position, y_position))
        draw = ImageDraw.Draw(background)
        center_x = 62
        center_y = 32
        draw.ellipse(
            (center_x - 4, center_y - 4, center_x + 4, center_y + 4),
            outline=(245, 247, 255, 255),
            width=1,
        )
        draw.line(
            (center_x - 10, center_y, center_x - 5, center_y),
            fill=(34, 211, 238, 255),
        )
        draw.line(
            (center_x + 5, center_y, center_x + 10, center_y),
            fill=(34, 211, 238, 255),
        )
        draw.line(
            (center_x, center_y - 10, center_x, center_y - 5),
            fill=(34, 211, 238, 255),
        )
        draw.line(
            (center_x, center_y + 5, center_x, center_y + 10),
            fill=(34, 211, 238, 255),
        )
        return ImageTk.PhotoImage(background)

    def _select_operation(self, operation_id):
        self.selected_id = operation_id
        self._set_mode("select")
        self._rebuild_pin_cards()
        self._render()

    def _update_status(self):
        pins = sum(operation["type"] == "pin" for operation in self.operations)
        redactions = sum(operation["type"] == "redact" for operation in self.operations)
        annotations = len(self.operations)
        if annotations:
            self.status_text.set(
                f"{annotations} annotation{'s' if annotations != 1 else ''}"
                f"  ·  {pins} pin{'s' if pins != 1 else ''}"
                f"  ·  {redactions} hidden area{'s' if redactions != 1 else ''}"
            )
        else:
            self.status_text.set("No annotations yet")
        self.privacy_text.set(
            f"Source title {'included' if self.include_title.get() else 'hidden'}"
            f"  ·  {self.mode.get().capitalize()} tool"
        )
        if hasattr(self, "undo_button"):
            self.undo_button.configure(state=tk.NORMAL if self.undo_stack else tk.DISABLED)
            self.redo_button.configure(state=tk.NORMAL if self.redo_stack else tk.DISABLED)

    def _prepare_send(self):
        self._sync_comments()
        export_image = self._render_image(show_selection=False)
        export_image.convert("RGB").save(self.image_path, "PNG")
        pin_comments = [
            operation.get("comment", "")
            for operation in self.operations
            if operation["type"] == "pin"
        ]
        self.final_prompt = self.build_prompt(
            topic=self.topic.get(),
            pin_comments=pin_comments,
            general_request=self.general_request.get("1.0", tk.END),
            source_window=(self.active_window_title if self.include_title.get() else ""),
        )
        if not self._confirm_prompt(self.final_prompt):
            return
        self.confirmed = True
        self.root.destroy()

    def _export_png(self):
        destination = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export annotated screenshot",
            defaultextension=".png",
            filetypes=(("PNG image", "*.png"),),
            initialfile="click-to-claude.png",
        )
        if not destination:
            return
        self._render_image(show_selection=False).convert("RGB").save(
            destination,
            "PNG",
        )
        previous_status = self.status_text.get()
        self.status_text.set("PNG exported")
        self.root.after(2200, lambda: self.status_text.set(previous_status))

    def _confirm_prompt(self, prompt):
        approved = [False]
        preview = tk.Toplevel(self.root)
        preview.title("Review before pasting")
        preview.configure(bg=COLORS["window"])
        preview.transient(self.root)
        preview.resizable(True, True)

        screen_width = preview.winfo_screenwidth()
        screen_height = preview.winfo_screenheight()
        width = min(760, max(500, screen_width - 80))
        height = min(600, max(400, screen_height - 80))
        x_position = max(0, (screen_width - width) // 2)
        y_position = max(0, (screen_height - height) // 2)
        preview.geometry(f"{width}x{height}+{x_position}+{y_position}")
        preview.grid_rowconfigure(1, weight=1)
        preview.grid_columnconfigure(0, weight=1)

        header = tk.Frame(preview, bg=COLORS["surface"], padx=18, pady=14)
        header.grid(row=0, column=0, sticky="ew")
        tk.Label(
            header,
            text="Review before pasting",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=(FONT_UI, 13, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Check the request below. You stay in control of what gets pasted.",
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=(FONT_UI, 9),
        ).pack(anchor="w", pady=(5, 0))

        prompt_preview = tk.Text(
            preview,
            wrap=tk.WORD,
            bg=COLORS["surface_raised"],
            fg=COLORS["text"],
            insertbackground=COLORS["cyan"],
            selectbackground=COLORS["primary"],
            relief=tk.FLAT,
            padx=14,
            pady=14,
            font=(FONT_UI, 9),
        )
        prompt_preview.insert("1.0", prompt)
        prompt_preview.configure(state=tk.DISABLED)
        prompt_preview.grid(row=1, column=0, sticky="nsew", padx=16, pady=14)

        footer = tk.Frame(preview, bg=COLORS["surface"], padx=16, pady=12)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)

        def close_preview(is_approved=False):
            if not preview.winfo_exists():
                return
            approved[0] = is_approved
            try:
                preview.grab_release()
            except tk.TclError:
                pass
            preview.destroy()
            if self.root.winfo_exists():
                self.root.attributes("-topmost", True)
                self.root.lift()

        self._button(
            footer,
            "Back",
            close_preview,
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            footer,
            text="●  Processed locally · Nothing is sent automatically",
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=(FONT_UI, 8),
        ).grid(row=0, column=1)
        confirm = tk.Button(
            footer,
            text="Confirm and paste",
            command=lambda: close_preview(True),
            bg=COLORS["primary"],
            fg=COLORS["text"],
            activebackground=COLORS["primary_hover"],
            activeforeground=COLORS["text"],
            relief=tk.FLAT,
            bd=0,
            padx=22,
            pady=11,
            cursor="hand2",
            font=(FONT_UI, 10, "bold"),
            default=tk.ACTIVE,
        )
        confirm.grid(row=0, column=2, sticky="e")

        self.root.attributes("-topmost", False)
        preview.attributes("-topmost", True)
        preview.protocol("WM_DELETE_WINDOW", close_preview)
        preview.bind("<Escape>", lambda _event: close_preview())
        preview.bind("<Control-Return>", lambda _event: close_preview(True))
        confirm.bind("<Return>", lambda _event: close_preview(True))
        preview.update_idletasks()
        preview.lift()
        preview.focus_force()
        confirm.focus_set()
        preview.grab_set()
        preview.wait_window()
        return approved[0]

    def run(self):
        self.root.mainloop()
        return self.confirmed, self.final_prompt

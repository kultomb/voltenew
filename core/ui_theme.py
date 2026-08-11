"""
Design system — HBG AdBlocker (CustomTkinter).
SaaS security console · deep navy · purple primary · green scan accent.
"""

from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk

# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------

C = {
    "bg_app": "#0b0e14",
    "bg_sidebar": "#0b0e14",
    "bg_surface": "#161b22",
    "bg_card": "#161b22",
    "bg_card_hover": "#1c2129",
    "bg_input": "#12151c",
    "bg_subtle": "#0f1218",
    "bg_inset": "#0d1016",
    "bg_modal": "#232b38",
    "border_modal": "#4b5563",
    "overlay_shadow": "#030508",
    "overlay_scrim": "#05070b",
    "border_subtle": "#252b36",
    "border_default": "#30363d",
    "border_focus": "#4f46e5",
    "text_primary": "#f0f3f6",
    "text_secondary": "#9ca3af",
    "text_tertiary": "#6b7280",
    "accent": "#4f46e5",
    "accent_hover": "#6366f1",
    "accent_soft": "#312e81",
    "accent_muted": "#a5b4fc",
    "success": "#10b981",
    "success_hover": "#34d399",
    "success_soft": "#064e3b",
    "danger": "#ef4444",
    "danger_hover": "#f87171",
    "danger_soft": "#450a0a",
    "warning": "#f59e0b",
    "warning_soft": "#422006",
    "brand_youtube": "#ff0000",
    "brand_youtube_hover": "#cc0000",
    "selection": "#3730a3",
    "row_alt": "#12151f",
    "row_hover": "#1a1f2e",
    "terminal_bg": "#080a12",
    "terminal_text": "#a7f3d0",
    "control_idle_bg": "#5c7cfa",
    "control_idle_hover_bg": "#4258d4",
    "control_idle_border": "#7b93ff",
    "control_glow_idle": "#354a9e",
    "control_running_bg": "#7c3aed",
    "control_running_hover": "#6d28d9",
    "control_active": "#6d8aff",
    "control_active_hover": "#8098ff",
    "control_glow": "#2f4494",
}

COLORS = {**C, "bg_deep": C["bg_app"], "bg_card": C["bg_card"], "bg_hover": C["bg_card_hover"],
          "bg_elevated": C["bg_surface"], "accent_primary": C["accent"], "accent_primary_hover": C["accent_hover"],
          "accent_success": C["success"], "accent_danger": C["danger"], "accent_warning": C["warning"],
          "text_primary": C["text_primary"], "text_muted": C["text_secondary"], "border": C["border_default"]}

LOG_TAGS = {
    "timestamp": {"foreground": C["text_tertiary"]},
    "success": {"foreground": C["success"]},
    "error": {"foreground": C["danger"]},
    "warning": {"foreground": C["warning"]},
    "pending": {"foreground": "#cbd5e1"},
    "info": {"foreground": "#86efac"},
}

SPACE = {"0": 0, "1": 4, "2": 8, "3": 12, "4": 16, "5": 20, "6": 24, "7": 32, "8": 40, "9": 48,
         "xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32, "2xl": 40}

LAYOUT = {
    "sidebar_width": 248,
    "content_pad_x": 24,
    "content_pad_y": 20,
    "content_pad_right": 24,
    "section_gap": 10,
    "header_gap": 16,
    "toolbar_h": 36,
    "metric_strip_h": 0,
    "tree_row_h": 52,
    "control_col": 300,
    "control_btn_h": 34,
    "control_btn_gap": 4,
    "max_content": 1280,
}

RADIUS = {"sm": 8, "md": 10, "lg": 12, "xl": 14}

# Balanced hierarchy — titles restrained, body readable (mockup-aligned)
FONTS = {
    "page": ("Segoe UI", 22, "bold"),
    "title": ("Segoe UI", 14, "bold"),
    "heading": ("Segoe UI", 13, "bold"),
    "body": ("Segoe UI", 13),
    "body_sm": ("Segoe UI", 12),
    "caption": ("Segoe UI", 11),
    "mono": ("JetBrains Mono", 12),
    "mono_sm": ("JetBrains Mono", 11),
    "stat": ("Segoe UI", 15, "bold"),
    "stat_sm": ("Segoe UI", 13, "bold"),
    "display": ("Segoe UI", 22, "bold"),
    "micro": ("Segoe UI", 10),
}


def get_font(variant: str = "body"):
    return FONTS.get(variant, FONTS["body"])


def init_app_theme():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    try:
        ctk.set_widget_scaling(1.0)
    except Exception:
        pass


class UI:
    @staticmethod
    def card(
        master, *, padding: int = 0, hover: bool = False, inset: bool = False, tight: bool = False, **kwargs
    ) -> ctk.CTkFrame:
        fg = C["bg_inset"] if inset else (C["bg_card_hover"] if hover else C["bg_card"])
        frame = ctk.CTkFrame(
            master, fg_color=fg, corner_radius=RADIUS["lg"],
            border_width=1, border_color=C["border_subtle"], **kwargs,
        )
        if padding:
            inner = ctk.CTkFrame(frame, fg_color="transparent", height=1)
            inner.pack_propagate(True)
            if tight:
                inner.pack(fill="x", padx=padding, pady=padding)
            else:
                inner.pack(fill="both", expand=True, padx=padding, pady=padding)
            frame._inner = inner  # noqa: SLF001
            frame.pack_propagate(True)
        return frame

    @staticmethod
    def card_inner(card: ctk.CTkFrame) -> ctk.CTkFrame:
        return getattr(card, "_inner", card)

    @staticmethod
    def overlay_panel(
        master,
        *,
        padding: int = 0,
        tight: bool = False,
        **kwargs,
    ) -> ctk.CTkFrame:
        """Thẻ dialog nổi — nền sáng hơn app, viền nhẹ (không lớp đen phía sau)."""
        frame = ctk.CTkFrame(
            master,
            fg_color=C["bg_modal"],
            corner_radius=RADIUS["xl"],
            border_width=1,
            border_color=C["border_modal"],
            **kwargs,
        )
        if padding:
            inner = ctk.CTkFrame(frame, fg_color="transparent", height=1)
            inner.pack_propagate(True)
            if tight:
                inner.pack(fill="x", padx=padding, pady=padding)
            else:
                inner.pack(fill="both", expand=True, padx=padding, pady=padding)
            frame._inner = inner  # noqa: SLF001
            frame.pack_propagate(True)
        return frame

    @staticmethod
    def command_bar(master, *, padding: int | None = None, compact: bool = False) -> tuple[ctk.CTkFrame, ctk.CTkFrame]:
        if padding is not None:
            pad = padding
        else:
            pad = SPACE["2"] if compact else SPACE["3"]
        card = UI.card(master, padding=pad, inset=True)
        return card, UI.card_inner(card)

    @staticmethod
    def toolbar_group(master, *, side: str = "left") -> ctk.CTkFrame:
        g = ctk.CTkFrame(master, fg_color="transparent")
        g.pack(side=side)
        return g

    @staticmethod
    def toolbar_sep(master) -> ctk.CTkFrame:
        sep = ctk.CTkFrame(master, width=1, height=20, fg_color=C["border_subtle"])
        sep.pack(side="left", padx=(SPACE["2"], SPACE["2"]))
        return sep

    @staticmethod
    def label(master, text, *, variant="body", color=None, **kwargs) -> ctk.CTkLabel:
        return ctk.CTkLabel(
            master, text=text, font=get_font(variant),
            text_color=color or C["text_primary"], **kwargs,
        )

    @staticmethod
    def muted(master, text, **kwargs) -> ctk.CTkLabel:
        return UI.label(master, text, variant="body_sm", color=C["text_secondary"], **kwargs)

    @staticmethod
    def subtitle(master, text, **kwargs) -> ctk.CTkLabel:
        """Breadcrumb / mô tả dưới tiêu đề trang."""
        return UI.label(master, text, variant="caption", color=C["text_tertiary"], **kwargs)

    @staticmethod
    def section_label(master, text, **kwargs) -> ctk.CTkLabel:
        """Nhãn nhóm MENU, THAO TÁC — nhỏ, chữ hoa."""
        return UI.label(master, text.upper(), variant="caption", color=C["text_tertiary"], **kwargs)

    @staticmethod
    def btn(master, text, command=None, *, variant="secondary", width=None, height=36, **kwargs) -> ctk.CTkButton:
        styles = {
            "primary": {
                "fg_color": C["accent"], "hover_color": C["accent_hover"],
                "text_color": C["text_primary"], "border_width": 0,
            },
            "secondary": {
                "fg_color": C["bg_input"], "hover_color": C["bg_card_hover"],
                "text_color": C["text_primary"], "border_width": 1, "border_color": C["border_default"],
            },
            "ghost": {
                "fg_color": C["bg_input"], "hover_color": C["bg_card_hover"],
                "text_color": C["text_secondary"], "border_width": 1, "border_color": C["border_subtle"],
            },
            "danger": {
                "fg_color": C["bg_input"], "hover_color": C["danger_soft"],
                "text_color": C["danger"], "border_width": 1, "border_color": C["border_subtle"],
            },
            "success": {
                "fg_color": C["success"], "hover_color": C["success_hover"],
                "text_color": "#052e1a", "border_width": 0,
            },
            "elevated": {
                "fg_color": C["bg_modal"],
                "hover_color": C["bg_card_hover"],
                "text_color": C["accent_muted"],
                "border_width": 1,
                "border_color": C["accent"],
            },
        }
        style = styles.get(variant, styles["secondary"])
        kw = {"master": master, "text": text, "command": command, "height": height,
              "corner_radius": RADIUS["md"], "font": get_font("body_sm"), **style, **kwargs}
        if width is not None:
            kw["width"] = width
        return ctk.CTkButton(**kw)

    @staticmethod
    def toolbar_reload_btn(master, command, *, width: int = 40, height: int = 36) -> ctk.CTkButton:
        """Nút tải lại ADB — biểu tượng ↻."""
        return ctk.CTkButton(
            master,
            text="↻",
            command=command,
            width=width,
            height=height,
            corner_radius=RADIUS["md"],
            font=("Segoe UI Symbol", 18),
            fg_color=C["bg_input"],
            hover_color=C["bg_card_hover"],
            text_color=C["text_primary"],
            border_width=1,
            border_color=C["border_subtle"],
        )

    @staticmethod
    def toolbar_youtube_btn(master, command, *, width: int = 40, height: int = 36) -> ctk.CTkButton:
        """Nút mở kênh YouTube — nền đỏ, icon play."""
        return ctk.CTkButton(
            master,
            text="▶",
            command=command,
            width=width,
            height=height,
            corner_radius=RADIUS["sm"],
            font=("Segoe UI", 13, "bold"),
            fg_color=C["brand_youtube"],
            hover_color=C["brand_youtube_hover"],
            text_color="#ffffff",
            border_width=0,
        )

    @staticmethod
    def entry(master, placeholder="", width=200, **kwargs) -> ctk.CTkEntry:
        return ctk.CTkEntry(
            master, placeholder_text=placeholder, width=width, height=36,
            corner_radius=RADIUS["md"], font=get_font("body_sm"),
            fg_color=C["bg_input"], border_color=C["border_default"], border_width=1,
            text_color=C["text_primary"], placeholder_text_color=C["text_tertiary"], **kwargs,
        )

    @staticmethod
    def search(master, placeholder="Tìm kiếm…", width=220, **kwargs) -> ctk.CTkEntry:
        return UI.entry(master, placeholder=placeholder, width=width, **kwargs)

    @staticmethod
    def progress(master, **kwargs) -> ctk.CTkProgressBar:
        height = kwargs.pop("height", 4)
        bar = ctk.CTkProgressBar(
            master,
            height=height,
            corner_radius=kwargs.pop("corner_radius", 2),
            fg_color=kwargs.pop("fg_color", C["bg_input"]),
            progress_color=kwargs.pop("progress_color", C["accent"]),
            border_width=kwargs.pop("border_width", 0),
            **kwargs,
        )
        bar.set(0)
        return bar

    @staticmethod
    def divider(master, orient="horizontal") -> ctk.CTkFrame:
        if orient == "horizontal":
            f = ctk.CTkFrame(master, height=1, fg_color=C["border_subtle"])
            f.pack(fill="x", pady=SPACE["3"])
            return f
        f = ctk.CTkFrame(master, width=1, fg_color=C["border_subtle"])
        return f

    @staticmethod
    def vdivider(master, *, height: int = 48) -> ctk.CTkFrame:
        sep = ctk.CTkFrame(master, width=1, height=height, fg_color=C["border_subtle"])
        return sep

    @staticmethod
    def badge(master, text, *, tone="neutral") -> ctk.CTkFrame:
        """Pill badge — outline style like mockup."""
        tones = {
            "neutral": (C["border_default"], C["text_secondary"]),
            "success": (C["success"], C["success"]),
            "warning": (C["warning"], C["warning"]),
            "danger": (C["danger"], C["danger"]),
            "accent": (C["accent"], C["accent_muted"]),
        }
        border, fg = tones.get(tone, tones["neutral"])
        wrap = ctk.CTkFrame(
            master, fg_color="transparent", corner_radius=RADIUS["xl"],
            border_width=1, border_color=border,
        )
        ctk.CTkLabel(
            wrap, text=text, font=get_font("body_sm"), text_color=fg,
        ).pack(padx=SPACE["3"], pady=SPACE["1"])
        return wrap

    @staticmethod
    def search_field(master, placeholder="Tìm app hoặc package…", width=360) -> ctk.CTkFrame:
        h = LAYOUT["toolbar_h"]
        wrap = ctk.CTkFrame(
            master, fg_color=C["bg_input"], corner_radius=RADIUS["sm"],
            border_width=1, border_color=C["border_default"], height=h,
        )
        wrap.pack_propagate(False)
        wrap.grid_columnconfigure(0, weight=1)
        entry = ctk.CTkEntry(
            wrap, placeholder_text=placeholder, height=h - 2,
            font=get_font("body_sm"), fg_color=C["bg_input"], border_width=0,
            text_color=C["text_primary"], placeholder_text_color=C["text_tertiary"],
        )
        entry.grid(row=0, column=0, sticky="ew", padx=(SPACE["3"], 0), pady=SPACE["1"])
        ctk.CTkLabel(wrap, text="🔍", font=get_font("body"), text_color=C["text_tertiary"]).grid(
            row=0, column=1, padx=(0, SPACE["3"]), pady=SPACE["1"],
        )
        wrap.configure(width=width)
        wrap._entry = entry  # noqa: SLF001
        return wrap

    @staticmethod
    def metric_cell(master, icon: str, title: str, value: str, subtitle: str = "") -> ctk.CTkFrame:
        """Mockup segment: icon | title → value → subtitle."""
        cell = ctk.CTkFrame(master, fg_color="transparent", height=1, corner_radius=0, border_width=0)
        cell.pack_propagate(True)
        cell.grid_propagate(True)
        row = ctk.CTkFrame(cell, fg_color="transparent", height=1)
        row.pack_propagate(True)
        row.pack(anchor="w")
        ctk.CTkLabel(
            row, text=icon, font=("Segoe UI", 16), text_color=C["text_tertiary"], width=22,
        ).pack(side="left", anchor="n")
        col = ctk.CTkFrame(row, fg_color="transparent")
        col.pack(side="left", padx=(SPACE["2"], 0))
        cell._title = UI.muted(col, title)
        cell._title.pack(anchor="w")
        cell._value = UI.label(col, value, variant="stat_sm")
        cell._value.pack(anchor="w", pady=(0, 0))
        sub_color = C["success"] if subtitle and "kết nối" in subtitle.lower() else C["text_tertiary"]
        cell._sub = ctk.CTkLabel(col, text=subtitle or "", font=get_font("caption"), text_color=sub_color)
        if subtitle:
            cell._sub.pack(anchor="w")

        def set_metric(val: str, sub: str = "", *, sub_tone: str = "muted"):
            cell._value.configure(text=val)
            if sub:
                cell._sub.configure(text=sub)
                colors = {"success": C["success"], "danger": C["danger"], "muted": C["text_tertiary"]}
                cell._sub.configure(text_color=colors.get(sub_tone, C["text_tertiary"]))
                if not cell._sub.winfo_ismapped():
                    cell._sub.pack(anchor="w")
            elif cell._sub.winfo_ismapped():
                cell._sub.pack_forget()

        cell.set_metric = set_metric
        return cell

    @staticmethod
    def metric_strip_row(master, *, min_height: int | None = None) -> ctk.CTkFrame:
        """Height follows content — no fixed min height."""
        row = ctk.CTkFrame(master, fg_color="transparent", height=1, corner_radius=0, border_width=0)
        row.pack_propagate(True)
        row.grid_propagate(True)
        row.pack(fill="x")
        return row

    @staticmethod
    def metric_strip_layout(row: ctk.CTkFrame, cells: list) -> None:
        n = len(cells)
        for i in range(n):
            col = i * 2
            row.grid_columnconfigure(col, weight=1, uniform="hbg_metric")
        for i in range(n - 1):
            div_col = i * 2 + 1
            row.grid_columnconfigure(div_col, weight=0, minsize=1)
            sep = ctk.CTkFrame(row, width=1, height=36, fg_color=C["border_subtle"])
            sep.grid_propagate(False)
            sep.grid(row=0, column=div_col, sticky="n", pady=4)
        for i, cell in enumerate(cells):
            cell.grid(row=0, column=i * 2, sticky="nw", padx=(SPACE["4"], SPACE["3"]), pady=0)

    @staticmethod
    def metric_strip(master, cells: list, *, min_height: int = 60) -> ctk.CTkFrame:
        row = UI.metric_strip_row(master, min_height=min_height)
        UI.metric_strip_layout(row, cells)
        return row

    @staticmethod
    def status_ready(master, text: str = "Sẵn sàng quét") -> ctk.CTkFrame:
        row = ctk.CTkFrame(master, fg_color="transparent")
        ctk.CTkLabel(row, text="●", font=get_font("caption"), text_color=C["accent"]).pack(side="left")
        row._status = UI.muted(row, text)  # noqa: SLF001
        row._status.pack(side="left", padx=(SPACE["1"], 0))
        return row

    @staticmethod
    def control_btn(master, text, command, *, icon="", variant="secondary") -> ctk.CTkButton:
        """Legacy — prefer ControlPanelGroup for dashboard điều khiển."""
        label = f"  {icon}  {text}" if icon else f"  {text}"
        return UI.btn(master, label, command, variant=variant, height=40)

    @staticmethod
    def nav_item(master, text, icon, command, *, active=False) -> ctk.CTkButton:
        return ctk.CTkButton(
            master, text=f"  {icon}   {text}", command=command, anchor="w", height=40,
            corner_radius=RADIUS["md"], font=get_font("body_sm"),
            fg_color=C["accent"] if active else "transparent",
            hover_color=C["accent_hover"] if active else C["bg_card_hover"],
            text_color=C["text_primary"] if active else C["text_secondary"],
            border_width=0,
        )

    @staticmethod
    def configure_treeview(style: ttk.Style, prefix: str = ""):
        name = f"{prefix}Saas.Treeview" if prefix else "Saas.Treeview"
        heading = f"{name}.Heading"
        style.theme_use("clam")
        rh = LAYOUT["tree_row_h"]
        style.configure(
            name,
            rowheight=rh,
            font=("Segoe UI Semibold", 13),
            background=C["bg_inset"],
            foreground=C["text_primary"],
            fieldbackground=C["bg_inset"],
            borderwidth=0,
            relief="flat",
        )
        style.configure(
            heading,
            background=C["bg_card"],
            foreground=C["text_tertiary"],
            bordercolor=C["border_subtle"],
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padding=(16, 10, 12, 10),
        )
        style.map(
            name,
            background=[("selected", C["selection"])],
            foreground=[("selected", C["text_primary"])],
        )
        return name, heading

    @staticmethod
    def style_context_menu(menu) -> None:
        try:
            menu_font = ("Segoe UI", 13)
            menu.configure(
                bg=C["bg_card"], fg=C["text_primary"],
                activebackground=C["accent"], activeforeground=C["text_primary"],
                relief="flat", borderwidth=1,
                font=menu_font,
            )
            menu.configure(activefont=menu_font, disabledforeground=C["text_tertiary"])
        except Exception:
            pass

    @staticmethod
    def textbox(master, *, height=120, mono=False, **kwargs) -> ctk.CTkTextbox:
        return ctk.CTkTextbox(
            master, height=height,
            font=get_font("mono") if mono else get_font("body"),
            fg_color=C["terminal_bg"], text_color=C["terminal_text"],
            corner_radius=RADIUS["md"], border_width=1, border_color=C["border_subtle"],
            wrap="word", **kwargs,
        )

    @staticmethod
    def empty_state(master, *, icon="◇", title="Chưa có dữ liệu",
                    description="Kết nối thiết bị để bắt đầu.", action_text=None, action_cmd=None) -> ctk.CTkFrame:
        wrap = UI.card(master, padding=SPACE["6"], inset=True)
        inner = UI.card_inner(wrap)
        UI.label(inner, icon, variant="title", color=C["text_tertiary"]).pack(pady=(0, SPACE["2"]))
        wrap.empty_title = UI.label(inner, title, variant="heading")
        wrap.empty_title.pack()
        wrap.empty_desc = UI.muted(inner, description)
        wrap.empty_desc.pack(pady=(SPACE["2"], SPACE["4"]))
        wrap.empty_action = None
        if action_text and action_cmd:
            wrap.empty_action = UI.btn(inner, action_text, action_cmd, variant="primary", width=128)
            wrap.empty_action.pack()
        return wrap


class ControlPanelGroup:
    """Nút điều khiển — hover / chọn + thanh tiến trình & trạng thái từng thao tác."""

    def __init__(self, master, *, height: int | None = None, gap: int | None = None):
        self._master = master
        self._height = height if height is not None else LAYOUT["control_btn_h"]
        self._gap = gap if gap is not None else LAYOUT["control_btn_gap"]
        self._items: list[dict] = []
        self._selected: ctk.CTkButton | None = None
        self._enabled = True

    def add(self, text: str, command, *, icon: str = "") -> ctk.CTkButton:
        label = f"  {icon}  {text}" if icon else f"  {text}"
        shell = ctk.CTkFrame(self._master, fg_color="transparent")
        half = max(1, self._gap // 2)
        shell.pack(fill="x", pady=(half, half))
        btn = ctk.CTkButton(
            shell,
            text=label,
            anchor="w",
            height=self._height,
            corner_radius=RADIUS["md"],
            font=get_font("body"),
            command=lambda b=None: None,
            fg_color=C["control_idle_bg"],
            hover_color=C["control_idle_hover_bg"],
            text_color="#ffffff",
            border_width=0,
        )
        btn.pack(fill="x")

        task_row = ctk.CTkFrame(shell, fg_color="transparent")
        progress = UI.progress(task_row, height=3)
        status_lbl = ctk.CTkLabel(
            task_row,
            text="",
            font=get_font("caption"),
            text_color=C["text_tertiary"],
            anchor="w",
            height=16,
        )
        status_lbl.pack(fill="x", pady=(SPACE["1"], 0))
        progress.pack(fill="x")
        progress.pack_forget()

        item = {
            "btn": btn,
            "shell": shell,
            "task_row": task_row,
            "command": command,
            "base_label": label,
            "progress": progress,
            "status_lbl": status_lbl,
            "task_phase": "idle",
            "pulse_v": 0.12,
            "pulse_after": None,
        }
        self._items.append(item)

        def _click():
            self._on_click(btn)

        btn.configure(command=_click)
        for widget in (shell, btn):
            widget.bind("<Enter>", lambda _e, b=btn: self._on_enter(b))
            widget.bind("<Leave>", lambda _e, b=btn: self._on_leave(b))

        self._apply(btn, "idle")
        return btn

    def _find(self, btn: ctk.CTkButton) -> dict | None:
        for item in self._items:
            if item["btn"] is btn:
                return item
        return None

    def _apply(self, btn: ctk.CTkButton, state: str) -> None:
        item = self._find(btn)
        if not item:
            return
        if state == "running":
            btn.configure(
                fg_color=C["control_running_bg"],
                hover_color=C["control_running_hover"],
                text_color="#ffffff",
                border_width=0,
            )
        elif state == "active":
            btn.configure(
                fg_color=C["control_active"],
                hover_color=C["control_active_hover"],
                text_color="#ffffff",
                border_width=0,
            )
        elif state == "success":
            btn.configure(
                fg_color=C["success"],
                hover_color=C["success_hover"],
                text_color="#ffffff",
                border_width=0,
            )
        elif state == "error":
            btn.configure(
                fg_color=C["danger"],
                hover_color=C["danger_hover"],
                text_color="#ffffff",
                border_width=0,
            )
        elif state == "hover":
            btn.configure(
                fg_color=C["control_idle_hover_bg"],
                hover_color=C["control_idle_hover_bg"],
                text_color="#ffffff",
                border_width=0,
            )
        elif state == "disabled":
            btn.configure(
                fg_color=C["bg_subtle"],
                hover_color=C["bg_subtle"],
                text_color=C["text_tertiary"],
                border_width=0,
            )
        else:
            btn.configure(
                fg_color=C["control_idle_bg"],
                hover_color=C["control_idle_hover_bg"],
                text_color="#ffffff",
                border_width=0,
            )

    def _on_enter(self, btn: ctk.CTkButton) -> None:
        if not self._enabled or btn.cget("state") == "disabled":
            return
        item = self._find(btn)
        if btn is self._selected and item and item.get("task_phase") == "running":
            self._apply(btn, "running")
        elif btn is self._selected:
            self._apply(btn, "active")
        else:
            self._apply(btn, "hover")

    def _on_leave(self, btn: ctk.CTkButton) -> None:
        if not self._enabled or btn.cget("state") == "disabled":
            return
        item = self._find(btn)
        if btn is self._selected and item and item.get("task_phase") == "running":
            self._apply(btn, "running")
        elif btn is self._selected:
            self._apply(btn, "active")
        else:
            self._apply(btn, "idle")

    def _on_click(self, btn: ctk.CTkButton) -> None:
        if not self._enabled or btn.cget("state") == "disabled":
            return
        item = self._find(btn)
        if not item:
            return
        if self._selected is not btn:
            if self._selected is not None:
                self._apply(self._selected, "idle")
            self._selected = btn
            self._apply(btn, "running")
        item["command"]()

    def set_selected(self, btn: ctk.CTkButton | None) -> None:
        if self._selected is not None and self._selected is not btn:
            self._apply(self._selected, "idle")
        self._selected = btn
        if btn is not None:
            self._apply(btn, "active")

    def clear_selection(self) -> None:
        self.set_selected(None)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        state = "normal" if enabled else "disabled"
        for item in self._items:
            btn = item["btn"]
            btn.configure(state=state)
            if enabled:
                self._apply(btn, "active" if btn is self._selected else "idle")
            else:
                self._apply(btn, "disabled")
        if not enabled:
            self._selected = None

    def buttons(self) -> list[ctk.CTkButton]:
        return [item["btn"] for item in self._items]

    def refresh_style(self, btn: ctk.CTkButton) -> None:
        """Cập nhật màu sau khi đổi state/text bên ngoài."""
        if not self._enabled or btn.cget("state") == "disabled":
            self._apply(btn, "disabled")
        elif btn is self._selected:
            item = self._find(btn)
            if item and item.get("task_phase") == "running":
                self._apply(btn, "running")
            else:
                self._apply(btn, "active")
        else:
            self._apply(btn, "idle")

    def _cancel_pulse(self, item: dict) -> None:
        aid = item.get("pulse_after")
        if aid:
            try:
                self._master.after_cancel(aid)
            except Exception:
                pass
            item["pulse_after"] = None

    def _pulse_tick(self, btn: ctk.CTkButton) -> None:
        item = self._find(btn)
        if not item or item.get("task_phase") != "running":
            return
        v = float(item.get("pulse_v", 0.12)) + 0.045
        if v > 0.92:
            v = 0.1
        item["pulse_v"] = v
        item["progress"].set(v)
        item["pulse_after"] = self._master.after(70, lambda b=btn: self._pulse_tick(b))

    def set_task(
        self,
        btn: ctk.CTkButton,
        phase: str,
        *,
        progress: float | None = None,
        detail: str = "",
        autoclear: bool = True,
    ) -> None:
        """
        phase: idle | running | success | error
        progress: 0..1 (None = indeterminate khi running)
        """
        item = self._find(btn)
        if not item:
            return
        self._cancel_pulse(item)
        item["task_phase"] = phase
        bar = item["progress"]
        lbl = item["status_lbl"]

        task_row = item["task_row"]

        if phase == "idle":
            bar.pack_forget()
            lbl.configure(text="", text_color=C["text_tertiary"])
            btn.configure(text=item["base_label"])
            task_row.pack_forget()
            if btn is self._selected:
                self.clear_selection()
            else:
                self._apply(btn, "idle")
            return

        if not task_row.winfo_ismapped():
            task_row.pack(fill="x", padx=SPACE["1"], pady=(SPACE["2"], 0))
        if not bar.winfo_ismapped():
            bar.pack(fill="x", before=lbl)

        if phase == "running":
            self.set_selected(btn)
            self._apply(btn, "running")
            lbl.configure(text=detail or "Đang xử lý…", text_color=C["accent_muted"])
            bar.configure(progress_color=C["accent"])
            if progress is None:
                self._pulse_tick(btn)
            else:
                bar.set(max(0.0, min(1.0, progress)))
            return

        if phase == "success":
            self._apply(btn, "success")
            bar.set(1.0)
            bar.configure(progress_color=C["success"])
            lbl.configure(text=detail or "Hoàn tất", text_color=C["success"])
            btn.configure(text=item["base_label"])
            if autoclear:
                self._master.after(1800, lambda b=btn: self.set_task(b, "idle"))
            return

        if phase == "error":
            self._apply(btn, "error")
            bar.set(1.0)
            bar.configure(progress_color=C["danger"])
            lbl.configure(text=detail or "Lỗi", text_color=C["danger"])
            btn.configure(text=item["base_label"])
            if autoclear:
                self._master.after(2200, lambda b=btn: self.set_task(b, "idle"))

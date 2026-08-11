"""
Chọn Launcher (màn hình chính) để gỡ — hiển thị launcher đang dùng và app cài thêm.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional

import customtkinter as ctk
import tkinter as tk

from core.junk_pick_dialog import _ctk_image_from_path, _placeholder_ctk_image, _resolve_icon_path
from core.ui_theme import C, UI, RADIUS, SPACE, get_font
from core.window_utils import show_overlay_panel

_LIST_ICON_PX = 44
_LIST_MAX_H = 380
_ROW_H = 72
_BADGE_ACTIVE_SYSTEM = "Đang sử dụng | Hệ thống"
_BADGE_ACTIVE_USER = "Đang sử dụng"


def ask_launcher_removal_pick(
    parent: ctk.Misc,
    launchers: list[dict[str, Any]],
    *,
    device_manager,
    label_for: Callable[[str], str],
    current_package: str | None = None,
) -> Optional[list[str]]:
    """
    Trả về package launcher được chọn để gỡ; None nếu hủy; [] nếu không chọn.
    """
    if not launchers:
        return []

    items = []
    for row in launchers:
        pkg = row["package"]
        is_system = bool(row.get("is_system", not row.get("is_user", True)))
        items.append({
            "package": pkg,
            "name": label_for(pkg),
            "is_default": bool(row.get("is_default")),
            "is_system": is_system,
            "activity": row.get("activity") or "",
        })
    removable_count = sum(1 for i in items if not i["is_system"])
    items.sort(key=lambda x: (x["is_system"], not x["is_default"], x["name"].lower()))

    root = parent.winfo_toplevel()
    result: dict = {"value": None}
    alive = {"ok": True}

    def _build(inner: ctk.CTkFrame, close: Callable[[], None]) -> None:
        images: dict[str, ctk.CTkImage] = {}
        row_widgets: dict[str, dict] = {}
        placeholder = _placeholder_ctk_image()
        confirm_btn: ctk.CTkButton | None = None

        head = ctk.CTkFrame(inner, fg_color="transparent")
        head.pack(fill="x", pady=(0, SPACE["2"]))
        head_top = ctk.CTkFrame(head, fg_color="transparent")
        head_top.pack(fill="x")
        UI.label(head_top, "Launcher trên thiết bị", variant="heading").pack(side="left", anchor="w")
        count_lbl = UI.muted(head_top, f"Đã chọn 0/{removable_count}")
        count_lbl.pack(side="right", anchor="e")

        cur = current_package or next((i["package"] for i in items if i["is_default"]), None)
        cur_item = next((i for i in items if i["package"] == cur), None) if cur else None
        cur_name = label_for(cur) if cur else "—"
        if cur_item and cur_item["is_system"]:
            sub = (
                f"Đang dùng: {cur_name} (launcher hệ thống). "
                "Chọn launcher cài thêm để gỡ — launcher hệ thống không thể gỡ."
            )
        else:
            sub = (
                f"Đang dùng: {cur_name}. "
                "Launcher cài thêm đang dùng được chọn sẵn. Launcher hệ thống không thể gỡ."
            )
        UI.muted(head, sub).pack(anchor="w", pady=(2, 0))

        def _refresh_count() -> None:
            n = sum(
                1 for w in row_widgets.values()
                if w.get("selectable") and w["var"].get()
            )
            count_lbl.configure(text=f"Đã chọn {n}/{removable_count}")
            if confirm_btn is not None:
                confirm_btn.configure(
                    text=f"Gỡ launcher ({n})" if n else "Gỡ launcher",
                    state="normal" if n else "disabled",
                )

        list_card = UI.card(inner, padding=0, inset=True)
        list_card.pack(fill="both", expand=True, pady=(SPACE["2"], SPACE["4"]))
        scroll = ctk.CTkScrollableFrame(
            UI.card_inner(list_card),
            fg_color="transparent",
            height=min(_LIST_MAX_H, max(160, len(items) * (_ROW_H + 4))),
            scrollbar_button_color=C["border_default"],
            scrollbar_button_hover_color=C["accent"],
        )
        scroll.pack(fill="both", expand=True, padx=SPACE["1"], pady=SPACE["1"])
        scroll.grid_columnconfigure(0, weight=1)

        for idx, item in enumerate(items):
            pkg = item["package"]
            name = item["name"]
            is_def = item["is_default"]
            is_system = item["is_system"]
            selectable = not is_system
            default_checked = selectable and is_def

            row = ctk.CTkFrame(
                scroll,
                fg_color=C["bg_card"] if idx % 2 == 0 else C["row_alt"],
                corner_radius=RADIUS["sm"],
                height=_ROW_H,
            )
            row.grid(row=idx, column=0, sticky="ew", padx=SPACE["1"], pady=3)
            row.grid_propagate(False)
            row.grid_columnconfigure(2, weight=1)

            var = tk.BooleanVar(value=default_checked)
            var.trace_add("write", lambda *_a: _refresh_count())

            cb = ctk.CTkCheckBox(
                row,
                text="",
                variable=var,
                width=32,
                checkbox_width=22,
                checkbox_height=22,
                fg_color=C["accent"],
                hover_color=C["accent_hover"],
                border_color=C["border_default"],
                checkmark_color="#ffffff",
            )
            cb.grid(row=0, column=0, padx=(SPACE["3"], SPACE["2"]), pady=SPACE["2"], sticky="w")
            if is_system:
                var.set(False)
                cb.configure(state="disabled")

            icon_lbl = ctk.CTkLabel(row, text="", image=placeholder, width=_LIST_ICON_PX)
            icon_lbl.grid(row=0, column=1, padx=(0, SPACE["2"]), pady=SPACE["2"], sticky="w")

            text_col = ctk.CTkFrame(row, fg_color="transparent")
            text_col.grid(row=0, column=2, sticky="ew", padx=(0, SPACE["2"]), pady=SPACE["2"])
            UI.label(text_col, name, variant="body").grid(row=0, column=0, sticky="w")
            tags = []
            if selectable:
                tags.append("Cài thêm")
            sub_line = f"{pkg} · {' · '.join(tags)}" if tags else pkg
            UI.muted(text_col, sub_line).grid(row=1, column=0, sticky="w")

            if is_def:
                badge_text = _BADGE_ACTIVE_SYSTEM if is_system else _BADGE_ACTIVE_USER
                pill = ctk.CTkFrame(row, fg_color=C["accent_soft"], corner_radius=12)
                pill.grid(row=0, column=3, padx=(0, SPACE["3"]), pady=SPACE["2"], sticky="e")
                ctk.CTkLabel(
                    pill,
                    text=badge_text,
                    font=get_font("caption"),
                    text_color=C["accent_muted"],
                ).pack(padx=10, pady=5)
            elif is_system:
                pill = ctk.CTkFrame(
                    row, fg_color=C["danger_soft"], corner_radius=12,
                    border_width=1, border_color=C["danger"],
                )
                pill.grid(row=0, column=3, padx=(0, SPACE["3"]), pady=SPACE["2"], sticky="e")
                ctk.CTkLabel(
                    pill,
                    text="Hệ thống",
                    font=get_font("caption"),
                    text_color=C["danger"],
                ).pack(padx=10, pady=5)

            row_widgets[pkg] = {"var": var, "icon_lbl": icon_lbl, "selectable": selectable}

        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(fill="x")

        def _cancel() -> None:
            result["value"] = None
            alive["ok"] = False
            close()

        def _confirm() -> None:
            selected = [
                p for p, w in row_widgets.items()
                if w.get("selectable") and w["var"].get()
            ]
            if not selected:
                return
            result["value"] = selected
            alive["ok"] = False
            close()

        UI.btn(btns, "Hủy", _cancel, variant="ghost", width=100, height=40).pack(side="right", padx=(SPACE["2"], 0))
        confirm_btn = UI.btn(
            btns, "Gỡ launcher", _confirm, variant="danger", width=140, height=40,
        )
        confirm_btn.pack(side="right")
        _refresh_count()

        def _apply_icon(pkg: str, path: Optional[str]) -> None:
            if not alive["ok"]:
                return
            w = row_widgets.get(pkg)
            if not w:
                return
            try:
                img = _ctk_image_from_path(path) if path else placeholder
                w["icon_lbl"].configure(image=img)
            except Exception as exc:
                logging.debug("launcher icon %s: %s", pkg, exc)

        def _icon_worker() -> None:
            def load_one(it: dict) -> tuple[str, Optional[str]]:
                try:
                    path = _resolve_icon_path(
                        device_manager, it["package"], it["name"], None,
                    )
                    return it["package"], path
                except Exception as exc:
                    logging.debug("launcher icon %s: %s", it["package"], exc)
                    return it["package"], None

            with ThreadPoolExecutor(max_workers=8) as pool:
                futures = [pool.submit(load_one, it) for it in items]
                for fu in as_completed(futures):
                    try:
                        pkg, path = fu.result()
                    except Exception:
                        continue
                    if alive["ok"]:
                        root.after(0, lambda p=pkg, ph=path: _apply_icon(p, ph))

        inner._icon_images = images  # noqa: SLF001
        threading.Thread(target=_icon_worker, daemon=True).start()

    show_overlay_panel(parent, _build, max_width=580)
    return result["value"]

"""
Chọn ứng dụng nghi quảng cáo để gỡ — panel trong app, danh sách icon + checkbox.
"""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional

import customtkinter as ctk
from PIL import Image

from core.icon_extractor import make_squircle_thumbnail
from core.ui_theme import C, UI, RADIUS, SPACE, get_font
from core.window_utils import show_overlay_panel

_LIST_ICON_PX = 44
_LIST_MAX_H = 400
_ROW_H = 68

_LEVEL_VI = {
    "dangerous": "Nguy hiểm",
    "high_risk": "Rủi ro cao",
    "warning": "Cảnh báo",
    "safe": "An toàn",
}

_LEVEL_TONE = {
    "dangerous": (C["danger_soft"], C["danger"]),
    "high_risk": (C["danger_soft"], C["danger"]),
    "warning": (C["warning_soft"], C["warning"]),
    "safe": (C["success_soft"], C["success"]),
}


def _ctk_image_from_path(icon_path: str, size: int = _LIST_ICON_PX) -> ctk.CTkImage:
    img = Image.open(icon_path).convert("RGBA")
    thumb = make_squircle_thumbnail(img, size)
    return ctk.CTkImage(light_image=thumb, dark_image=thumb, size=(size, size))


def _placeholder_ctk_image(size: int = _LIST_ICON_PX) -> ctk.CTkImage:
    base = Image.new("RGBA", (size, size), (38, 42, 52, 255))
    thumb = make_squircle_thumbnail(base, size)
    return ctk.CTkImage(light_image=thumb, dark_image=thumb, size=(size, size))


def _normalize_items(
    packages: list[str],
    label_for: Callable[[str], str],
    meta_for: Callable[[str], dict] | None,
) -> list[dict[str, Any]]:
    items = []
    for pkg in packages:
        meta = (meta_for(pkg) if meta_for else {}) or {}
        analysis = meta.get("analysis") or meta
        level = analysis.get("level", meta.get("level", "warning"))
        score = int(analysis.get("score", meta.get("score", 0)))
        items.append({
            "package": pkg,
            "name": label_for(pkg),
            "level": level,
            "score": score,
        })
    return sorted(items, key=lambda x: (-x["score"], x["name"].lower()))


def _resolve_icon_path(
    device_manager,
    package: str,
    label: str,
    apk_hint: Optional[str],
) -> Optional[str]:
    path = device_manager.get_cached_icon_path(package)
    if path:
        return path
    path = device_manager.extract_icon_to_cache(package, apk_hint, label)
    if path:
        return path
    path = device_manager.ensure_ui_icon(package, apk_hint, label)
    return path


def prefetch_junk_icons(
    device_manager,
    packages: list[str],
    *,
    label_for: Callable[[str], str],
    hint_for: Callable[[str], Optional[str]] | None = None,
    max_workers: int = 10,
) -> None:
    """Tải icon Play Store / cache trước khi mở dialog."""
    if not packages:
        return

    def load_one(pkg: str) -> None:
        label = label_for(pkg)
        hint = hint_for(pkg) if hint_for else None
        try:
            _resolve_icon_path(device_manager, pkg, label, hint)
        except Exception as exc:
            logging.debug("prefetch icon %s: %s", pkg, exc)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        list(pool.map(load_one, packages))


def ask_junk_removal_pick(
    parent: ctk.Misc,
    packages: list[str],
    *,
    device_manager,
    label_for: Callable[[str], str],
    meta_for: Callable[[str], dict] | None = None,
    hint_for: Callable[[str], Optional[str]] | None = None,
    premium: bool = False,
    title: str | None = None,
) -> Optional[list[str]]:
    """
    Hiển thị danh sách app nghi QC; mặc định tất cả được chọn.
    Trả về list package đã chọn, [] nếu không chọn gì, None nếu hủy.
    """
    if not packages:
        return []

    items = _normalize_items(packages, label_for, meta_for)
    root = parent.winfo_toplevel()
    result: dict = {"value": None}
    alive = {"ok": True}
    max_w = 600 if premium else 560

    def _build(inner: ctk.CTkFrame, close: Callable[[], None]) -> None:
        images: dict[str, ctk.CTkImage] = {}
        row_widgets: dict[str, dict] = {}
        placeholder = _placeholder_ctk_image()
        confirm_btn: ctk.CTkButton | None = None

        head = ctk.CTkFrame(inner, fg_color="transparent")
        head.pack(fill="x", pady=(0, SPACE["3"]))
        head.grid_columnconfigure(1, weight=1)

        if premium:
            badge = ctk.CTkFrame(
                head, width=48, height=48, corner_radius=24,
                fg_color=C["accent_soft"], border_width=1, border_color=C["accent"],
            )
            badge.grid(row=0, column=0, rowspan=2, padx=(0, SPACE["3"]), sticky="nw")
            badge.grid_propagate(False)
            ctk.CTkLabel(
                badge, text="⚡", font=("Segoe UI", 22), text_color=C["accent_muted"],
            ).place(relx=0.5, rely=0.5, anchor="center")
            head_title = title or "Kết quả quét nhanh"
            head_sub = f"Phát hiện {len(items)} ứng dụng đáng gỡ. Giữ lại app bạn cần."
        else:
            badge = ctk.CTkFrame(
                head, width=44, height=44, corner_radius=22, fg_color=C["warning_soft"],
                border_width=1, border_color=C["warning"],
            )
            badge.grid(row=0, column=0, rowspan=2, padx=(0, SPACE["3"]), sticky="nw")
            badge.grid_propagate(False)
            ctk.CTkLabel(
                badge, text="!", font=("Segoe UI", 20, "bold"), text_color=C["warning"],
            ).place(relx=0.5, rely=0.5, anchor="center")
            head_title = title or "Ứng dụng nghi quảng cáo"
            head_sub = f"Tìm thấy {len(items)} app. Bỏ chọn app bạn muốn giữ lại."

        UI.label(head, head_title, variant="heading").grid(row=0, column=1, sticky="w")
        UI.muted(head, head_sub).grid(row=1, column=1, sticky="w", pady=(SPACE["1"], 0))

        tools = ctk.CTkFrame(inner, fg_color="transparent")
        tools.pack(fill="x", pady=(0, SPACE["2"]))

        count_lbl = UI.muted(tools, f"Đã chọn {len(items)}/{len(items)}")
        count_lbl.pack(side="right")

        _batch = {"active": False}
        toggle_btn: ctk.CTkButton | None = None

        def _sync_row_style(_pkg: str, w: dict) -> None:
            if not premium:
                return
            row = w["row"]
            on = w["var"].get()
            row.configure(
                fg_color=C["accent_soft"] if on else C["bg_input"],
                border_color=C["accent"] if on else C["border_subtle"],
            )

        def _update_toggle_label(n: int) -> None:
            if toggle_btn is None:
                return
            toggle_btn.configure(
                text="Bỏ chọn tất cả" if n >= len(items) else "Chọn tất cả",
            )

        def _refresh_count() -> None:
            n = sum(1 for it in row_widgets.values() if it["var"].get())
            count_lbl.configure(text=f"Đã chọn {n}/{len(items)}")
            if confirm_btn is not None:
                confirm_btn.configure(
                    text=f"Gỡ ngay ({n})" if premium and n else (f"Gỡ ({n})" if n else "Gỡ"),
                    state="normal" if n else "disabled",
                )
            _update_toggle_label(n)
            if premium:
                for pkg, w in row_widgets.items():
                    _sync_row_style(pkg, w)

        def _on_var_change(*_args) -> None:
            if _batch["active"]:
                return
            _refresh_count()

        def _toggle_select_all() -> None:
            n = sum(1 for it in row_widgets.values() if it["var"].get())
            checked = n < len(items)
            _batch["active"] = True
            try:
                for it in row_widgets.values():
                    it["var"].set(checked)
            finally:
                _batch["active"] = False
            _refresh_count()

        toggle_btn = UI.btn(
            tools,
            "Bỏ chọn tất cả",
            _toggle_select_all,
            variant="ghost",
            width=120,
            height=30,
        )
        toggle_btn.pack(side="left")

        list_card = UI.card(inner, padding=0, inset=True)
        list_card.pack(fill="both", expand=True, pady=(0, SPACE["4"]))
        list_inner = UI.card_inner(list_card)

        scroll = ctk.CTkScrollableFrame(
            list_inner,
            fg_color="transparent",
            height=min(_LIST_MAX_H, max(180, len(items) * (_ROW_H + 4))),
            scrollbar_button_color=C["border_default"],
            scrollbar_button_hover_color=C["accent"],
        )
        scroll.pack(fill="both", expand=True, padx=SPACE["1"], pady=SPACE["1"])
        scroll.grid_columnconfigure(0, weight=1)

        for idx, item in enumerate(items):
            pkg = item["package"]
            name = item["name"]
            level = item.get("level", "warning")
            score = item.get("score", 0)
            soft, accent = _LEVEL_TONE.get(level, _LEVEL_TONE["warning"])

            if premium:
                row = ctk.CTkFrame(
                    scroll,
                    fg_color=C["bg_input"],
                    corner_radius=RADIUS["md"],
                    height=_ROW_H,
                    border_width=2,
                    border_color=C["border_subtle"],
                )
            else:
                row = ctk.CTkFrame(
                    scroll,
                    fg_color=C["bg_card"] if idx % 2 == 0 else C["row_alt"],
                    corner_radius=RADIUS["sm"],
                    height=_ROW_H,
                )
            row.grid(row=idx, column=0, sticky="ew", padx=SPACE["1"], pady=3)
            row.grid_propagate(False)
            row.grid_columnconfigure(2, weight=1)

            var = tk.BooleanVar(value=True)
            var.trace_add("write", _on_var_change)

            cb = ctk.CTkCheckBox(
                row,
                text="",
                variable=var,
                width=32,
                checkbox_width=26 if premium else 22,
                checkbox_height=26 if premium else 22,
                corner_radius=8 if premium else 6,
                border_width=2,
                fg_color=C["accent"],
                hover_color=C["accent_hover"],
                border_color=C["border_default"],
                checkmark_color="#ffffff",
            )
            cb.grid(row=0, column=0, padx=(SPACE["3"], SPACE["2"]), pady=SPACE["2"], sticky="w")

            cached = device_manager.get_cached_icon_path(pkg)
            if cached:
                try:
                    images[pkg] = _ctk_image_from_path(cached)
                    row_icon = images[pkg]
                except Exception:
                    row_icon = placeholder
            else:
                row_icon = placeholder

            icon_lbl = ctk.CTkLabel(row, text="", image=row_icon, width=_LIST_ICON_PX)
            icon_lbl.grid(row=0, column=1, padx=(0, SPACE["2"]), pady=SPACE["2"], sticky="w")

            text_col = ctk.CTkFrame(row, fg_color="transparent")
            text_col.grid(row=0, column=2, sticky="ew", padx=(0, SPACE["2"]), pady=SPACE["2"])
            text_col.grid_columnconfigure(0, weight=1)
            UI.label(text_col, name, variant="body").grid(row=0, column=0, sticky="w")
            pkg_short = pkg if len(pkg) <= 48 else pkg[:22] + "…" + pkg[-20:]
            UI.muted(text_col, pkg_short).grid(row=1, column=0, sticky="w")

            if premium:
                pill = ctk.CTkFrame(
                    row, fg_color=soft, corner_radius=12,
                    border_width=1, border_color=accent,
                )
                pill.grid(row=0, column=3, padx=(0, SPACE["3"]), pady=SPACE["2"], sticky="e")
                ctk.CTkLabel(
                    pill,
                    text=f"{score} · {_LEVEL_VI.get(level, level)}",
                    font=get_font("caption"),
                    text_color=accent,
                ).pack(padx=10, pady=5)

            def _toggle_row(_e=None, v=var):
                v.set(not v.get())

            def _row_enter(_e=None, r=row):
                if premium and not var.get():
                    r.configure(border_color=C["border_default"])

            def _row_leave(_e=None, r=row):
                _sync_row_style(pkg, row_widgets[pkg])

            for w in (row, text_col, icon_lbl):
                w.bind("<Button-1>", _toggle_row)
            if premium:
                row.bind("<Enter>", _row_enter)
                row.bind("<Leave>", _row_leave)

            row_widgets[pkg] = {"var": var, "icon_lbl": icon_lbl, "row": row}

        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(fill="x")

        def _cancel() -> None:
            result["value"] = None
            alive["ok"] = False
            close()

        def _confirm() -> None:
            selected = [p for p, w in row_widgets.items() if w["var"].get()]
            if not selected:
                return
            result["value"] = selected
            alive["ok"] = False
            close()

        UI.btn(btns, "Để sau", _cancel, variant="ghost", width=108, height=40).pack(side="right", padx=(SPACE["2"], 0))
        confirm_btn = UI.btn(
            btns,
            f"Gỡ ngay ({len(items)})" if premium else f"Gỡ ({len(items)})",
            _confirm,
            variant="danger" if not premium else "primary",
            width=140 if premium else 120,
            height=40,
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
                if path:
                    images[pkg] = _ctk_image_from_path(path)
                    w["icon_lbl"].configure(image=images[pkg])
                else:
                    w["icon_lbl"].configure(image=placeholder)
            except Exception as exc:
                logging.debug("junk dialog icon %s: %s", pkg, exc)

        def _icon_worker() -> None:
            def load_one(pkg: str, label: str) -> tuple[str, Optional[str]]:
                try:
                    hint = hint_for(pkg) if hint_for else None
                    path = _resolve_icon_path(device_manager, pkg, label, hint)
                    return pkg, path
                except Exception as exc:
                    logging.debug("junk icon %s: %s", pkg, exc)
                    return pkg, None

            with ThreadPoolExecutor(max_workers=10) as pool:
                futures = [pool.submit(load_one, it["package"], it["name"]) for it in items]
                for fu in as_completed(futures):
                    try:
                        pkg, path = fu.result()
                    except Exception:
                        continue
                    if alive["ok"]:
                        root.after(0, lambda p=pkg, ph=path: _apply_icon(p, ph))

        inner._icon_images = images  # noqa: SLF001 — giữ reference CTkImage
        threading.Thread(target=_icon_worker, daemon=True).start()

    show_overlay_panel(parent, _build, max_width=max_w)
    return result["value"]

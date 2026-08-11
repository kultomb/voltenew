"""
Chi tiết phân tích risk — overlay trong app (không cửa sổ OS riêng).
"""

from __future__ import annotations

import re
from collections.abc import Callable

import customtkinter as ctk

from core.ui_theme import C, UI, SPACE, get_font
from core.window_utils import show_overlay_panel

_TONE_COLOR = {
    "danger": C["danger"],
    "warning": C["warning"],
    "muted": C["text_secondary"],
    "safe": C["success"],
    "info": C["text_primary"],
}

_RULE_ROWS = (
    {"rule": "BLACKLIST", "icon": "🔒", "label": "Trạng thái", "hint": "(Đen: nguy hiểm)", "tone": "danger"},
    {"rule": "JUNK_KEYWORDS", "icon": "🧹", "label": "Từ khóa Junk", "hint": "(Trắng: chú ý)", "tone": "muted"},
    {"rule": "AD_NETWORKS", "icon": "📢", "label": "SDK Quảng cáo", "hint": "", "tone": "info"},
    {"rule": "AD_DOMAINS", "icon": "🌐", "label": "Domain QC/Tracker", "hint": "", "tone": "info"},
    {"rule": "PERMISSION_RISK", "icon": "🔑", "label": "Quyền", "hint": "(Đỏ: quyền cao)", "tone": "danger"},
    {"rule": "OVERLAY_BOOT_ADS", "icon": "⚠", "label": "Popup / Boot", "hint": "(Cam: cảnh báo)", "tone": "warning"},
    {"rule": "BEHAVIOR_KEYWORDS", "icon": "⚙", "label": "Hành vi", "hint": "(Cam: cảnh báo)", "tone": "warning"},
    {"rule": "TRUSTED_APP", "icon": "✓", "label": "Đánh giá", "hint": "(Xanh: an toàn)", "tone": "safe"},
)

_REASON_HINTS = (
    ("blacklist", "BLACKLIST"),
    ("từ khóa", "JUNK_KEYWORDS"),
    ("app rác", "JUNK_KEYWORDS"),
    ("ad sdk", "AD_NETWORKS"),
    ("domain", "AD_DOMAINS"),
    ("tracker", "AD_DOMAINS"),
    ("quyền", "PERMISSION_RISK"),
    ("overlay", "OVERLAY_BOOT_ADS"),
    ("boot", "OVERLAY_BOOT_ADS"),
    ("popup", "OVERLAY_BOOT_ADS"),
    ("hành vi", "BEHAVIOR_KEYWORDS"),
    ("chuyển hướng", "BEHAVIOR_KEYWORDS"),
    ("uy tín", "TRUSTED_APP"),
    ("phổ biến", "TRUSTED_APP"),
)


def _reason_text_for_rule(rule: str, reasons: list[str]) -> str:
    for text in reasons:
        low = text.lower()
        for needle, mapped in _REASON_HINTS:
            if mapped == rule and needle in low:
                return text
    return ""


def _short_value(rule: str, reason: str, package: str, app_name: str) -> str:
    if not reason:
        defaults = {
            "BLACKLIST": "Nằm trong BLACKLIST",
            "JUNK_KEYWORDS": "Phát hiện từ khóa app rác",
            "AD_NETWORKS": "Có SDK quảng cáo",
            "AD_DOMAINS": "Có domain quảng cáo/tracker",
            "PERMISSION_RISK": "Quyền nhạy cảm",
            "OVERLAY_BOOT_ADS": "Overlay + Boot + Ads",
            "BEHAVIOR_KEYWORDS": "Dấu hiệu quảng cáo/chuyển hướng",
            "TRUSTED_APP": "Ứng dụng uy tín / phổ biến",
        }
        return defaults.get(rule, "—")

    if rule == "BLACKLIST":
        return "Nằm trong BLACKLIST"

    if rule == "JUNK_KEYWORDS":
        m = re.search(r":\s*(.+)$", reason)
        if m:
            chunk = m.group(1).strip()
            first = chunk.split(",")[0].strip().strip("'\"")
            if first:
                return f"Từ khóa '{first}'"
        for kw in ("clean", "boost", "junk", "virus", "ad"):
            if kw in package.lower() or kw in (app_name or "").lower():
                return f"Từ khóa '{kw}'"
        return "Phát hiện từ khóa app rác"

    if rule in ("AD_NETWORKS", "AD_DOMAINS", "PERMISSION_RISK"):
        m = re.search(r":\s*(.+)$", reason)
        if m:
            return m.group(1).strip()
        return reason

    if rule == "BEHAVIOR_KEYWORDS":
        return "Dấu hiệu quảng cáo/chuyển hướng"

    if rule == "OVERLAY_BOOT_ADS":
        return "Tổ hợp Overlay + Boot + Ads"

    if rule == "TRUSTED_APP":
        return reason.split("—")[0].strip() if "—" in reason else reason

    return reason


def _level_label_vi(level: str) -> str:
    return {
        "safe": "An toàn",
        "low_risk": "Rủi ro thấp",
        "warning": "Cảnh báo",
        "high_risk": "Rủi ro cao",
        "dangerous": "Nguy hiểm",
    }.get(level, level)


def _build_rows(package: str, app_name: str, analysis: dict) -> list[tuple[str, str, str, str, str]]:
    reasons = analysis.get("reasons") or []
    matched = list(analysis.get("matched_rules") or [])
    tags = set(analysis.get("tags") or [])

    if not matched and reasons:
        inferred: set[str] = set()
        for text in reasons:
            low = text.lower()
            for needle, rule in _REASON_HINTS:
                if needle in low:
                    inferred.add(rule)
        matched = sorted(inferred, key=lambda r: next(i for i, s in enumerate(_RULE_ROWS) if s["rule"] == r))

    tag_to_rule = {
        "blacklist": "BLACKLIST",
        "remove_recommended": "BLACKLIST",
        "cleaner": "JUNK_KEYWORDS",
        "ads": "AD_NETWORKS",
        "tracker": "AD_DOMAINS",
        "permissions": "PERMISSION_RISK",
        "behavior": "BEHAVIOR_KEYWORDS",
        "popup": "OVERLAY_BOOT_ADS",
        "boot": "OVERLAY_BOOT_ADS",
        "trusted": "TRUSTED_APP",
    }
    for tag in tags:
        rule = tag_to_rule.get(tag)
        if rule and rule not in matched:
            matched.append(rule)

    rows: list[tuple[str, str, str, str, str]] = [
        ("📁", "Package", package, "", "info"),
    ]

    seen_rules: set[str] = set()
    for spec in _RULE_ROWS:
        rule = spec["rule"]
        if rule not in matched:
            continue
        seen_rules.add(rule)
        reason = _reason_text_for_rule(rule, reasons)
        value = _short_value(rule, reason, package, app_name)
        rows.append((spec["icon"], spec["label"], value, spec["hint"], spec["tone"]))

    if not seen_rules:
        if not reasons:
            rows.append(("ℹ", "Ghi chú", "Không phát hiện rủi ro đáng kể.", "", "safe"))
        else:
            for text in reasons[:6]:
                rows.append(("•", "Chi tiết", text, "", "muted"))

    return rows


def _add_detail_row(
    parent: ctk.CTkFrame,
    icon: str,
    label: str,
    value: str,
    hint: str,
    tone: str,
) -> None:
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", pady=(0, SPACE["2"]))
    row.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(
        row,
        text=icon,
        width=28,
        font=("Segoe UI Symbol", 15),
        text_color="#c8d0dc",
        anchor="w",
    ).grid(row=0, column=0, sticky="nw", padx=(0, SPACE["1"]))

    block = ctk.CTkFrame(row, fg_color="transparent")
    block.grid(row=0, column=1, sticky="ew")

    ctk.CTkLabel(
        block,
        text=f"{label}:",
        font=get_font("body"),
        text_color=C["text_primary"],
        anchor="w",
    ).pack(anchor="w")

    value_row = ctk.CTkFrame(block, fg_color="transparent")
    value_row.pack(anchor="w", fill="x")

    ctk.CTkLabel(
        value_row,
        text=value,
        font=get_font("body_sm"),
        text_color=C["text_primary"],
        anchor="w",
        justify="left",
        wraplength=400,
    ).pack(side="left")

    if hint:
        ctk.CTkLabel(
            value_row,
            text=hint,
            font=get_font("body_sm"),
            text_color=_TONE_COLOR.get(tone, C["text_secondary"]),
            anchor="w",
        ).pack(side="left", padx=(SPACE["1"], 0))


def show_risk_detail(
    parent: ctk.Misc,
    *,
    app_name: str,
    package: str,
    analysis: dict,
) -> None:
    score = int(analysis.get("score", 0))
    level = analysis.get("level", "safe")
    tags = list(analysis.get("tags") or [])
    rows = _build_rows(package, app_name, analysis)

    def _build(inner: ctk.CTkFrame, close: Callable[[], None]) -> None:
        UI.label(inner, "Thông tin Rủi ro", variant="heading").pack(anchor="w", pady=(0, SPACE["1"]))

        level_tone = (
            "danger"
            if level == "dangerous"
            else "warning"
            if level in ("warning", "high_risk")
            else "safe"
        )
        ctk.CTkLabel(
            inner,
            text=f"{app_name}  ·  Điểm {score}  ·  {_level_label_vi(level)}",
            font=get_font("caption"),
            text_color=_TONE_COLOR[level_tone],
            anchor="w",
        ).pack(anchor="w", pady=(0, SPACE["3"]))

        UI.label(inner, "Lý do", variant="body_sm", color=C["text_tertiary"]).pack(anchor="w", pady=(0, SPACE["2"]))

        detail_card = UI.card(inner, padding=SPACE["3"], inset=True)
        detail_card.pack(fill="x", pady=(0, SPACE["4"]))
        detail_inner = UI.card_inner(detail_card)

        for icon, label, value, hint, tone in rows:
            _add_detail_row(detail_inner, icon, label, value, hint, tone)

        if tags:
            tag_head = ctk.CTkFrame(inner, fg_color="transparent")
            tag_head.pack(fill="x", pady=(0, SPACE["2"]))
            ctk.CTkLabel(
                tag_head,
                text="Tags:",
                font=get_font("body_sm"),
                text_color=C["text_tertiary"],
                anchor="w",
            ).pack(side="left")

            tag_wrap = ctk.CTkFrame(inner, fg_color="transparent")
            tag_wrap.pack(fill="x", pady=(0, SPACE["4"]))

            col = 0
            row_i = 0
            max_cols = 4
            for tag in tags:
                pill = ctk.CTkFrame(
                    tag_wrap,
                    fg_color=C["bg_input"],
                    corner_radius=12,
                    border_width=1,
                    border_color=C["border_subtle"],
                )
                ctk.CTkLabel(
                    pill,
                    text=tag,
                    font=get_font("caption"),
                    text_color=C["text_primary"],
                    fg_color="transparent",
                ).pack(padx=12, pady=4)
                pill.grid(row=row_i, column=col, padx=(0, SPACE["1"]), pady=(0, SPACE["1"]), sticky="w")
                col += 1
                if col >= max_cols:
                    col = 0
                    row_i += 1

        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(fill="x")
        UI.btn(btns, "Đóng", close, variant="primary", width=108, height=38).pack(side="right")

        parent.winfo_toplevel().bind("<Return>", lambda _e: close(), add="+")

    show_overlay_panel(parent, _build, max_width=520)

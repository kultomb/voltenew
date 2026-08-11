"""
Chuẩn hóa dòng nhật ký — gọn, nhất quán, bỏ nhiễu (hủy thao tác, cache…).
"""

from __future__ import annotations

import re
from typing import Optional

# Không ghi ra nhật ký
_SKIP = re.compile(
    r"(đã\s+)?h[uủ]y\b|"
    r"tên từ cache|"
    r"bổ sung tên/icon|"
    r"đang bổ sung",
    re.IGNORECASE,
)

_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^Đã kết nối:\s*(.+)$", re.I), r"✓ Kết nối · \1"),
    (re.compile(r"^Đã ngắt kết nối thiết bị\.?$", re.I), "✓ Ngắt kết nối ADB"),
    (re.compile(r"^Chưa kết nối thiết bị!?$", re.I), "⚠ Chưa kết nối thiết bị"),
    (re.compile(r"^Chưa kết nối hoặc chưa bật USB Debug\.?$", re.I), "⚠ Bật USB Debug và kết nối cáp"),
    (re.compile(r"^Đang làm mới danh sách ứng dụng\.+$", re.I), "› Đồng bộ danh sách ứng dụng…"),
    (re.compile(r"^Đã tải (\d+) ứng dụng.*$", re.I), r"✓ Danh sách · \1 ứng dụng"),
    (re.compile(r"^Đang liệt kê launcher.*$", re.I), "› Quét launcher màn hình chính…"),
    (re.compile(r"^Đang gỡ (\d+) launcher.*$", re.I), r"› Gỡ \1 launcher…"),
    (re.compile(r"^Hoàn tất: đã xử lý (\d+) launcher\.?$", re.I), r"✓ Launcher · xong \1 mục"),
    (re.compile(r"^Đã gỡ launcher:\s*(.+)$", re.I), r"✓ Gỡ launcher · \1"),
    (re.compile(r"^Đã vô hiệu hóa launcher:\s*(.+)$", re.I), r"✓ Tắt launcher · \1"),
    (re.compile(r"^Không gỡ được (.+)$", re.I), r"✕ Launcher · \1"),
    (re.compile(r"^Lỗi gỡ launcher (.+)$", re.I), r"✕ Launcher · \1"),
    (re.compile(r"^Lỗi xóa launcher:\s*(.+)$", re.I), r"✕ Launcher · \1"),
    (re.compile(r"^Lỗi quét launcher:\s*(.+)$", re.I), r"✕ Quét launcher · \1"),
    (re.compile(r"^Không tìm thấy launcher nào.*$", re.I), "⚠ Không có launcher trên thiết bị"),
    (re.compile(r"^Không đổi launcher hệ thống:\s*(.+)$", re.I), r"⚠ Không đặt launcher gốc · \1"),
    (re.compile(r"^Đã đặt màn hình chính:\s*(.+)$", re.I), r"✓ Màn hình chính · \1"),
    (re.compile(r"^Đã gửi lệnh đặt HOME:\s*(.+)$", re.I), r"✓ Đặt màn hình chính · \1"),
    (re.compile(r"^Cảnh báo:\s*(.+)$", re.I), r"⚠ \1"),
    (re.compile(r"^Đang quét ứng dụng rác\.+$", re.I), "› Quét ứng dụng rác…"),
    (re.compile(r"^Đang gỡ (\d+) ứng dụng.*$", re.I), r"› Gỡ \1 ứng dụng…"),
    (re.compile(r"^Đã gỡ (\d+) ứng dụng rác$", re.I), r"✓ Đã gỡ \1 ứng dụng rác"),
    (re.compile(r"^Đã gỡ:\s*(.+)$", re.I), r"✓ Đã gỡ · \1"),
    (re.compile(r"^Không tìm thấy ứng dụng rác\.?$", re.I), "✓ Quét rác · không phát hiện"),
    (re.compile(r"^Lỗi quét:\s*(.+)$", re.I), r"✕ Quét rác · \1"),
    (re.compile(r"^Quét xong: phát hiện (\d+) app.*$", re.I), r"✓ Quét nhanh · \1 app đề xuất gỡ"),
    (re.compile(r"^Quét xong — không phát hiện.*$", re.I), "✓ Quét nhanh · sạch"),
    (re.compile(r"^Bắt đầu quét nhanh AI\.+$", re.I), "› Quét nhanh AI…"),
    (re.compile(r"^Bật giám sát thời gian thực\.+$", re.I), "› Bật giám sát realtime…"),
    (re.compile(r"^Giám sát đã bật!?$", re.I), "✓ Giám sát realtime đang chạy"),
    (re.compile(r"^Đã dừng giám sát!?$", re.I), "✓ Đã dừng giám sát"),
    (re.compile(r"^Mất kết nối ADB, dừng giám sát\.+$", re.I), "⚠ Mất ADB · dừng giám sát"),
    (re.compile(r"^Phát hiện quảng cáo từ:\s*(.+)$", re.I), r"⚠ QC · \1"),
    (re.compile(r"^Popup từ:\s*(.+)$", re.I), r"⚠ Popup · \1"),
    (re.compile(r"^Đang thiết lập AdGuard DNS\.+$", re.I), "› Cấu hình DNS AdGuard…"),
    (re.compile(r"^Đã đặt DNS:\s*(.+)$", re.I), r"✓ DNS · \1"),
    (re.compile(r"^Lỗi DNS:\s*(.+)$", re.I), r"✕ DNS · \1"),
    (re.compile(r"^Kiểm tra ứng dụng rác đang chạy\.+$", re.I), "› Kiểm tra app đang mở…"),
    (re.compile(r"^Ứng dụng đang chạy:\s*(.+)$", re.I), r"› Foreground · \1"),
    (re.compile(r"^Phát hiện rác đang chạy:\s*(.+)$", re.I), r"⚠ App rác · \1"),
    (re.compile(r"^Không phải rác:\s*(.+)$", re.I), r"✓ App an toàn · \1"),
    (re.compile(r"^Bỏ qua app được bảo vệ.*:\s*(.+)$", re.I), r"› Bỏ qua (bảo vệ) · \1"),
    (re.compile(r"^Bỏ qua launcher được bảo vệ:\s*(.+)$", re.I), r"› Bỏ qua (bảo vệ) · \1"),
    (re.compile(r"^Lỗi tải danh sách:\s*(.+)$", re.I), r"✕ Danh sách · \1"),
    (re.compile(r"^Không tìm thấy ứng dụng bên thứ ba.*$", re.I), "⚠ Không có app cài thêm — thử Làm mới"),
    (re.compile(r"^Đang reload kết nối ADB\.+$", re.I), "› Khởi động lại ADB…"),
    (re.compile(r"^Reloading ADB\.+$", re.I), "› Khởi động lại ADB…"),
    (re.compile(r"^Lỗi reload ADB:\s*(.+)$", re.I), r"✕ ADB · \1"),
]


def polish_log(message: str) -> str:
    text = (message or "").strip()
    if not text:
        return text
    if text[0] in "›✓⚠✕":
        return text
    for pattern, repl in _RULES:
        if pattern.match(text):
            return pattern.sub(repl, text)
    if re.match(r"^Đang ", text, re.I):
        body = text[5:].rstrip(".!")
        return f"› {body}…"
    if re.match(r"^Lỗi ", text, re.I):
        return f"✕ {text[5:]}"
    if re.match(r"^Đã ", text, re.I) and not text.startswith("✓"):
        return f"✓ {text}"
    return text


def prepare_log_line(message: str) -> Optional[str]:
    """Trả về dòng đã chuẩn hóa, hoặc None nếu không ghi."""
    raw = (message or "").strip()
    if not raw:
        return None
    if _SKIP.search(raw):
        return None
    return polish_log(raw)

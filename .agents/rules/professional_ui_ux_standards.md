# Quy Tắc Thiết Kế Giao Diện & Kiến Trúc Chuyên Nghiệp (Professional Mobile Tool UI/UX & Architecture Rules)

Tài liệu này quy định các tiêu chuẩn thiết kế UI/UX và kiến trúc xử lý phần mềm cho toàn bộ dự án Tool Android / VoLTE Fixer để đảm bảo trải nghiệm người dùng đẳng cấp và chuyên nghiệp nhất.

---

## 🎨 1. QUY TẮC NÚT BẤM GIAO DIỆN (DYNAMIC TOGGLE BUTTONS)
- **Tuyệt đối không tạo nút Hủy/Dừng tách rời thành dòng riêng**: Việc để nút Dừng làm 1 hàng cố định bên dưới làm giao diện bị rối và nghiệp dư.
- **Sử dụng Nút bấm Biến hình Trạng thái (Dynamic Toggle Button)**:
  - Khi ở trạng thái chờ: Hiển thị tên tính năng chính (Ví dụ: `⚡ BROM 1-CLICK: TỰ ĐỘNG RÚT ➔ VÁ ➔ NẠP VENDOR` - Màu Cam/Xanh).
  - Khi đang thực thi tiến trình: **Chính nút đó tự đổi thành Nút Dừng** (Nội dung: `🛑 DỪNG TIẾN TRÌNH (STOP)` - Màu Đỏ) và vẫn cho phép người dùng bấm vào để HỦY tiến trình ngầm ngay lập tức.
  - Khi tiến trình hoàn tất hoặc bị hủy: Nút tự động chuyển về trạng thái ban đầu.

---

## 📺 2. QUY TẮC NHẬT KÝ CONSOLE LOG (CLEAN & CONCISE LOGGING)
- **Lọc sạch rác ANSI & Debug Spam**: Xóa toàn bộ các mã màu ANSI nhị phân (`\x1b[31m`, `[0m`) và các dòng log spam lặp đi lặp lại của thư viện C/C++ (`DeviceClass`, `Couldn't get device configuration`, `Hint:`...).
- **In log theo đúng thứ tự thời gian thực (Chronological Order)**:
  - Chưa kết nối thiết bị $\rightarrow$ Chỉ in log đứng chờ cắm cáp (`⌛ Đang đứng chờ kết nối...`).
  - Khi phát hiện thiết bị kết nối thành công $\rightarrow$ Mới bắt đầu in các Bước thực thi (`✓ Đã kết nối -> Bước 1 -> Bước 2`).
- **Không dùng Popup phiền nhiễu**: Hạn chế dùng các hộp thoại xác nhận lặt vặt (`messagebox.askyesno`). Hướng dẫn thao tác được in trực tiếp vào khung log bằng màu sắc cảnh báo nhẹ nhàng.

---

## ⚡ 3. QUY TẮC QUẢN LÝ TIẾN TRÌNH NGẦM (PROCESS WATCHDOG & CANCELLATION)
- **Luôn có cờ Hủy tiến trình (Cancel Token / Process Kill)**: Khi người dùng bấm dừng hoặc rút cáp USB, tiến trình con (`subprocess`) phải bị tiêu diệt ngay lập tức, không được chạy ngầm đơ máy.
- **Tự động dọn dẹp khi thoát (App Shutdown Cleanup)**: Khi đóng ứng dụng (`on_closing`), tự động kill toàn bộ subprocess và thread ngầm.
- **Thời gian Timeout hợp lý**: Không để thời gian chờ quá lâu làm đơ nút; đặt timeout từ 30s - 40s kèm bộ đếm hủy tự động.

---

## 💾 4. QUY TẮC AN TOÀN DỮ LIỆU & TIÊU CHUẨN NẠP BẢN VÁ
- **Bảo toàn kích thước Byte 100%**: Bản vá tệp đĩa `vendor.img` phải giữ nguyên 100% dung lượng byte gốc để tránh gây brick máy.
- **Không Hardcode cứng**: Mọi thuật toán vá phải sử dụng quét mẫu nhị phân động (Universal Binary Pattern Matching) tự nhận diện chip và offset.
- **Chuẩn hóa Tên tệp xuất ra**: Tệp bản vá đầu ra phải luôn đưa tiền tố **`PATCHED_` VIẾT HOA LÊN ĐẦU** (Ví dụ: `PATCHED_VENDOR_OPPO_F9_CPH1823_ANDROID_10.IMG`).

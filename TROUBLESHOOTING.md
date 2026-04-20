# Auto_login_wifi — Troubleshooting Guide

Tài liệu này giúp bạn xử lý các lỗi thường gặp khi chạy project `auto-connect-wifi`.

## 1) Chạy trên Linux/macOS bị báo không có `netsh`

### Triệu chứng
- Khi chạy lệnh CLI như:
  - `python main.py --list`
  - `python main.py --show "MyWifi"`
- Chương trình báo tool chỉ hỗ trợ Windows.

### Nguyên nhân
- Project dùng `netsh` (công cụ mạng của Windows), nên **không chạy được trên Linux/macOS**.

### Cách xử lý
- Chạy ứng dụng trên Windows 10/11.
- Nếu đang dùng máy ảo/CI, hãy dùng runner Windows.

---

## 2) Không export/import được profile

### Triệu chứng
- Lệnh export/import trả về lỗi quyền truy cập hoặc không thành công.

### Nguyên nhân
- Một số thao tác `netsh wlan export/add/delete` cần quyền cao hơn tùy cấu hình máy.

### Cách xử lý
- Mở PowerShell/CMD bằng **Run as Administrator** rồi chạy lại.
- Kiểm tra đường dẫn thư mục `profiles/` có quyền ghi.

---

## 3) Kết nối profile thất bại dù đã import XML

### Triệu chứng
- Import thành công nhưng connect không thành công.

### Checklist xử lý
1. Mở `Show Details` để kiểm tra profile đã xuất hiện chưa.
2. Xác nhận SSID đúng chính tả (phân biệt ký tự đặc biệt).
3. Kiểm tra mật khẩu trong XML (`<keyMaterial>`) có chính xác không.
4. Thử xóa profile cũ và import lại bản XML mới.

---

## 4) XML bị lỗi khi SSID/password có ký tự đặc biệt

### Triệu chứng
- Add profile lỗi với SSID/password chứa ký tự như `&`, `<`, `>`, `"`, `'`.

### Trạng thái hiện tại
- Project đã escape ký tự đặc biệt khi tạo XML tự động trong `create_and_add_profile`, nên lỗi này đã được giảm đáng kể.

### Khuyến nghị
- Vẫn nên tránh copy/paste thêm khoảng trắng thừa trong SSID/password.

---

## 5) Vì sao `requirements.txt` gần như trống?

### Giải thích
- GUI dùng `tkinter`, là thư viện đi kèm Python chuẩn trên Windows.
- Vì vậy project hiện **không yêu cầu package ngoài** để chạy những chức năng cơ bản.

---

## 6) Gợi ý debug nhanh

- Chạy kiểm tra cú pháp:
  ```bash
  python -m py_compile main.py gui_main.py
  ```
- Test nhanh CLI:
  ```bash
  python main.py --list
  python main.py --show "TenProfile"
  ```

---

Nếu bạn muốn, mình có thể viết thêm:
- `CHANGELOG.md` theo version (SemVer),
- `CONTRIBUTING.md` cho team dev,
- hoặc tài liệu deploy `.exe` + installer chi tiết hơn cho người dùng cuối.

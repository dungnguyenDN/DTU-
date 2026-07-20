# Kiến trúc hệ thống

## Sơ đồ 3 tầng

```
┌─────────────────────────────────────────────────────────────┐
│  TẦNG 1 — GIAO DIỆN (frontend/)                              │
│  ├─ platform/index.html   Nền tảng quản lý (6 module, cần    │
│  │                        đăng nhập vai trò "quan_ly")       │
│  └─ portal/index.html     Cổng chia sẻ nội dung (giảng viên, │
│                            đăng nhập vai trò bất kỳ)          │
└───────────────────────────┬─────────────────────────────────┘
                             │ fetch() qua HTTP + JWT Bearer token
┌───────────────────────────▼─────────────────────────────────┐
│  TẦNG 2 — BACKEND API (backend/)                              │
│  Flask + SQLite — chạy thật, có kiểm thử tự động             │
│  ├─ routes/        7 nhóm endpoint (auth, content, teachers, │
│  │                 kpi, chatbot, benchmark, funnel)           │
│  ├─ services/      logic nghiệp vụ tách riêng (dễ kiểm thử)  │
│  │   ├─ analytics_service.py  tier, funnel, engagement rate  │
│  │   └─ ai_service.py         Claude API + fallback rule-based│
│  ├─ auth.py         JWT + băm mật khẩu (pbkdf2, không cần    │
│  │                   thư viện ngoài bcrypt)                    │
│  └─ database.py     schema SQLite, 8 bảng                     │
└───────────────────────────┬─────────────────────────────────┘
                             │ (tuỳ chọn, mở rộng)
┌───────────────────────────▼─────────────────────────────────┐
│  TẦNG 3 — TỰ ĐỘNG HOÁ MỞ RỘNG (n8n-workflows/) — TUỲ CHỌN     │
│  4 workflow n8n cho các tác vụ cần tích hợp bên ngoài thật:   │
│  đăng Facebook thật, gửi email nhắc nhở hàng loạt, gọi        │
│  Facebook Insights API định kỳ. Backend Python đã tự xử lý   │
│  toàn bộ logic nghiệp vụ cốt lõi — n8n chỉ cần khi muốn nối   │
│  thêm dịch vụ bên thứ ba theo kiểu low-code.                  │
└─────────────────────────────────────────────────────────────┘
```

## Vì sao chọn Flask + SQLite thay vì FastAPI + PostgreSQL?

Ở quy mô đề tài nghiên cứu khoa học cấp trường (demo, không phải hệ thống production phục vụ hàng chục nghìn người dùng đồng thời), Flask + SQLite mang lại:

- **Không phụ thuộc dịch vụ ngoài**: SQLite là 1 file, không cần cài đặt server database riêng, dễ triển khai trên máy cá nhân hoặc server nhỏ.
- **Dễ kiểm thử**: `sqlite3` và `Flask.test_client()` đều là công cụ chuẩn, không cần mock phức tạp.
- **Dễ đọc cho hội đồng chấm**: mã nguồn tường minh, không có lớp trừu tượng ORM phức tạp (SQL thuần, dễ đối chiếu với thiết kế cơ sở dữ liệu trong báo cáo).
- **Có đường nâng cấp rõ ràng**: khi triển khai thật với lượng truy cập lớn, chỉ cần đổi `database.py` sang dùng PostgreSQL (SQLAlchemy) mà không phải viết lại route/service.

## Luồng xác thực (Authentication flow)

1. Người dùng nhập email/mật khẩu tại `loginOverlay`.
2. Frontend gọi `POST /api/auth/login`.
3. Backend kiểm tra mật khẩu (băm bằng PBKDF2-SHA256, 260,000 vòng lặp, có salt ngẫu nhiên).
4. Nếu đúng, backend trả về **JWT token** (hết hạn sau 8 giờ mặc định) chứa `id`, `vai_tro`, `ho_ten`.
5. Frontend lưu token trong **biến JavaScript** (không dùng `localStorage`/`sessionStorage` — tránh rủi ro XSS đọc token, đồng thời tương thích với môi trường xem trước dạng artifact). Hệ quả: tải lại trang sẽ yêu cầu đăng nhập lại — chấp nhận được cho bản demo.
6. Mỗi request tiếp theo gắn `Authorization: Bearer <token>`.
7. Backend giải mã token, kiểm tra hạn và vai trò (`@login_required(role="quan_ly")`) trước khi cho phép truy cập.

## Vòng phản hồi khép kín — hiện thực hoá bằng API thật

Đây là điểm khác biệt cốt lõi của đề tài, nay đã có endpoint thật thay vì chỉ mô tả bằng lời:

1. Thí sinh hỏi chatbot → `POST /api/chatbot/hoi` → ghi vào bảng `chat_log`.
2. Quản lý xem chủ đề nổi bật → `GET /api/chatbot/chu-de-noi-bat` (gom nhóm theo từ khoá FAQ khớp được).
3. Quản lý bấm "Tạo gợi ý nội dung" → `POST /api/chatbot/tao-goi-y-tu-chu-de` → **tự động chèn dòng mới vào bảng `lich_noi_dung`** với trạng thái "chờ soạn".
4. Dòng mới xuất hiện ngay trong tab Lịch nội dung — kiểm chứng được bằng cách gọi `GET /api/content?trang_thai=cho_soan` (đã test tự động trong `backend/tests/test_backend.py`).

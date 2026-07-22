# Hướng dẫn deploy lên internet

Sản phẩm gồm 2 phần deploy tách rời — cách chuẩn của một ứng dụng web thật:

| Phần | Deploy ở đâu | Vì sao |
|---|---|---|
| `backend/` (Flask + SQLite) | **Render.com** — có sẵn `render.yaml`, deploy 1 cú click | Cần chạy Python liên tục, có ổ đĩa lưu SQLite |
| `frontend/` (HTML/CSS/JS tĩnh) | **Netlify** — kéo-thả thư mục | Chỉ là file tĩnh, không cần build |

Toàn bộ cấu hình đã chuẩn bị sẵn: `render.yaml` (blueprint backend), `frontend/config.js` (điểm cấu hình API duy nhất), `frontend/netlify.toml`, `Dockerfile` (gunicorn). Bạn chỉ cần bấm theo các bước dưới.

---

## Bước 0 — Đưa mã nguồn lên GitHub (~5 phút)

Repo đã được khởi tạo git sẵn (đã có commit đầu tiên). Chỉ cần đẩy lên GitHub:

```bash
# Tạo repo trống trên github.com (không thêm README), rồi:
git remote add origin https://github.com/<tài-khoản>/<tên-repo>.git
git branch -M main
git push -u origin main
```

> Nếu chưa có commit: `git add . && git commit -m "Deploy DTU platform"` trước khi push.

---

## Bước 1 — Deploy backend lên Render (~10 phút, 1 cú click nhờ Blueprint)

1. Vào [render.com](https://render.com) → đăng nhập bằng GitHub.
2. **New → Blueprint** → chọn repo vừa push. Render tự đọc `render.yaml` và điền sẵn:
   - Web service `dtu-backend`, gói **Free**
   - Build: `pip install -r requirements.txt`
   - Start: `python seed_data.py && gunicorn app:app ...` (WSGI production)
   - `SECRET_KEY` tự sinh, health check `/api/health`, SQLite ghi vào `/tmp`

> **Dữ liệu bền vững:** `render.yaml` đã khai báo sẵn một **PostgreSQL free** (`dtu-db`) và tự nối vào backend qua `DATABASE_URL`. Nhờ đó tài khoản mới, đổi vai trò, bài đã duyệt, lead... được **lưu vĩnh viễn**, không reset khi server ngủ. Khi push thay đổi có thêm database, vào Render → Blueprint của bạn → **Approve/Sync** để Render tạo Postgres và nối vào (hoặc tạo Postgres thủ công rồi thêm biến `DATABASE_URL` = *Internal Database URL* vào service).
3. (Tùy chọn) Điền `ANTHROPIC_API_KEY` trong tab **Environment** để chatbot/soạn caption dùng Claude thật. Bỏ trống vẫn chạy đầy đủ ở chế độ AI offline.
4. Bấm **Apply** → Render build & deploy, trả về URL dạng `https://dtu-backend.onrender.com`.
5. Kiểm tra: mở `https://dtu-backend.onrender.com/api/health` — phải thấy `{"status":"ok"}`.

> **Gói Free của Render** cho server "ngủ" sau ~15 phút không có request; lần gọi đầu sau đó mất 30–60 giây để "thức". Trước giờ demo, mở link trước 5–10 phút cho server sẵn sàng.

---

## Bước 2 — Trỏ frontend về backend (sửa DUY NHẤT 1 dòng)

Mở `frontend/config.js`, đổi dòng `PRODUCTION_API_BASE` thành URL backend ở Bước 1:

```js
var PRODUCTION_API_BASE = "https://dtu-backend.onrender.com/api";
```

Cả 4 trang (trang chủ, tuyển sinh, quản lý, cổng giảng viên) và trang báo cáo đều đọc chung file này — không cần sửa chỗ nào khác. Khi chạy ở `localhost` nó tự dùng backend local nên không ảnh hưởng lúc phát triển.

Commit lại: `git commit -am "Cấu hình API production" && git push`.

---

## Bước 3 — Deploy frontend lên Netlify (~3 phút)

**Cách nhanh nhất (kéo-thả):**
1. Vào [app.netlify.com/drop](https://app.netlify.com/drop).
2. Kéo-thả **toàn bộ thư mục `frontend/`** vào trang.
3. Netlify trả về link dạng `https://ten-ngau-nhien.netlify.app`.

Mở link — trang chủ (`index.html`) hiện ra với 3 lối vào. Thử lần lượt:
- `/` — trang chủ điều hướng
- `/tuyensinh/index.html` — trang công khai + chatbot
- `/platform/index.html` — đăng nhập quản lý
- `/portal/index.html` — đăng nhập giảng viên

> Muốn deploy tự động khi push GitHub: **Netlify → Add new site → Import from Git**, chọn repo, đặt **Base directory** = `frontend`, **Publish directory** = `frontend`.

---

## Chạy thử local trước khi deploy (khuyến nghị)

```bash
# Cách 1 — Docker (1 lệnh, có cả backend + frontend + gunicorn):
docker compose up --build
# Mở http://localhost:8080

# Cách 2 — không cần Docker:
bash run.sh
```

Chạy bộ kiểm thử (47 test) để chắc chắn mọi thứ nguyên vẹn:
```bash
cd backend && python -m unittest discover -s tests -v
```

---

## Tài khoản demo

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Quản lý | `truyenthong@duytan.edu.vn` | `DemoPass123!` |
| Giảng viên | `nguyenvana@duytan.edu.vn` | `DemoPass123!` |

Trang tuyển sinh công khai không cần đăng nhập.

---

## Lưới an toàn cho buổi bảo vệ

1. **Đánh thức server** 5–10 phút trước giờ demo (mở link backend + frontend).
2. **Quay video dự phòng** toàn luồng demo 3–5 phút phòng khi mạng hội trường chập chờn.
3. **Hotspot 4G** cá nhân làm mạng dự phòng.
4. Muốn giữ dữ liệu tích lũy qua nhiều lần demo: xóa lời gọi `clear_all()` trong `seed_data.py` sau lần deploy đầu (mặc định mỗi lần khởi động sẽ seed lại sạch).

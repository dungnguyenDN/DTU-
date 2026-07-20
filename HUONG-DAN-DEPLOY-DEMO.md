# Hướng dẫn deploy lên internet để demo hội đồng chấm

Kiến trúc giờ đã có backend Python thật, nên việc deploy đơn giản và chuẩn hơn nhiều so với
cách "publish Google Sheet dạng CSV" trước đây — không cần thủ thuật, đây là cách một ứng dụng
web thật được triển khai.

## Tổng quan: 2 phần cần deploy

| Phần | Deploy ở đâu | Vì sao |
|---|---|---|
| `backend/` | Render.com hoặc Railway.app (có gói miễn phí) | Cần chạy Python liên tục, có ổ đĩa lưu SQLite |
| `frontend/` | Netlify (kéo-thả, miễn phí) | Chỉ là file tĩnh HTML/CSS/JS |

## Bước 1 — Deploy backend lên Render.com (~15 phút)

1. Đưa toàn bộ project lên GitHub (repo riêng hoặc public tuỳ ý).
2. Vào [render.com](https://render.com) → **New → Web Service** → chọn repo vừa tạo.
3. Cấu hình:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python seed_data.py && python app.py`
   - **Instance Type**: Free
4. Thêm biến môi trường trong tab **Environment**:
   - `SECRET_KEY` = một chuỗi ngẫu nhiên dài
   - `ANTHROPIC_API_KEY` = (điền nếu có, để trống vẫn chạy được ở chế độ fallback)
   - `CORS_ALLOWED_ORIGINS` = `*` (hoặc domain Netlify ở bước 2 để chặt chẽ hơn)
5. Deploy — Render trả về URL dạng `https://ten-app.onrender.com`.
6. Kiểm tra: mở `https://ten-app.onrender.com/api/health` — phải thấy `{"status":"ok"}`.

> **Lưu ý về gói Free của Render:** server sẽ "ngủ" sau ~15 phút không có request, lần truy cập
> đầu tiên sau đó sẽ mất khoảng 30-60 giây để "đánh thức". Trước giờ demo, hãy mở link trước
> 5-10 phút để server sẵn sàng khi hội đồng xem.

## Bước 2 — Deploy frontend lên Netlify (~5 phút)

1. Trước khi deploy, sửa `DTU_API_BASE` trong 2 file frontend để trỏ về backend thật.
   Cách sạch nhất: thêm dòng này vào đầu thẻ `<head>` của cả `platform/index.html` và `portal/index.html`:
   ```html
   <script>window.DTU_API_BASE = "https://ten-app.onrender.com/api";</script>
   ```
2. Vào [app.netlify.com/drop](https://app.netlify.com/drop) → kéo thả **toàn bộ thư mục `frontend/`**.
3. Netlify trả về link dạng `https://ten-ngau-nhien.netlify.app`.
4. Test cả 2 đường dẫn: `.../platform/index.html` và `.../portal/index.html`.

## Bước 3 — Nhập dữ liệu thật/thực tế trước khi demo

Dữ liệu mẫu (`seed_data.py`) đủ để demo, nhưng nếu muốn dữ liệu sát với ngành đào tạo thật của
Đại học Duy Tân, sửa trực tiếp `backend/seed_data.py` (thay tên giảng viên, chủ đề nội dung, câu
hỏi FAQ...) rồi deploy lại — Render sẽ tự chạy lại `seed_data.py` mỗi lần khởi động.

**Lưu ý:** `seed_data.py` xoá sạch dữ liệu cũ trước khi tạo mới (`clear_all()`). Nếu muốn giữ dữ liệu
tích lũy qua nhiều lần demo, xoá dòng gọi `clear_all()` trong `seed()` sau lần deploy đầu tiên.

## Bước 4 — Lưới an toàn cho buổi bảo vệ

1. **Quay màn hình dự phòng**: quay lại toàn bộ luồng demo (đăng nhập → xem 6 tab → bấm nút chia sẻ
   → hỏi chatbot) thành video 3-5 phút, phòng khi wifi hội trường không ổn định.
2. **Kiểm tra lại đúng 1 tiếng trước giờ bảo vệ**: mở cả 2 link, đăng nhập thử, đảm bảo backend
   Render đã "thức" (xem lưu ý ở Bước 1).
3. Chuẩn bị hotspot 4G cá nhân làm mạng dự phòng.

## Kịch bản demo gợi ý (10-15 phút)

1. Mở `platform` → đăng nhập bằng tài khoản quản lý → đi qua từng tab theo đúng mạch đề cương:
   Benchmark đối thủ (Nội dung 1) → Lịch nội dung (Nội dung 2) → Giảng viên (chỉ tiêu 5 bài) →
   Chatbot (bấm "Tạo gợi ý nội dung" để hội đồng thấy vòng phản hồi khép kín chạy thật) →
   Phễu chuyển đổi (thước đo hiệu quả cuối cùng).
2. Mở `portal` trên điện thoại → đăng nhập tài khoản giảng viên → bấm "Chia sẻ ngay" → cho thấy
   khung chia sẻ Facebook mở thật, tiến độ tăng lên thật.
3. Mở tab trình duyệt khác gọi `GET /api/health` hoặc chạy `python backend/scripts/smoke_test.py`
   trước mặt hội đồng (nếu phù hợp) để chứng minh có bộ kiểm thử tự động thật, không chỉ giao diện đẹp.

# Nền tảng quản lý truyền thông tuyển sinh — Đại học Duy Tân

Sản phẩm ứng dụng của đề tài nghiên cứu khoa học cấp trường: *"Giải pháp truyền thông - marketing số nhằm gia tăng độ nhận diện và sức lan tỏa cho các ngành đào tạo tại Đại học Duy Tân"*.

Đây là **dự án phần mềm hoàn chỉnh, chạy được thật** — không phải giao diện tĩnh minh hoạ:
backend Python có cơ sở dữ liệu, xác thực, logic nghiệp vụ thật và **47 kiểm thử tự động đều PASS**.

## Cấu trúc dự án

```
dtu-project/
├── backend/                Flask + SQLite — API thật, có test tự động
│   ├── app.py               điểm khởi động ứng dụng
│   ├── config.py             cấu hình qua biến môi trường
│   ├── database.py           schema SQLite (8 bảng)
│   ├── auth.py                JWT + băm mật khẩu
│   ├── seed_data.py           tạo dữ liệu mẫu thực tế
│   ├── routes/                 7 nhóm API endpoint
│   ├── services/                logic nghiệp vụ (AI, phân tích số liệu)
│   ├── tests/                    22 test tự động (unittest, không cần cài thêm)
│   ├── scripts/smoke_test.py      kiểm thử toàn trình end-to-end
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/                Giao diện — gọi thẳng API backend (không còn dữ liệu giả)
│   ├── tuyensinh/index.html  Trang tuyển sinh CÔNG KHAI — thí sinh/phụ huynh hỏi chatbot,
│   │                          không cần đăng nhập (đúng thiết kế trong đề cương)
│   ├── platform/index.html   Nền tảng quản lý (6 tab, đăng nhập vai trò quản lý)
│   ├── portal/index.html      Cổng chia sẻ nội dung (đăng nhập giảng viên)
│   └── assets/logo.png
├── n8n-workflows/            4 workflow — MỞ RỘNG TUỲ CHỌN (xem README riêng)
├── docs/
│   ├── ARCHITECTURE.md        giải thích kiến trúc 3 tầng
│   └── API_REFERENCE.md       tài liệu toàn bộ endpoint
├── docker-compose.yml        chạy cả hệ thống bằng 1 lệnh
└── run.sh                    chạy không cần Docker
```

## Chạy thử trong 1 phút

**Cách 1 — Docker (khuyến nghị, không cần cài Python/thư viện):**
```bash
docker compose up --build
```
Mở `http://localhost:8080/platform/index.html`

**Cách 2 — không cần Docker:**
```bash
bash run.sh
```

Sau khi chạy, hệ thống tự tạo sẵn dữ liệu mẫu và 2 tài khoản demo:

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Quản lý (xem Nền tảng quản lý) | `truyenthong@duytan.edu.vn` | `DemoPass123!` |
| Giảng viên (xem Cổng chia sẻ) | `nguyenvana@duytan.edu.vn` | `DemoPass123!` |

## Ba giao diện — ba đối tượng người dùng (đúng thiết kế đề cương)

| Giao diện | Ai dùng | Đăng nhập? | Mở link |
|---|---|---|---|
| **Trang tuyển sinh** | Thí sinh, phụ huynh (người ngoài) | **KHÔNG** — công khai | `/tuyensinh/index.html` |
| Nền tảng quản lý | Phòng truyền thông | Có, vai trò quản lý | `/platform/index.html` |
| Cổng chia sẻ | Giảng viên, nhân viên | Có | `/portal/index.html` |

Trang tuyển sinh là nơi người ngoài trò chuyện với **chatbot AI thật** (gọi `POST /api/chatbot/hoi`),
xem tin tuyển sinh **đọc trực tiếp từ database** (các bài trạng thái "đã đăng" trong Lịch nội dung).
Mọi câu hỏi thí sinh đặt ở đây được ghi vào `chat_log` — và hiện lên ngay tab Chatbot của Nền tảng
quản lý, nuôi tiếp vòng phản hồi khép kín.

## Cổng chia sẻ giảng viên — AI đề xuất bài đăng theo mùa vụ

Cổng chia sẻ (`/portal/index.html`) là dashboard hoàn chỉnh dành cho giảng viên:

- **AI đề xuất theo mùa** (`GET /api/content/goi-y-mua-vu`): hệ thống nhận diện giai đoạn
  truyền thông hiện tại theo lịch tuyển sinh Việt Nam (tư vấn hướng nghiệp → mùa thi →
  cao điểm xét tuyển → nhập học → gắn kết), chấm điểm mức phù hợp 0-100 cho từng bài
  đã duyệt (khớp mùa + độ gần ngày đăng + tỷ lệ tương tác lịch sử) kèm **lý do đề xuất**
  và **khung giờ vàng** nên đăng. Logic trong `backend/services/season_service.py`, có unit test.
- **AI viết lại caption theo giọng cá nhân** (`POST /api/content/<id>/caption-ca-nhan`):
  giảng viên chọn giọng văn (thân thiện / chuyên nghiệp / truyền cảm hứng), hệ thống viết lại
  bài fanpage thành bài chia sẻ Facebook cá nhân — dùng Claude nếu có API key, fallback
  rule-based vẫn cho caption dùng được ngay khi demo offline.
- **Gamification**: thẻ thống kê cá nhân (tiến độ vòng tròn, lượt click, cấp bậc
  Đồng/Bạc/Vàng/Kim Cương, thứ hạng), bảng xếp hạng lan toả toàn trường, biểu đồ hoạt động
  7 ngày, dòng thời gian lịch sử chia sẻ, hiệu ứng chúc mừng khi đạt chỉ tiêu 5 bài/đợt,
  và **6 huy hiệu thành tích** (Khởi động, Đạt chỉ tiêu, Chuỗi 3 ngày, Nam châm click,
  Lan toả đa ngành, Top 3) có thanh tiến độ mở khoá — logic trong `services/badge_service.py`.
- **Mô phỏng What-if** (tab Phễu chuyển đổi của Nền tảng quản lý): kéo thanh trượt
  "N giảng viên × M bài/đợt" để dự báo lượt click, hồ sơ nộp và nhập học tăng thêm —
  dự báo tính từ tỷ lệ thật trong DB (`GET /api/funnel/mo-phong`), minh chứng định lượng
  cho giá trị kênh giảng viên nêu trong đề cương.
- Mỗi lượt chia sẻ được gắn **link UTM định danh giảng viên** để đo lượt click quy về từng người.

## Kiểm thử tự động

```bash
cd backend
python3 -m unittest discover -s tests -v
```
Kết quả: **47/47 test PASS** — bao gồm kiểm thử băm mật khẩu, JWT, phân quyền (RBAC), logic tính cấp bậc giảng viên, logic phễu chuyển đổi, khớp FAQ chatbot, logic AI đề xuất theo mùa vụ, cá nhân hoá caption, huy hiệu thành tích, mô phỏng What-if, AI lập kế hoạch tháng, A/B caption, đa kênh, thu lead, và toàn bộ endpoint API qua `Flask.test_client()`.

## Các tính năng mở rộng (đã chạy thật, có test)

| Tính năng | Ở đâu | Endpoint |
|---|---|---|
| AI lập kế hoạch nội dung tháng | Platform → Lịch nội dung | `POST /api/content/ke-hoach-thang` |
| A/B testing caption (2 phong cách, chọn biến thể thắng) | Platform → Lịch nội dung | `POST /api/content/<id>/ab-caption` |
| Chatbot thu lead + quản lý trạng thái | Trang tuyển sinh + Platform → Lead tư vấn | `POST /api/chatbot/lead` |
| Báo cáo tuần in được (PDF qua Ctrl+P) | Platform → nút "Xuất báo cáo tuần" | `frontend/platform/bao-cao.html` |
| Thi đua giữa các khoa | Portal | `GET /api/teachers/bang-xep-hang-khoa` |
| Đa kênh: Facebook / Zalo / kịch bản TikTok | Portal → modal bài viết | `POST /api/content/<id>/da-kenh` |
| Poster QR cá nhân (offline-to-online, UTM định danh) | Portal → modal bài viết | tạo phía client, QR qua api.qrserver.com (có fallback) |

Kiểm thử toàn trình (chạy server thật, gọi qua HTTP như người dùng thật):
```bash
python3 backend/scripts/smoke_test.py
```

## Vì sao mỗi tab của Nền tảng quản lý là API thật, không phải số liệu giả

| Tab | Endpoint đứng sau | Logic thật đã kiểm thử |
|---|---|---|
| Tổng quan KPI | `GET /api/kpi/tong-quan` | Tổng hợp SQL thật từ bảng `kpi_dashboard`, `chat_log`, `share_log` |
| Lịch nội dung | `GET /api/content` | Đọc/ghi bảng `lich_noi_dung`, có trạng thái thật |
| Giảng viên | `GET /api/teachers` | Tính cấp bậc (Đồng/Bạc/Vàng/Kim Cương) và lượt click thật từ `share_log` |
| Chatbot | `POST /api/chatbot/hoi` | Khớp từ khoá FAQ thật, gọi Claude API nếu có key, fallback rule-based nếu không |
| Benchmark đối thủ | `GET /api/benchmark` | Đọc bảng `benchmark_truong` |
| Phễu chuyển đổi | `GET /api/funnel` | Tính % rơi giữa các chặng bằng công thức thật, không hard-code |

Nút **"Tạo gợi ý nội dung từ chủ đề này"** ở tab Chatbot gọi `POST /api/chatbot/tao-goi-y-tu-chu-de`,
**tạo thật một dòng mới trong bảng `lich_noi_dung`** — đây chính là vòng phản hồi khép kín được nêu
trong đề cương nghiên cứu, nay là code thật chứ không chỉ mô tả.

## Cấu hình nâng cao

Sao chép `backend/.env.example` thành `backend/.env` và điền:
- `ANTHROPIC_API_KEY` — để chatbot và AI soạn caption dùng Claude thật thay vì fallback rule-based.
- `FACEBOOK_PAGE_ACCESS_TOKEN`, `FACEBOOK_PAGE_ID` — nếu muốn nối n8n workflow 01 đăng bài Facebook thật.

Không có các key trên, hệ thống **vẫn chạy đầy đủ chức năng** ở chế độ rule-based/mô phỏng —
phù hợp cho việc demo mà không phụ thuộc dịch vụ bên ngoài.

## Về vai trò của n8n

4 workflow n8n trong `n8n-workflows/` giờ là **phần mở rộng tuỳ chọn**, không phải lõi hệ thống.
Toàn bộ logic nghiệp vụ cốt lõi đã chạy thật trong backend Python. Xem `n8n-workflows/README-tuy-chon.md`
để biết khi nào nên bật thêm n8n (chủ yếu để tích hợp thật với Facebook/email/Zalo).

## Tài liệu tham khảo thêm

- `docs/ARCHITECTURE.md` — sơ đồ kiến trúc 3 tầng, giải thích lựa chọn công nghệ
- `docs/API_REFERENCE.md` — danh sách đầy đủ endpoint kèm ví dụ curl
- `HUONG-DAN-TRIEN-KHAI-DEMO.md` *(nếu có trong gói giao)* — hướng dẫn deploy lên internet để demo hội đồng

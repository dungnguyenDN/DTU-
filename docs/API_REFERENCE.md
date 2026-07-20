# Tài liệu API

Base URL mặc định: `http://localhost:8000/api`

Xác thực: gắn header `Authorization: Bearer <token>` cho các endpoint đánh dấu 🔒.
Endpoint đánh dấu 🔒👤 yêu cầu vai trò `quan_ly` (quản lý), 🔒 thường chỉ yêu cầu đăng nhập (mọi vai trò).

## Auth

| Method | Path | Mô tả |
|---|---|---|
| POST | `/auth/login` | Đăng nhập, trả về `{token, user}` |

## Lịch nội dung

| Method | Path | Quyền | Mô tả |
|---|---|---|---|
| GET | `/content` | công khai | Danh sách lịch nội dung, lọc theo `?trang_thai=` |
| GET | `/content/goi-y-hom-nay` | 🔒 | Bài gợi ý phù hợp nhất với ngày hiện tại |
| GET | `/content/goi-y-mua-vu` | 🔒 | **AI đề xuất theo mùa vụ**: giai đoạn hiện tại + danh sách bài chấm điểm phù hợp 0-100 kèm lý do & khung giờ vàng (`?limit=6`) |
| POST | `/content/<id>/caption-ca-nhan` | 🔒 | AI viết lại caption theo giọng văn cá nhân giảng viên (`giong_van`: `than_thien` \| `chuyen_nghiep` \| `truyen_cam_hung`) |
| POST | `/content/ke-hoach-thang` | 🔒👤 | **AI lập kế hoạch tháng**: sinh N mục nội dung 30 ngày tới theo mùa vụ (`{so_bai: 12}`), trạng thái chờ soạn |
| POST | `/content/<id>/ab-caption` | 🔒👤 | **A/B testing**: AI sinh 2 biến thể caption (A thông tin / B cảm xúc) |
| POST | `/content/<id>/chon-caption` | 🔒👤 | Lưu biến thể thắng làm caption chính thức (`{caption, bien_the}`) |
| POST | `/content/<id>/da-kenh` | 🔒 | **Đa kênh**: sinh 3 biến thể Facebook / tin nhắn Zalo / kịch bản TikTok |
| POST | `/content` | 🔒👤 | Thêm mục lịch nội dung mới |
| POST | `/content/<id>/soan-nhap-ai` | 🔒👤 | Gọi AI soạn caption, chuyển trạng thái sang "chờ duyệt" |
| POST | `/content/<id>/duyet-va-dang` | 🔒👤 | Duyệt và đăng (mô phỏng Facebook API) |

## Giảng viên & Cổng chia sẻ

| Method | Path | Quyền | Mô tả |
|---|---|---|---|
| GET | `/teachers` | 🔒👤 | Bảng xếp hạng toàn bộ giảng viên |
| GET | `/teachers/toi/tien-do` | 🔒 | Tiến độ của người đang đăng nhập |
| GET | `/teachers/toi/thong-ke` | 🔒 | Thống kê cá nhân đầy đủ: tiến độ, cấp bậc, thứ hạng, hoạt động 7 ngày, lịch sử chia sẻ, **6 huy hiệu thành tích** (`huy_hieu`) |
| GET | `/teachers/bang-xep-hang` | 🔒 | Bảng xếp hạng gamification cho Cổng chia sẻ (đánh dấu `la_toi`) |
| GET | `/teachers/bang-xep-hang-khoa` | 🔒 | **Thi đua giữa các khoa**: tổng bài + click theo khoa trong đợt |
| POST | `/teachers/chia-se` | 🔒 | Ghi nhận 1 lượt chia sẻ (nút "Chia sẻ ngay") |

## Phễu chuyển đổi (bổ sung)

| Method | Path | Quyền | Mô tả |
|---|---|---|---|
| GET | `/funnel/mo-phong` | 🔒👤 | **Mô phỏng What-if**: dự báo click/hồ sơ/nhập học nếu `?so_giang_vien=N&so_bai=M` — tính từ click trung bình/bài và tỷ lệ chuyển đổi thật trong DB |

## KPI / Tổng quan

| Method | Path | Quyền | Mô tả |
|---|---|---|---|
| GET | `/kpi/tong-quan` | 🔒👤 | Số liệu tổng quan cho 4 thẻ KPI |
| GET | `/kpi/theo-nganh` | 🔒👤 | Tương tác gộp theo ngành |
| GET | `/kpi/nhan-dinh-tuan` | 🔒👤 | Nhận định AI/rule-based tổng hợp tuần |

## Chatbot

| Method | Path | Quyền | Mô tả |
|---|---|---|---|
| POST | `/chatbot/hoi` | **công khai** | Đặt câu hỏi — không cần đăng nhập (dành cho thí sinh) |
| GET | `/chatbot/lich-su` | 🔒👤 | Lịch sử hỏi-đáp |
| GET | `/chatbot/chu-de-noi-bat` | 🔒👤 | Gom nhóm chủ đề câu hỏi nổi bật |
| POST | `/chatbot/tao-goi-y-tu-chu-de` | 🔒👤 | Tạo gợi ý nội dung mới từ 1 chủ đề (vòng phản hồi khép kín) |

## Lead tư vấn (chatbot thu lead)

| Method | Path | Quyền | Mô tả |
|---|---|---|---|
| POST | `/chatbot/lead` | công khai | Thí sinh để lại `{ho_ten, lien_he, cau_hoi}` khi chatbot chuyển tư vấn viên |
| GET | `/chatbot/leads` | 🔒👤 | Danh sách lead cho tab "Lead tư vấn" |
| PUT | `/chatbot/leads/<id>` | 🔒👤 | Cập nhật `trang_thai`: `moi` \| `da_goi` \| `da_nop_ho_so` |

## Benchmark đối thủ

| Method | Path | Quyền | Mô tả |
|---|---|---|---|
| GET | `/benchmark` | 🔒👤 | Danh sách so sánh với các trường khác |
| POST | `/benchmark` | 🔒👤 | Thêm 1 dòng benchmark mới |

## Phễu chuyển đổi

| Method | Path | Quyền | Mô tả |
|---|---|---|---|
| GET | `/funnel` | 🔒👤 | Các chặng Reach → Nhập học kèm % rơi |
| GET | `/funnel/theo-nguon` | 🔒👤 | Tỷ lệ chuyển đổi theo từng nguồn (fanpage/giảng viên/chatbot) |

## Khác

| Method | Path | Quyền | Mô tả |
|---|---|---|---|
| GET | `/health` | công khai | Kiểm tra server còn sống (dùng cho healthcheck khi deploy) |

---

Ví dụ gọi API bằng curl:

```bash
# Đăng nhập
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"truyenthong@duytan.edu.vn","mat_khau":"DemoPass123!"}'

# Dùng token trả về để gọi endpoint cần quyền quản lý
curl http://localhost:8000/api/kpi/tong-quan \
  -H "Authorization: Bearer <token>"
```

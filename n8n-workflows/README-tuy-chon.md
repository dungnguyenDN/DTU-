# Ghi chú: n8n workflows là phần MỞ RỘNG TUỲ CHỌN

Kể từ khi dự án có backend Python (Flask) tự xử lý toàn bộ logic nghiệp vụ cốt lõi
(soạn AI, ghi nhận chia sẻ, tính KPI, chatbot, benchmark, funnel — xem `backend/`),
4 workflow n8n trong thư mục này **không còn là bắt buộc** để chạy demo.

## Khi nào nên dùng n8n workflows này?

Dùng khi muốn **tích hợp thật với dịch vụ bên thứ ba** theo hướng low-code, thay vì tự viết code Python gọi API:

| Workflow | Vẫn hữu ích khi... |
|---|---|
| `01-soan-duyet-dang-noi-dung.json` | Muốn tự động đăng thật lên Fanpage Facebook chính thức theo lịch, không cần thao tác tay |
| `02-cong-chia-se-giang-vien.json` | Muốn gửi email/Zalo nhắc nhở hàng loạt theo lịch cố định mà không cần viết cron job riêng |
| `03-do-luong-kpi.json` | Muốn tự động kéo số liệu Facebook Insights thật mỗi đêm về ghi vào hệ thống |
| `04-chatbot-ai-thoi-gian-thuc.json` | Muốn nối chatbot với Facebook Messenger/Zalo OA thật (n8n có sẵn node tích hợp các nền tảng nhắn tin) |

## Cách nối n8n với backend Python (nếu muốn dùng cả hai)

Thay vì để n8n ghi trực tiếp vào Google Sheets như thiết kế ban đầu, sửa các node cuối trong mỗi workflow
thành gọi HTTP Request tới chính backend Flask, ví dụ:

```
POST http://<địa-chỉ-backend>/api/teachers/chia-se
Headers: Authorization: Bearer <token lấy từ /api/auth/login>
Body: { "dot_truyen_thong": "...", "link_bai_dang": "..." }
```

Như vậy n8n chỉ đóng vai trò "cầu nối" gọi ra dịch vụ ngoài (Facebook, email) rồi gọi ngược vào
backend Python để ghi nhận kết quả — backend Python vẫn là nguồn dữ liệu duy nhất (single source of truth),
tránh tình trạng dữ liệu phân tán ở cả Google Sheets lẫn database.

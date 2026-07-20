#!/bin/bash
# Chạy toàn bộ hệ thống (backend + frontend) trên máy local, không cần Docker.
# Cách dùng: bash run.sh

cd "$(dirname "$0")"

echo "== 1/4: Cài thư viện Python (nếu chưa có) =="
pip install -r backend/requirements.txt --quiet --break-system-packages 2>/dev/null || pip install -r backend/requirements.txt --quiet

echo "== 2/4: Tạo dữ liệu mẫu =="
(cd backend && python3 seed_data.py)

echo "== 3/4: Khởi động backend tại http://localhost:8000 =="
cd backend
nohup python3 app.py > ../backend.log 2>&1 &
disown
cd ..
sleep 2

echo "== 4/4: Khởi động frontend tại http://localhost:8080 =="
cd frontend
nohup python3 -m http.server 8080 > ../frontend.log 2>&1 &
disown
cd ..
sleep 1

echo ""
echo "✅ Hệ thống đã chạy:"
echo "   Trang tuyển sinh (CÔNG KHAI, cho thí sinh): http://localhost:8080/tuyensinh/index.html"
echo "   Nền tảng quản lý : http://localhost:8080/platform/index.html"
echo "   Cổng chia sẻ     : http://localhost:8080/portal/index.html"
echo "   Backend API      : http://localhost:8000/api/health"
echo ""
echo "   Đăng nhập quản lý : truyenthong@duytan.edu.vn / DemoPass123!"
echo "   Đăng nhập giảng viên: nguyenvana@duytan.edu.vn / DemoPass123!"
echo ""
echo "Dừng hệ thống: pkill -f 'python3 app.py' && pkill -f 'http.server 8080'"

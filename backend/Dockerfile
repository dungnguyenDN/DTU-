FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Thư mục lưu SQLite (mount volume vào đây để giữ dữ liệu qua các lần khởi động lại)
ENV DATABASE_PATH=/app/data/dtu_platform.db
RUN mkdir -p /app/data

EXPOSE 8000

# Chạy bằng gunicorn (WSGI production) thay vì Flask dev server.
# Dùng 1 worker + nhiều thread để tránh tranh chấp khoá ghi của SQLite.
# Cổng lấy từ biến môi trường $PORT (Render/Railway đặt sẵn), mặc định 8000.
CMD ["sh", "-c", "python seed_data.py && gunicorn app:app --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 4 --timeout 120"]

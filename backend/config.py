"""
Cấu hình ứng dụng — đọc từ biến môi trường, có giá trị mặc định an toàn cho môi trường demo.
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass  # python-dotenv là tuỳ chọn; nếu không cài, vẫn chạy được bằng biến môi trường hệ thống

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dtu-demo-secret-key-doi-truoc-khi-deploy-that")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "dtu_platform.db"))
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    FACEBOOK_PAGE_ACCESS_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "")
    FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "")
    JWT_EXP_MINUTES = int(os.environ.get("JWT_EXP_MINUTES", "480"))
    SHARE_TARGET_PER_PERIOD = int(os.environ.get("SHARE_TARGET_PER_PERIOD", "5"))
    CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "*")

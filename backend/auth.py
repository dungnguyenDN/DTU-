"""
Xác thực người dùng — JWT (PyJWT) + băm mật khẩu bằng hashlib.pbkdf2_hmac
(không phụ thuộc bcrypt/passlib để dễ cài đặt, vẫn đủ an toàn cho quy mô đề tài).
"""
import hashlib
import os
import base64
import time
import jwt
from functools import wraps
from flask import request, jsonify, g
from config import Config

PBKDF2_ITERATIONS = 260_000


def hash_password(plain_password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()


def verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        salt_b64, dk_b64 = stored_hash.split("$")
        salt = base64.b64decode(salt_b64)
        expected_dk = base64.b64decode(dk_b64)
        dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
        return dk == expected_dk
    except Exception:
        return False


def create_token(payload: dict) -> str:
    to_encode = payload.copy()
    to_encode["exp"] = int(time.time()) + Config.JWT_EXP_MINUTES * 60
    return jwt.encode(to_encode, Config.SECRET_KEY, algorithm="HS256")


def decode_token(token: str):
    try:
        return jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def login_required(role=None):
    """Decorator bảo vệ route: yêu cầu Bearer token hợp lệ, tuỳ chọn giới hạn theo vai trò."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Thiếu hoặc sai định dạng Authorization header"}), 401
            token = auth_header.split(" ", 1)[1]
            payload = decode_token(token)
            if payload is None:
                return jsonify({"error": "Token không hợp lệ hoặc đã hết hạn"}), 401
            if role is not None and payload.get("vai_tro") != role:
                return jsonify({"error": "Không đủ quyền truy cập"}), 403
            g.current_user = payload
            return fn(*args, **kwargs)
        return wrapper
    return decorator

"""
Route xác thực — đăng nhập cho giảng viên/nhân viên (Cổng chia sẻ) và quản lý (Nền tảng quản lý).
"""
from flask import Blueprint, request, jsonify
import database as db
from auth import verify_password, create_token

bp = Blueprint("auth_routes", __name__, url_prefix="/api/auth")


@bp.post("/login")
def login():
    payload = request.get_json(force=True, silent=True) or {}
    email = payload.get("email", "").strip().lower()
    mat_khau = payload.get("mat_khau", "")

    if not email or not mat_khau:
        return jsonify({"error": "Thiếu email hoặc mật khẩu"}), 400

    row = db.query("SELECT * FROM giang_vien WHERE lower(email) = ?", (email,), fetchone=True)
    if row is None or not verify_password(mat_khau, row["mat_khau_hash"]):
        return jsonify({"error": "Email hoặc mật khẩu không đúng"}), 401

    # Tài khoản bị quản trị viên khóa thì không cho đăng nhập
    if "kich_hoat" in row.keys() and row["kich_hoat"] == 0:
        return jsonify({"error": "Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên."}), 403

    token = create_token({
        "sub": row["ma_giang_vien"],
        "id": row["id"],
        "ho_ten": row["ho_ten"],
        "khoa": row["khoa"],
        "vai_tro": row["vai_tro"],
    })
    return jsonify({
        "token": token,
        "user": {
            "id": row["id"],
            "ma_giang_vien": row["ma_giang_vien"],
            "ho_ten": row["ho_ten"],
            "khoa": row["khoa"],
            "vai_tro": row["vai_tro"],
        },
    })

"""
Route Quản trị hệ thống — chỉ dành cho vai trò quản lý:
- Quản lý người dùng (danh sách, thêm, sửa vai trò, reset mật khẩu, khóa/mở, xóa)
- Xem nhanh cơ sở dữ liệu (số bản ghi từng bảng)
"""
import sqlite3
import secrets
from flask import Blueprint, request, jsonify, g
import database as db
from auth import login_required, hash_password

bp = Blueprint("admin_routes", __name__, url_prefix="/api/admin")

VAI_TRO_HOP_LE = ("giang_vien", "quan_ly")


def _user_public(row):
    d = dict(row)
    d.pop("mat_khau_hash", None)
    d["kich_hoat"] = d.get("kich_hoat", 1)
    return d


# ============ QUẢN LÝ NGƯỜI DÙNG ============

@bp.get("/users")
@login_required(role="quan_ly")
def list_users():
    rows = db.query("SELECT * FROM giang_vien ORDER BY vai_tro DESC, ho_ten")
    return jsonify([_user_public(r) for r in rows])


@bp.post("/users")
@login_required(role="quan_ly")
def create_user():
    p = request.get_json(force=True, silent=True) or {}
    required = ["ma_giang_vien", "ho_ten", "email", "khoa", "mat_khau"]
    missing = [f for f in required if not (p.get(f) or "").strip()]
    if missing:
        return jsonify({"error": f"Thiếu trường bắt buộc: {', '.join(missing)}"}), 400

    vai_tro = p.get("vai_tro", "giang_vien")
    if vai_tro not in VAI_TRO_HOP_LE:
        return jsonify({"error": "vai_tro phải là giang_vien hoặc quan_ly"}), 400

    try:
        new_id = db.execute(
            """INSERT INTO giang_vien (ma_giang_vien, ho_ten, email, khoa, mat_khau_hash, vai_tro, kich_hoat)
               VALUES (?, ?, ?, ?, ?, ?, 1)""",
            (p["ma_giang_vien"].strip(), p["ho_ten"].strip(), p["email"].strip().lower(),
             p["khoa"].strip(), hash_password(p["mat_khau"]), vai_tro),
        )
    except sqlite3.IntegrityError:
        return jsonify({"error": "Mã giảng viên hoặc email đã tồn tại"}), 409

    row = db.query("SELECT * FROM giang_vien WHERE id = ?", (new_id,), fetchone=True)
    return jsonify(_user_public(row)), 201


@bp.put("/users/<int:user_id>")
@login_required(role="quan_ly")
def update_user(user_id):
    row = db.query("SELECT * FROM giang_vien WHERE id = ?", (user_id,), fetchone=True)
    if row is None:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404
    p = request.get_json(force=True, silent=True) or {}

    ho_ten = (p.get("ho_ten") or row["ho_ten"]).strip()
    khoa = (p.get("khoa") or row["khoa"]).strip()
    vai_tro = p.get("vai_tro", row["vai_tro"])
    if vai_tro not in VAI_TRO_HOP_LE:
        return jsonify({"error": "vai_tro phải là giang_vien hoặc quan_ly"}), 400

    # Không cho tự hạ quyền chính mình (tránh mất quyền quản trị ngoài ý muốn)
    if user_id == g.current_user["id"] and vai_tro != "quan_ly":
        return jsonify({"error": "Không thể tự hạ quyền quản lý của chính bạn"}), 400

    db.execute("UPDATE giang_vien SET ho_ten = ?, khoa = ?, vai_tro = ? WHERE id = ?",
               (ho_ten, khoa, vai_tro, user_id))
    return jsonify(_user_public(db.query("SELECT * FROM giang_vien WHERE id = ?", (user_id,), fetchone=True)))


@bp.post("/users/<int:user_id>/reset-mat-khau")
@login_required(role="quan_ly")
def reset_password(user_id):
    row = db.query("SELECT id FROM giang_vien WHERE id = ?", (user_id,), fetchone=True)
    if row is None:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404
    p = request.get_json(force=True, silent=True) or {}
    mat_khau_moi = (p.get("mat_khau") or "").strip() or ("DTU" + secrets.token_hex(3))
    db.execute("UPDATE giang_vien SET mat_khau_hash = ? WHERE id = ?",
               (hash_password(mat_khau_moi), user_id))
    # Trả về mật khẩu mới để quản trị viên gửi cho người dùng (chỉ hiện một lần)
    return jsonify({"id": user_id, "mat_khau_moi": mat_khau_moi})


@bp.post("/users/<int:user_id>/khoa")
@login_required(role="quan_ly")
def toggle_lock(user_id):
    row = db.query("SELECT * FROM giang_vien WHERE id = ?", (user_id,), fetchone=True)
    if row is None:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404
    if user_id == g.current_user["id"]:
        return jsonify({"error": "Không thể tự khóa tài khoản của chính bạn"}), 400
    p = request.get_json(force=True, silent=True) or {}
    kich_hoat = 1 if p.get("kich_hoat", 0) else 0
    db.execute("UPDATE giang_vien SET kich_hoat = ? WHERE id = ?", (kich_hoat, user_id))
    return jsonify({"id": user_id, "kich_hoat": kich_hoat})


@bp.delete("/users/<int:user_id>")
@login_required(role="quan_ly")
def delete_user(user_id):
    row = db.query("SELECT * FROM giang_vien WHERE id = ?", (user_id,), fetchone=True)
    if row is None:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404
    if user_id == g.current_user["id"]:
        return jsonify({"error": "Không thể tự xóa tài khoản của chính bạn"}), 400
    # Xóa dữ liệu chia sẻ phụ thuộc trước để không vướng khóa ngoại
    db.execute("DELETE FROM share_log WHERE giang_vien_id = ?", (user_id,))
    db.execute("DELETE FROM giang_vien WHERE id = ?", (user_id,))
    return jsonify({"id": user_id, "message": "Đã xóa người dùng"})


# ============ XEM NHANH CƠ SỞ DỮ LIỆU ============

DB_TABLES = [
    ("giang_vien", "Người dùng (giảng viên & quản lý)"),
    ("lich_noi_dung", "Bài trong lịch nội dung"),
    ("share_log", "Lượt chia sẻ của giảng viên"),
    ("kpi_dashboard", "Số liệu KPI theo bài"),
    ("faq", "Câu hỏi thường gặp (chatbot)"),
    ("chat_log", "Nhật ký câu hỏi thí sinh"),
    ("lead_tu_van", "Lead tư vấn thu được"),
    ("benchmark_truong", "Trường đối sánh"),
    ("funnel_source", "Nguồn phễu chuyển đổi"),
]


@bp.get("/thong-ke-db")
@login_required(role="quan_ly")
def db_stats():
    result = []
    for bang, mo_ta in DB_TABLES:
        row = db.query(f"SELECT COUNT(*) AS c FROM {bang}", fetchone=True)
        result.append({"bang": bang, "mo_ta": mo_ta, "so_ban_ghi": row["c"]})
    return jsonify({"tables": result, "engine": "PostgreSQL" if db.IS_POSTGRES else "SQLite"})

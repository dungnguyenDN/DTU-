"""
Route Benchmark đối thủ — đại diện cho Nội dung 1 trong đề cương:
nghiên cứu insight & benchmark từ các trường đại học khác.
"""
from flask import Blueprint, request, jsonify
import database as db
from auth import login_required

bp = Blueprint("benchmark_routes", __name__, url_prefix="/api/benchmark")


@bp.get("")
@login_required(role="quan_ly")
def list_benchmark():
    rows = db.query("SELECT * FROM benchmark_truong ORDER BY tang_truong_follower DESC")
    return jsonify(db.rows_to_list(rows))


@bp.post("")
@login_required(role="quan_ly")
def add_benchmark():
    payload = request.get_json(force=True, silent=True) or {}
    required = ["ten_truong", "tang_truong_follower", "ty_le_tuong_tac"]
    missing = [f for f in required if payload.get(f) is None]
    if missing:
        return jsonify({"error": f"Thiếu trường bắt buộc: {', '.join(missing)}"}), 400

    new_id = db.execute(
        """INSERT INTO benchmark_truong (ten_truong, tang_truong_follower, ty_le_tuong_tac, dinh_dang_chu_dao, la_truong_minh)
           VALUES (?, ?, ?, ?, ?)""",
        (payload["ten_truong"], payload["tang_truong_follower"], payload["ty_le_tuong_tac"],
         payload.get("dinh_dang_chu_dao", ""), 1 if payload.get("la_truong_minh") else 0),
    )
    return jsonify({"id": new_id}), 201

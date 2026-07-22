"""
Route Giảng viên & Cổng chia sẻ nội dung — Nội dung 2 trong đề cương:
chỉ tiêu 05 bài/giảng viên/đợt, cấp bậc, hiệu quả (lượt click).
"""
from datetime import date, timedelta
from flask import Blueprint, request, jsonify, g
import database as db
from auth import login_required
from config import Config
from services.analytics_service import tier_for, progress_ratio
from services.badge_service import compute_badges

bp = Blueprint("teacher_routes", __name__, url_prefix="/api/teachers")


@bp.get("")
@login_required(role="quan_ly")
def list_teachers():
    """Bảng xếp hạng giảng viên — dùng cho tab Giảng viên trong Nền tảng quản lý."""
    dot = request.args.get("dot_truyen_thong", "")
    rows = db.query("SELECT * FROM giang_vien WHERE vai_tro = 'giang_vien' ORDER BY ho_ten")
    result = []
    for t in rows:
        if dot:
            count_row = db.query(
                "SELECT COUNT(*) AS c, COALESCE(SUM(luot_click),0) AS clicks FROM share_log "
                "WHERE giang_vien_id = ? AND dot_truyen_thong = ?",
                (t["id"], dot), fetchone=True,
            )
        else:
            count_row = db.query(
                "SELECT COUNT(*) AS c, COALESCE(SUM(luot_click),0) AS clicks FROM share_log WHERE giang_vien_id = ?",
                (t["id"],), fetchone=True,
            )
        total_row = db.query(
            "SELECT COUNT(*) AS total FROM share_log WHERE giang_vien_id = ?", (t["id"],), fetchone=True
        )
        tier = tier_for(total_row["total"])
        result.append({
            "id": t["id"], "ho_ten": t["ho_ten"], "khoa": t["khoa"],
            "so_bai_dot_nay": count_row["c"], "luot_click": count_row["clicks"],
            "tong_luy_ke": total_row["total"], "target": Config.SHARE_TARGET_PER_PERIOD,
            "tien_do": round(progress_ratio(count_row["c"]) * 100, 1),
            "cap_bac": tier,
        })
    result.sort(key=lambda x: (-x["so_bai_dot_nay"], -x["luot_click"]))
    return jsonify(result)


@bp.get("/toi/tien-do")
@login_required()
def my_progress():
    """Tiến độ của chính giảng viên đang đăng nhập — dùng cho vòng tròn tiến độ trên Cổng chia sẻ."""
    user_id = g.current_user["id"]
    dot = request.args.get("dot_truyen_thong", "")
    if dot:
        row = db.query(
            "SELECT COUNT(*) AS c FROM share_log WHERE giang_vien_id = ? AND dot_truyen_thong = ?",
            (user_id, dot), fetchone=True,
        )
    else:
        row = db.query("SELECT COUNT(*) AS c FROM share_log WHERE giang_vien_id = ?", (user_id,), fetchone=True)
    return jsonify({
        "so_bai_da_chia_se": row["c"],
        "target": Config.SHARE_TARGET_PER_PERIOD,
        "hoan_thanh": row["c"] >= Config.SHARE_TARGET_PER_PERIOD,
    })


def _leaderboard_rows(dot: str):
    """Tính bảng xếp hạng giảng viên trong một đợt — dùng chung cho leaderboard và thống kê cá nhân."""
    rows = db.query("SELECT * FROM giang_vien WHERE vai_tro = 'giang_vien'")
    board = []
    for t in rows:
        count_row = db.query(
            "SELECT COUNT(*) AS c, COALESCE(SUM(luot_click),0) AS clicks FROM share_log "
            "WHERE giang_vien_id = ? AND dot_truyen_thong = ?",
            (t["id"], dot), fetchone=True,
        )
        total_row = db.query(
            "SELECT COUNT(*) AS total FROM share_log WHERE giang_vien_id = ?", (t["id"],), fetchone=True
        )
        board.append({
            "id": t["id"], "ho_ten": t["ho_ten"], "khoa": t["khoa"],
            "so_bai": count_row["c"], "luot_click": count_row["clicks"],
            "tong_luy_ke": total_row["total"],
            "cap_bac": tier_for(total_row["total"]),
        })
    board.sort(key=lambda x: (-x["so_bai"], -x["luot_click"], x["ho_ten"]))
    for i, item in enumerate(board):
        item["hang"] = i + 1
    return board


@bp.get("/bang-xep-hang")
@login_required()
def leaderboard():
    """Bảng xếp hạng gamification hiển thị ngay trên Cổng chia sẻ — mọi giảng viên xem được."""
    dot = request.args.get("dot_truyen_thong", "Đợt tuyển sinh 2026")
    board = _leaderboard_rows(dot)
    me_id = g.current_user["id"]
    for item in board:
        item["la_toi"] = item["id"] == me_id
    return jsonify({"dot_truyen_thong": dot, "bang_xep_hang": board})


@bp.get("/bang-xep-hang-khoa")
@login_required()
def leaderboard_by_khoa():
    """Thi đua giữa các khoa — tổng hợp số bài và click của cả khoa trong đợt."""
    dot = request.args.get("dot_truyen_thong", "Đợt tuyển sinh 2026")
    board = _leaderboard_rows(dot)
    khoa_map = {}
    for item in board:
        k = khoa_map.setdefault(item["khoa"], {"khoa": item["khoa"], "so_gv": 0, "so_bai": 0, "luot_click": 0})
        k["so_gv"] += 1
        k["so_bai"] += item["so_bai"]
        k["luot_click"] += item["luot_click"]
    result = sorted(khoa_map.values(), key=lambda x: (-x["so_bai"], -x["luot_click"]))
    for i, item in enumerate(result):
        item["hang"] = i + 1
    me = next((b for b in board if b["id"] == g.current_user["id"]), None)
    return jsonify({"dot_truyen_thong": dot, "khoa_cua_toi": me["khoa"] if me else None, "bang_xep_hang": result})


@bp.get("/toi/thong-ke")
@login_required()
def my_stats():
    """
    Thống kê cá nhân đầy đủ cho dashboard Cổng chia sẻ: tiến độ, cấp bậc, thứ hạng,
    hoạt động 7 ngày gần nhất và lịch sử chia sẻ kèm tên bài + lượt click.
    """
    user_id = g.current_user["id"]
    dot = request.args.get("dot_truyen_thong", "Đợt tuyển sinh 2026")

    board = _leaderboard_rows(dot)
    me = next((item for item in board if item["id"] == user_id), None)

    six_days_ago = (date.today() - timedelta(days=6)).isoformat()
    activity = db.query(
        f"""SELECT {db.date_col('thoi_gian')} AS ngay, COUNT(*) AS so_luot FROM share_log
           WHERE giang_vien_id = ? AND {db.date_col('thoi_gian')} >= ?
           GROUP BY {db.date_col('thoi_gian')}""",
        (user_id, six_days_ago),
    )

    history = db.query(
        """SELECT s.thoi_gian, s.luot_click, s.dot_truyen_thong,
                  COALESCE(l.chu_de, 'Bài chia sẻ') AS chu_de,
                  COALESCE(l.giai_doan, '') AS giai_doan
           FROM share_log s LEFT JOIN lich_noi_dung l ON l.id = s.lich_noi_dung_id
           WHERE s.giang_vien_id = ?
           ORDER BY s.thoi_gian DESC LIMIT 10""",
        (user_id,),
    )

    # Số liệu cho huy hiệu thành tích
    total_clicks_row = db.query(
        "SELECT COALESCE(SUM(luot_click),0) AS s FROM share_log WHERE giang_vien_id = ?",
        (user_id,), fetchone=True,
    )
    share_days = db.query(
        f"SELECT DISTINCT {db.date_col('thoi_gian')} AS ngay FROM share_log WHERE giang_vien_id = ?",
        (user_id,),
    )
    nganh_row = db.query(
        """SELECT COUNT(DISTINCT l.nganh) AS c FROM share_log s
           JOIN lich_noi_dung l ON l.id = s.lich_noi_dung_id
           WHERE s.giang_vien_id = ?""",
        (user_id,), fetchone=True,
    )
    huy_hieu = compute_badges(
        tong_luy_ke=me["tong_luy_ke"] if me else 0,
        so_bai_dot_nay=me["so_bai"] if me else 0,
        target=Config.SHARE_TARGET_PER_PERIOD,
        tong_click=total_clicks_row["s"],
        ngay_chia_se=[r["ngay"] for r in share_days],
        so_nganh=nganh_row["c"],
        hang=me["hang"] if me else None,
    )

    return jsonify({
        "huy_hieu": huy_hieu,
        "dot_truyen_thong": dot,
        "so_bai_dot_nay": me["so_bai"] if me else 0,
        "target": Config.SHARE_TARGET_PER_PERIOD,
        "hoan_thanh": (me["so_bai"] if me else 0) >= Config.SHARE_TARGET_PER_PERIOD,
        "luot_click_dot_nay": me["luot_click"] if me else 0,
        "tong_luy_ke": me["tong_luy_ke"] if me else 0,
        "cap_bac": me["cap_bac"] if me else tier_for(0),
        "hang": me["hang"] if me else None,
        "tong_giang_vien": len(board),
        "hoat_dong_7_ngay": db.rows_to_list(activity),
        "lich_su": db.rows_to_list(history),
    })


@bp.post("/chia-se")
@login_required()
def record_share():
    """
    Endpoint mà nút "Chia sẻ ngay" trên Cổng chia sẻ nội dung gọi tới.
    Đây là bản thay thế chạy thật cho webhook n8n Luồng 2 khi dùng kiến trúc backend Python.
    """
    payload = request.get_json(force=True, silent=True) or {}
    user_id = g.current_user["id"]
    dot = payload.get("dot_truyen_thong", "")
    link_bai_dang = payload.get("link_bai_dang", "")
    lich_noi_dung_id = payload.get("lich_noi_dung_id")

    if not dot or not link_bai_dang:
        return jsonify({"error": "Thiếu dot_truyen_thong hoặc link_bai_dang"}), 400

    utm_link = f"{link_bai_dang}?utm_source=giangvien&utm_medium=facebook&utm_campaign={dot}&utm_content={g.current_user['sub']}"

    db.execute(
        """INSERT INTO share_log (giang_vien_id, lich_noi_dung_id, dot_truyen_thong, link_bai_dang, utm_link)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, lich_noi_dung_id, dot, link_bai_dang, utm_link),
    )

    row = db.query(
        "SELECT COUNT(*) AS c FROM share_log WHERE giang_vien_id = ? AND dot_truyen_thong = ?",
        (user_id, dot), fetchone=True,
    )
    count = row["c"]
    target = Config.SHARE_TARGET_PER_PERIOD
    return jsonify({
        "ok": True,
        "utm_link": utm_link,
        "so_bai_da_chia_se": count,
        "target": target,
        "hoan_thanh": count >= target,
    })

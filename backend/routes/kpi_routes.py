"""
Route KPI tổng quan — Nội dung 3 trong đề cương: đo lường, phân tích tương tác.
"""
from flask import Blueprint, request, jsonify
import database as db
from auth import login_required
from services.analytics_service import build_weekly_insight

bp = Blueprint("kpi_routes", __name__, url_prefix="/api/kpi")


@bp.get("/tong-quan")
@login_required(role="quan_ly")
def overview():
    reach_row = db.query("SELECT COALESCE(SUM(luot_xem),0) AS s FROM kpi_dashboard", fetchone=True)
    engaged_row = db.query("SELECT COALESCE(SUM(luot_tuong_tac),0) AS s FROM kpi_dashboard", fetchone=True)
    avg_rate_row = db.query("SELECT COALESCE(AVG(ty_le_tuong_tac),0) AS a FROM kpi_dashboard", fetchone=True)
    chat_total_row = db.query("SELECT COUNT(*) AS c FROM chat_log", fetchone=True)
    chat_auto_row = db.query("SELECT COUNT(*) AS c FROM chat_log WHERE chuyen_tu_van_vien = 0", fetchone=True)

    teacher_total_row = db.query("SELECT COUNT(*) AS c FROM giang_vien WHERE vai_tro = 'giang_vien'", fetchone=True)
    teacher_done_row = db.query(
        """SELECT COUNT(DISTINCT giang_vien_id) AS c FROM (
               SELECT giang_vien_id, COUNT(*) AS so_bai FROM share_log GROUP BY giang_vien_id
               HAVING so_bai >= 5
           )""",
        fetchone=True,
    )

    teacher_total = teacher_total_row["c"] or 1
    teacher_done_pct = round((teacher_done_row["c"] or 0) / teacher_total * 100, 1)
    chat_total = chat_total_row["c"] or 1
    chat_auto_pct = round((chat_auto_row["c"] or 0) / chat_total * 100, 1)

    return jsonify({
        "tong_luot_tiep_can": reach_row["s"],
        "tong_luot_tuong_tac": engaged_row["s"],
        "ty_le_tuong_tac_trung_binh": round(avg_rate_row["a"], 2),
        "giang_vien_dat_chi_tieu_pct": teacher_done_pct,
        "so_cau_hoi_chatbot": chat_total_row["c"],
        "ty_le_tu_dong_tra_loi_pct": chat_auto_pct,
    })


@bp.get("/theo-nganh")
@login_required(role="quan_ly")
def by_major():
    rows = db.query(
        """SELECT nganh, COALESCE(SUM(luot_tuong_tac),0) AS tuong_tac
           FROM kpi_dashboard GROUP BY nganh ORDER BY tuong_tac DESC"""
    )
    return jsonify(db.rows_to_list(rows))


@bp.get("/nhan-dinh-tuan")
@login_required(role="quan_ly")
def weekly_insight():
    top_content_row = db.query(
        """SELECT l.chu_de, l.nganh FROM kpi_dashboard k
           JOIN lich_noi_dung l ON l.id = k.lich_noi_dung_id
           ORDER BY k.luot_tuong_tac DESC LIMIT 1""",
        fetchone=True,
    )
    chat_rows = db.query("SELECT cau_hoi FROM chat_log ORDER BY thoi_gian DESC LIMIT 50")
    top_teacher_rows = db.query(
        """SELECT gv.ho_ten, COALESCE(SUM(sl.luot_click),0) AS clicks
           FROM giang_vien gv JOIN share_log sl ON sl.giang_vien_id = gv.id
           GROUP BY gv.id ORDER BY clicks DESC LIMIT 2"""
    )
    benchmark_row = db.query(
        "SELECT ten_truong FROM benchmark_truong WHERE la_truong_minh = 1 "
        "AND tang_truong_follower = (SELECT MAX(tang_truong_follower) FROM benchmark_truong)",
        fetchone=True,
    )

    text = build_weekly_insight(
        top_content=db.row_to_dict(top_content_row),
        top_chat_topics=[{"topic": r["cau_hoi"][:24]} for r in chat_rows[:2]],
        top_teachers=db.rows_to_list(top_teacher_rows),
        benchmark_leader=benchmark_row is not None,
    )
    return jsonify({"nhan_dinh": text})

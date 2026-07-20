"""
Route Phễu chuyển đổi — thước đo hiệu quả cuối cùng: Reach -> Tương tác -> Click ->
Hồ sơ nộp -> Nhập học, kèm hiệu quả chuyển đổi theo từng nguồn.
"""
from flask import Blueprint, request, jsonify
import database as db
from auth import login_required
from services.analytics_service import compute_funnel, compute_conversion_rate

bp = Blueprint("funnel_routes", __name__, url_prefix="/api/funnel")


@bp.get("")
@login_required(role="quan_ly")
def funnel_overview():
    reach = db.query("SELECT COALESCE(SUM(luot_xem),0) AS s FROM kpi_dashboard", fetchone=True)["s"]
    engaged = db.query("SELECT COALESCE(SUM(luot_tuong_tac),0) AS s FROM kpi_dashboard", fetchone=True)["s"]
    clicks = db.query("SELECT COALESCE(SUM(luot_click),0) AS s FROM funnel_source", fetchone=True)["s"]
    apps = db.query("SELECT COALESCE(SUM(ho_so_nop),0) AS s FROM funnel_source", fetchone=True)["s"]

    # Giai đoạn "hồ sơ bắt đầu điền" và "nhập học" là ước lượng theo tỷ lệ chuẩn ngành
    # (trong triển khai thật sẽ lấy từ hệ thống tuyển sinh CRM riêng của trường).
    started = round(apps * 1.35)
    enrolled = round(apps * 0.42)

    stages = compute_funnel([
        {"label": "Lượt tiếp cận", "value": reach},
        {"label": "Lượt tương tác", "value": engaged},
        {"label": "Click về trang tuyển sinh", "value": clicks},
        {"label": "Hồ sơ bắt đầu điền", "value": started},
        {"label": "Hồ sơ nộp hoàn chỉnh", "value": apps},
        {"label": "Nhập học", "value": enrolled},
    ])
    return jsonify(stages)


@bp.get("/mo-phong")
@login_required(role="quan_ly")
def funnel_what_if():
    """
    Mô phỏng What-if: "Nếu N giảng viên cùng chia sẻ M bài/đợt thì kênh giảng viên
    mang lại thêm bao nhiêu click và hồ sơ?" — dự báo dựa trên các tỷ lệ THẬT trong DB
    (click trung bình/bài chia sẻ và tỷ lệ chuyển đổi kênh giảng viên), không hard-code.
    """
    try:
        so_giang_vien = max(0, int(request.args.get("so_giang_vien", 50)))
        so_bai = max(0, int(request.args.get("so_bai", 5)))
    except ValueError:
        return jsonify({"error": "Tham số so_giang_vien/so_bai phải là số nguyên"}), 400

    share_row = db.query(
        "SELECT COUNT(*) AS c, COALESCE(SUM(luot_click),0) AS clicks FROM share_log", fetchone=True
    )
    avg_click_per_share = (share_row["clicks"] / share_row["c"]) if share_row["c"] else 8.0

    gv_row = db.query(
        "SELECT COALESCE(SUM(luot_click),0) AS clicks, COALESCE(SUM(ho_so_nop),0) AS apps "
        "FROM funnel_source WHERE nguon = 'Giảng viên chia sẻ'", fetchone=True,
    )
    conv_rate = (gv_row["apps"] / gv_row["clicks"]) if gv_row["clicks"] else 0.15

    du_kien_chia_se = so_giang_vien * so_bai
    du_kien_click = round(du_kien_chia_se * avg_click_per_share)
    du_kien_ho_so = round(du_kien_click * conv_rate)
    du_kien_nhap_hoc = round(du_kien_ho_so * 0.42)  # cùng hệ số ước lượng với funnel_overview

    return jsonify({
        "tham_so": {"so_giang_vien": so_giang_vien, "so_bai": so_bai},
        "gia_dinh": {
            "click_trung_binh_moi_bai": round(avg_click_per_share, 1),
            "ty_le_chuyen_doi_kenh_gv_pct": round(conv_rate * 100, 1),
        },
        "hien_tai": {"luot_click": gv_row["clicks"], "ho_so_nop": gv_row["apps"]},
        "du_bao": {
            "luot_chia_se": du_kien_chia_se,
            "luot_click": du_kien_click,
            "ho_so_nop": du_kien_ho_so,
            "nhap_hoc": du_kien_nhap_hoc,
        },
    })


@bp.get("/theo-nguon")
@login_required(role="quan_ly")
def funnel_by_source():
    rows = db.query(
        """SELECT nguon, COALESCE(SUM(luot_click),0) AS clicks, COALESCE(SUM(ho_so_nop),0) AS apps
           FROM funnel_source GROUP BY nguon ORDER BY clicks DESC"""
    )
    result = []
    for r in rows:
        result.append({
            "nguon": r["nguon"], "luot_click": r["clicks"], "ho_so_nop": r["apps"],
            "ty_le_chuyen_doi_pct": compute_conversion_rate(r["clicks"], r["apps"]),
        })
    return jsonify(result)

"""
Route Lịch nội dung — Nội dung 2 trong đề cương: lịch nội dung theo mùa vụ học đường.
"""
from datetime import date
from flask import Blueprint, request, jsonify, g
import database as db
from auth import login_required
from services.ai_service import draft_caption, personalize_caption, multi_channel_captions, ab_captions
from services.season_service import current_season, score_post, build_reason

bp = Blueprint("content_routes", __name__, url_prefix="/api/content")


@bp.get("")
def list_content():
    trang_thai = request.args.get("trang_thai")
    if trang_thai:
        rows = db.query(
            "SELECT * FROM lich_noi_dung WHERE trang_thai = ? ORDER BY ngay_dang_du_kien DESC",
            (trang_thai,),
        )
    else:
        rows = db.query("SELECT * FROM lich_noi_dung ORDER BY ngay_dang_du_kien DESC")
    return jsonify(db.rows_to_list(rows))


@bp.get("/goi-y-hom-nay")
@login_required()
def suggestion_today():
    """
    Trả về bài gợi ý phù hợp nhất với ngày hiện tại — dùng cho Cổng chia sẻ nội dung
    (nút "Chia sẻ ngay" đọc từ endpoint này thay vì mảng tĩnh CONTENT_LIBRARY).
    """
    today = date.today().isoformat()
    row = db.query(
        """SELECT * FROM lich_noi_dung
           WHERE trang_thai = 'da_dang'
           ORDER BY ABS(julianday(ngay_dang_du_kien) - julianday(?)) ASC
           LIMIT 1""",
        (today,),
        fetchone=True,
    )
    if row is None:
        return jsonify({"error": "Chưa có bài đăng nào để gợi ý"}), 404
    return jsonify(db.row_to_dict(row))


@bp.get("/goi-y-mua-vu")
@login_required()
def seasonal_suggestions():
    """
    AI đề xuất bài đăng theo mùa vụ — trái tim của Cổng chia sẻ giảng viên.
    Trả về giai đoạn mùa vụ hiện tại + danh sách bài đã đăng được chấm điểm
    mức phù hợp (0-100) kèm lý do đề xuất và khung giờ vàng nên đăng.
    """
    season = current_season()
    rows = db.query("SELECT * FROM lich_noi_dung WHERE trang_thai = 'da_dang'")

    # Tỷ lệ tương tác lịch sử của từng bài (từ kpi_dashboard) đưa vào công thức chấm điểm.
    kpi_rows = db.query(
        "SELECT lich_noi_dung_id, MAX(ty_le_tuong_tac) AS ty_le FROM kpi_dashboard GROUP BY lich_noi_dung_id"
    )
    engagement = {r["lich_noi_dung_id"]: (r["ty_le"] or 0.0) for r in kpi_rows}

    suggestions = []
    for row in rows:
        post = db.row_to_dict(row)
        rate = engagement.get(post["id"], 0.0)
        score = score_post(post, season, engagement_rate=rate)
        post["diem_phu_hop"] = score
        post["ty_le_tuong_tac"] = rate
        post["ly_do_goi_y"] = build_reason(post, season, score, engagement_rate=rate)
        suggestions.append(post)

    suggestions.sort(key=lambda p: -p["diem_phu_hop"])
    limit = min(int(request.args.get("limit", 6)), 12)
    return jsonify({
        "mua_vu": {
            "ten": season["ten"],
            "mo_ta": season["mo_ta"],
            "khung_gio_vang": season["khung_gio_vang"],
            "hashtag": season["hashtag"],
            "icon": season["icon"],
            "key": season["key"],
        },
        "goi_y": suggestions[:limit],
    })


@bp.post("/<int:content_id>/caption-ca-nhan")
@login_required()
def personalized_caption(content_id):
    """
    AI viết lại caption theo giọng văn cá nhân của giảng viên đang đăng nhập
    (thân thiện / chuyên nghiệp / truyền cảm hứng). Có fallback rule-based khi offline.
    """
    row = db.query("SELECT * FROM lich_noi_dung WHERE id = ?", (content_id,), fetchone=True)
    if row is None:
        return jsonify({"error": "Không tìm thấy bài viết"}), 404

    payload = request.get_json(force=True, silent=True) or {}
    tone = payload.get("giong_van", "than_thien")

    user = db.query("SELECT * FROM giang_vien WHERE id = ?", (g.current_user["id"],), fetchone=True)
    ho_ten = user["ho_ten"] if user else "Giảng viên Duy Tân"
    khoa = user["khoa"] if user else "Đại học Duy Tân"

    base_caption = row["caption_cuoi"] or f"{row['chu_de']} — thông tin dành cho ngành {row['nganh']}."
    result = personalize_caption(base_caption, row["chu_de"], row["nganh"], ho_ten, khoa, tone)
    return jsonify({"id": content_id, "giong_van": tone, **result})


# Kho mẫu chủ đề theo nhóm giai đoạn — dùng cho AI lập kế hoạch tháng (chạy offline)
PLAN_TEMPLATES = {
    "Mùa tuyển sinh": [
        "Giới thiệu ngành {nganh}: học gì, làm gì sau tốt nghiệp",
        "Một ngày trải nghiệm của sinh viên ngành {nganh}",
        "Phỏng vấn cựu sinh viên {nganh} thành đạt",
        "Cơ sở vật chất phục vụ ngành {nganh}",
        "Học bổng dành cho thí sinh đăng ký ngành {nganh}",
        "5 câu hỏi thí sinh hay hỏi nhất về ngành {nganh}",
    ],
    "Mùa thi": [
        "Bí quyết ôn thi hiệu quả từ giảng viên {nganh}",
        "Lời nhắn gửi sĩ tử 2K8 từ khoa {nganh}",
        "Định hướng chọn ngành {nganh} trước kỳ thi",
    ],
    "Mùa nhập học": [
        "Hướng dẫn thủ tục nhập học cho tân sinh viên",
        "Checklist chuẩn bị trước ngày nhập học",
        "Đời sống ký túc xá và câu lạc bộ sinh viên",
    ],
    "Sự kiện thường niên": [
        "Sự kiện trải nghiệm thực tế dành cho học sinh THPT",
        "Ngày hội tư vấn ngành {nganh}",
        "Workshop kỹ năng cùng chuyên gia ngành {nganh}",
    ],
}
PLAN_NGANH = ["CNTT", "Kinh tế", "Y Dược", "Du lịch", "Ngôn ngữ", "Kiến trúc", "Toàn trường"]


@bp.post("/ke-hoach-thang")
@login_required(role="quan_ly")
def ai_month_plan():
    """
    AI lập kế hoạch nội dung 30 ngày tới: chọn nhóm bài theo thứ tự ưu tiên của mùa vụ
    hiện tại, xoay vòng ngành và kho mẫu chủ đề, rồi tạo thật các dòng "chờ soạn"
    trong lich_noi_dung để phòng truyền thông duyệt/sửa.
    """
    from datetime import timedelta
    payload = request.get_json(force=True, silent=True) or {}
    try:
        so_bai = min(max(int(payload.get("so_bai", 12)), 4), 20)
    except (ValueError, TypeError):
        return jsonify({"error": "so_bai phải là số nguyên"}), 400

    season = current_season()
    today = date.today()
    created = []
    for i in range(so_bai):
        # 60% nhóm ưu tiên nhất của mùa, 25% nhóm thứ hai, còn lại nhóm thứ ba
        if i % 5 < 3:
            giai_doan = season["uu_tien"][0]
        elif i % 5 == 3:
            giai_doan = season["uu_tien"][1]
        else:
            giai_doan = season["uu_tien"][2]
        nganh = PLAN_NGANH[i % len(PLAN_NGANH)]
        templates = PLAN_TEMPLATES.get(giai_doan, PLAN_TEMPLATES["Mùa tuyển sinh"])
        chu_de = templates[i % len(templates)].format(nganh=nganh)
        ngay = (today + timedelta(days=2 + round(i * 28 / so_bai))).isoformat()
        new_id = db.execute(
            """INSERT INTO lich_noi_dung (ngay_dang_du_kien, giai_doan, chu_de, nganh, ghi_chu, trang_thai)
               VALUES (?, ?, ?, ?, ?, 'cho_soan')""",
            (ngay, giai_doan, chu_de, nganh, f"AI lập kế hoạch — {season['ten']}"),
        )
        created.append({"id": new_id, "ngay_dang_du_kien": ngay, "giai_doan": giai_doan,
                        "chu_de": chu_de, "nganh": nganh})
    return jsonify({"mua_vu": season["ten"], "tao_moi": len(created), "items": created}), 201


@bp.post("/<int:content_id>/ab-caption")
@login_required(role="quan_ly")
def generate_ab_captions(content_id):
    """A/B testing caption: AI sinh 2 biến thể phong cách khác nhau để người duyệt chọn."""
    row = db.query("SELECT * FROM lich_noi_dung WHERE id = ?", (content_id,), fetchone=True)
    if row is None:
        return jsonify({"error": "Không tìm thấy mục lịch nội dung"}), 404
    result = ab_captions(row["chu_de"], row["giai_doan"], row["nganh"], row["caption_cuoi"] or "")
    return jsonify({"id": content_id, **result})


@bp.post("/<int:content_id>/chon-caption")
@login_required(role="quan_ly")
def choose_caption(content_id):
    """Lưu biến thể caption thắng cuộc (A hoặc B) làm caption chính thức, chuyển chờ duyệt."""
    row = db.query("SELECT id FROM lich_noi_dung WHERE id = ?", (content_id,), fetchone=True)
    if row is None:
        return jsonify({"error": "Không tìm thấy mục lịch nội dung"}), 404
    payload = request.get_json(force=True, silent=True) or {}
    caption = (payload.get("caption") or "").strip()
    if not caption:
        return jsonify({"error": "Thiếu caption"}), 400
    db.execute(
        "UPDATE lich_noi_dung SET caption_cuoi = ?, trang_thai = 'cho_duyet' WHERE id = ?",
        (caption, content_id),
    )
    return jsonify({"id": content_id, "trang_thai": "cho_duyet", "bien_the": payload.get("bien_the", "")})


@bp.post("/<int:content_id>/da-kenh")
@login_required()
def multi_channel(content_id):
    """Đa kênh phân phối: từ 1 bài sinh 3 biến thể Facebook / Zalo / kịch bản TikTok."""
    row = db.query("SELECT * FROM lich_noi_dung WHERE id = ?", (content_id,), fetchone=True)
    if row is None:
        return jsonify({"error": "Không tìm thấy bài viết"}), 404
    base = row["caption_cuoi"] or f"{row['chu_de']} — thông tin dành cho ngành {row['nganh']}."
    return jsonify({"id": content_id, **multi_channel_captions(base, row["chu_de"], row["nganh"])})


@bp.post("")
@login_required(role="quan_ly")
def create_content():
    payload = request.get_json(force=True, silent=True) or {}
    required = ["ngay_dang_du_kien", "giai_doan", "chu_de", "nganh"]
    missing = [f for f in required if not payload.get(f)]
    if missing:
        return jsonify({"error": f"Thiếu trường bắt buộc: {', '.join(missing)}"}), 400

    new_id = db.execute(
        """INSERT INTO lich_noi_dung (ngay_dang_du_kien, giai_doan, chu_de, nganh, ghi_chu, trang_thai)
           VALUES (?, ?, ?, ?, ?, 'cho_soan')""",
        (payload["ngay_dang_du_kien"], payload["giai_doan"], payload["chu_de"],
         payload["nganh"], payload.get("ghi_chu", "")),
    )
    return jsonify({"id": new_id, "message": "Đã thêm vào lịch nội dung"}), 201


@bp.post("/<int:content_id>/soan-nhap-ai")
@login_required(role="quan_ly")
def draft_with_ai(content_id):
    row = db.query("SELECT * FROM lich_noi_dung WHERE id = ?", (content_id,), fetchone=True)
    if row is None:
        return jsonify({"error": "Không tìm thấy mục lịch nội dung"}), 404

    caption = draft_caption(row["chu_de"], row["giai_doan"], row["nganh"], row["ghi_chu"] or "")
    db.execute(
        "UPDATE lich_noi_dung SET caption_cuoi = ?, trang_thai = 'cho_duyet' WHERE id = ?",
        (caption, content_id),
    )
    return jsonify({"id": content_id, "caption_cuoi": caption, "trang_thai": "cho_duyet"})


@bp.post("/<int:content_id>/duyet-va-dang")
@login_required(role="quan_ly")
def approve_and_publish(content_id):
    """
    Trong triển khai thật, endpoint này gọi Facebook Graph API để đăng bài.
    Ở đây mô phỏng bằng cách lưu link bài đăng giả lập — n8n workflow 01 sẽ đảm nhiệm
    phần gọi Facebook thật khi nối vào hạ tầng production.
    """
    row = db.query("SELECT * FROM lich_noi_dung WHERE id = ?", (content_id,), fetchone=True)
    if row is None:
        return jsonify({"error": "Không tìm thấy mục lịch nội dung"}), 404

    fake_post_link = f"https://facebook.com/duytanuniversity/posts/{content_id}"
    db.execute(
        "UPDATE lich_noi_dung SET trang_thai = 'da_dang', link_bai_dang = ? WHERE id = ?",
        (fake_post_link, content_id),
    )
    return jsonify({"id": content_id, "trang_thai": "da_dang", "link_bai_dang": fake_post_link})

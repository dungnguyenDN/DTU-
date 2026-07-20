"""
Route Chatbot AI — Nội dung 3 trong đề cương: chatbot công khai, không cần đăng nhập,
dành cho học sinh/thí sinh/phụ huynh. Khác với các route quản lý ở trên (yêu cầu đăng nhập),
route này CỐ Ý mở công khai — xem giải thích trong đề cương mục 6.2.1 về việc tách bạch
giữa Cổng chia sẻ nội dung (nội bộ) và Chatbot (công khai).
"""
from flask import Blueprint, request, jsonify
import database as db
from auth import login_required
from services.ai_service import answer_question

bp = Blueprint("chatbot_routes", __name__, url_prefix="/api/chatbot")


@bp.post("/hoi")
def ask():
    payload = request.get_json(force=True, silent=True) or {}
    question = (payload.get("cau_hoi") or "").strip()
    if not question:
        return jsonify({"error": "Thiếu câu hỏi"}), 400

    faq_rows = db.rows_to_list(db.query("SELECT * FROM faq"))
    result = answer_question(question, faq_rows)

    db.execute(
        "INSERT INTO chat_log (cau_hoi, cau_tra_loi, chuyen_tu_van_vien) VALUES (?, ?, ?)",
        (question, result["answer"], 1 if result["handoff"] else 0),
    )
    return jsonify(result)


@bp.post("/lead")
def capture_lead():
    """
    Thu lead tư vấn — công khai (không cần đăng nhập): khi chatbot phải chuyển tư vấn viên,
    thí sinh để lại tên + liên hệ để đội tuyển sinh gọi lại. Đây là mắt xích chuyển đổi
    thật sự của vòng phản hồi: câu hỏi -> lead -> hồ sơ.
    """
    payload = request.get_json(force=True, silent=True) or {}
    ho_ten = (payload.get("ho_ten") or "").strip()
    lien_he = (payload.get("lien_he") or "").strip()
    if not ho_ten or not lien_he:
        return jsonify({"error": "Thiếu ho_ten hoặc lien_he"}), 400
    new_id = db.execute(
        "INSERT INTO lead_tu_van (ho_ten, lien_he, cau_hoi) VALUES (?, ?, ?)",
        (ho_ten, lien_he, (payload.get("cau_hoi") or "").strip()),
    )
    return jsonify({"id": new_id, "message": "Đã ghi nhận — đội tư vấn tuyển sinh sẽ liên hệ bạn sớm nhất."}), 201


@bp.get("/leads")
@login_required(role="quan_ly")
def list_leads():
    rows = db.query("SELECT * FROM lead_tu_van ORDER BY thoi_gian DESC LIMIT 200")
    return jsonify(db.rows_to_list(rows))


@bp.put("/leads/<int:lead_id>")
@login_required(role="quan_ly")
def update_lead(lead_id):
    payload = request.get_json(force=True, silent=True) or {}
    trang_thai = payload.get("trang_thai")
    if trang_thai not in ("moi", "da_goi", "da_nop_ho_so"):
        return jsonify({"error": "trang_thai phải là moi | da_goi | da_nop_ho_so"}), 400
    row = db.query("SELECT id FROM lead_tu_van WHERE id = ?", (lead_id,), fetchone=True)
    if row is None:
        return jsonify({"error": "Không tìm thấy lead"}), 404
    db.execute("UPDATE lead_tu_van SET trang_thai = ? WHERE id = ?", (trang_thai, lead_id))
    return jsonify({"id": lead_id, "trang_thai": trang_thai})


@bp.get("/lich-su")
@login_required(role="quan_ly")
def history():
    limit = min(int(request.args.get("limit", 50)), 200)
    rows = db.query("SELECT * FROM chat_log ORDER BY thoi_gian DESC LIMIT ?", (limit,))
    return jsonify(db.rows_to_list(rows))


@bp.get("/chu-de-noi-bat")
@login_required(role="quan_ly")
def trending_topics():
    """
    Gom nhóm câu hỏi theo từ khoá FAQ khớp được — dùng cho panel "Chủ đề nổi bật tuần này"
    (thể hiện trực quan vòng phản hồi khép kín: câu hỏi thật -> gợi ý nội dung).
    """
    faq_rows = db.rows_to_list(db.query("SELECT * FROM faq"))
    chat_rows = db.rows_to_list(db.query("SELECT cau_hoi FROM chat_log ORDER BY thoi_gian DESC LIMIT 200"))

    topic_counts = {}
    for chat in chat_rows:
        q_lower = chat["cau_hoi"].lower()
        matched_topic = None
        for faq in faq_rows:
            keywords = [k.strip().lower() for k in faq["tu_khoa"].split(",") if k.strip()]
            if any(k in q_lower for k in keywords):
                matched_topic = keywords[0].capitalize()
                break
        topic_counts[matched_topic or "Khác"] = topic_counts.get(matched_topic or "Khác", 0) + 1

    total = sum(topic_counts.values()) or 1
    result = [
        {"topic": topic, "count": count, "pct": round(count / total * 100, 1)}
        for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1])
    ]
    return jsonify(result)


@bp.post("/tao-goi-y-tu-chu-de")
@login_required(role="quan_ly")
def create_suggestion_from_topic():
    """
    Đây chính là API triển khai thật cho nút "Tạo gợi ý nội dung từ chủ đề này" trên platform —
    khép vòng phản hồi: chủ đề hot từ chatbot -> tự tạo dòng mới trong lich_noi_dung chờ soạn.
    """
    payload = request.get_json(force=True, silent=True) or {}
    topic = payload.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "Thiếu topic"}), 400

    from datetime import date, timedelta
    target_date = (date.today() + timedelta(days=7)).isoformat()

    new_id = db.execute(
        """INSERT INTO lich_noi_dung (ngay_dang_du_kien, giai_doan, chu_de, nganh, ghi_chu, trang_thai)
           VALUES (?, 'Gợi ý từ Chatbot', ?, 'Toàn trường', ?, 'cho_soan')""",
        (target_date, f"Giải đáp về {topic}", f"Tự động tạo từ chủ đề câu hỏi nổi bật: {topic}"),
    )
    return jsonify({"id": new_id, "message": f"Đã tạo gợi ý nội dung về '{topic}' vào lịch nội dung, chờ soạn"}), 201

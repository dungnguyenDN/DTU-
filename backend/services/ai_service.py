"""
Lớp gọi AI (Anthropic Claude API) — tách riêng để dễ thay thế/kiểm thử.
Khi không có ANTHROPIC_API_KEY (ví dụ môi trường demo offline), các hàm sẽ
rơi về (fallback) kết quả rule-based thay vì lỗi 500 cho người dùng cuối.
"""
import json
import requests
from config import Config

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-sonnet-4-6"


def _call_claude(system: str, user_message: str, max_tokens: int = 400):
    if not Config.ANTHROPIC_API_KEY:
        return None  # fallback được xử lý ở nơi gọi hàm này
    try:
        resp = requests.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": Config.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": ANTHROPIC_MODEL,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user_message}],
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]
    except Exception:
        return None


def match_faq(question: str, faq_rows: list, top_k: int = 3) -> list:
    """Khớp câu hỏi với FAQ theo từ khoá — đơn giản, không cần vector DB, đủ dùng cho quy mô đề tài."""
    question_lower = question.lower()
    scored = []
    for row in faq_rows:
        keywords = [k.strip().lower() for k in row["tu_khoa"].split(",") if k.strip()]
        hits = sum(1 for k in keywords if k in question_lower)
        if hits > 0:
            scored.append((hits, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [row for _, row in scored[:top_k]]


def answer_question(question: str, faq_rows: list) -> dict:
    """
    Trả lời câu hỏi thí sinh dựa trên FAQ.
    Trả về {"answer": str, "handoff": bool, "source": "ai" | "rule_based"}
    """
    matched = match_faq(question, faq_rows)

    if not matched:
        return {
            "answer": "Xin lỗi, hiện tại hệ thống chưa có thông tin về câu hỏi này. "
                       "Đội ngũ tư vấn tuyển sinh sẽ liên hệ hỗ trợ bạn trong thời gian sớm nhất.",
            "handoff": True,
            "source": "rule_based",
        }

    context = "\n".join(f"- {m['cau_hoi']}: {m['cau_tra_loi']}" for m in matched)

    ai_text = _call_claude(
        system=(
            "Bạn là trợ lý tư vấn tuyển sinh của Đại học Duy Tân. "
            "Chỉ trả lời dựa trên ngữ cảnh FAQ được cung cấp. "
            "Nếu ngữ cảnh không đủ để trả lời chắc chắn, trả về đúng chuỗi: HANDOFF. "
            "Trả lời ngắn gọn, thân thiện, dưới 80 từ, không thêm lời chào/kết thừa thãi."
        ),
        user_message=f"Ngữ cảnh FAQ:\n{context}\n\nCâu hỏi của thí sinh: {question}",
    )

    if ai_text is None:
        # Fallback rule-based: trả lời trực tiếp bằng câu trả lời FAQ khớp nhất
        best = matched[0]
        return {"answer": best["cau_tra_loi"], "handoff": False, "source": "rule_based"}

    if ai_text.strip() == "HANDOFF":
        return {
            "answer": "Câu hỏi này cần tư vấn viên hỗ trợ trực tiếp, đội ngũ tuyển sinh sẽ phản hồi bạn trong ít phút.",
            "handoff": True,
            "source": "ai",
        }

    return {"answer": ai_text.strip(), "handoff": False, "source": "ai"}


TONE_LABELS = {
    "than_thien": "thân thiện, gần gũi, có emoji",
    "chuyen_nghiep": "chuyên nghiệp, chỉn chu, đáng tin cậy",
    "truyen_cam_hung": "truyền cảm hứng, giàu cảm xúc",
}


def personalize_caption(caption: str, chu_de: str, nganh: str, ho_ten: str, khoa: str, tone: str = "than_thien") -> dict:
    """
    Viết lại caption theo giọng văn cá nhân của giảng viên để bài chia sẻ trên trang
    Facebook cá nhân tự nhiên hơn (không copy nguyên văn bài fanpage).
    Trả về {"caption": str, "source": "ai" | "rule_based"}.
    """
    tone = tone if tone in TONE_LABELS else "than_thien"
    ai_text = _call_claude(
        system=(
            "Bạn giúp giảng viên đại học viết lại bài đăng của fanpage trường thành bài chia sẻ "
            "trên Facebook cá nhân của chính giảng viên đó. Giữ đúng thông tin, không bịa thêm số liệu. "
            "Viết như lời của giảng viên nói với học sinh/phụ huynh, dưới 130 từ, kèm 2-3 hashtag. "
            "Chỉ trả về đúng phần caption."
        ),
        user_message=(
            f"Giảng viên: {ho_ten}, {khoa}, Đại học Duy Tân.\n"
            f"Giọng văn mong muốn: {TONE_LABELS[tone]}.\n"
            f"Chủ đề: {chu_de} (ngành {nganh}).\n"
            f"Bài gốc của fanpage:\n{caption}"
        ),
        max_tokens=350,
    )
    if ai_text is not None:
        return {"caption": ai_text.strip(), "source": "ai"}

    # Fallback rule-based: bọc bài gốc trong khung lời dẫn phù hợp từng giọng văn,
    # để chế độ demo offline vẫn cho ra caption dùng được ngay.
    ten_ngan = ho_ten.split(". ")[-1] if ". " in ho_ten else ho_ten
    hashtag = f"#DaiHocDuyTan #{nganh.replace(' ', '').replace('-', '')} #TuyenSinh2026"
    if tone == "chuyen_nghiep":
        wrapped = (
            f"[{chu_de}]\n\n"
            f"Với vai trò giảng viên {khoa}, tôi xin chia sẻ thông tin chính thức từ Nhà trường "
            f"tới quý phụ huynh và các em học sinh quan tâm ngành {nganh}:\n\n{caption}\n\n"
            f"Quý phụ huynh và các em cần tư vấn thêm có thể liên hệ trực tiếp với tôi.\n{hashtag}"
        )
    elif tone == "truyen_cam_hung":
        wrapped = (
            f"✨ Mỗi mùa tuyển sinh, điều tôi mong nhất là các em tìm được ngành học khiến mình "
            f"muốn thức dậy mỗi sáng.\n\n{caption}\n\n"
            f"Nếu em đang phân vân về ngành {nganh}, cứ nhắn cho thầy/cô — biết đâu đây chính là "
            f"khởi đầu của em. 🌱\n{hashtag}"
        )
    else:  # than_thien
        wrapped = (
            f"Cả nhà ơi 👋 {ten_ngan} ở {khoa} đây!\n\n"
            f"Hôm nay mình muốn chia sẻ một thông tin rất đáng chú ý cho các bạn quan tâm ngành {nganh}:\n\n"
            f"{caption}\n\n📩 Bạn nào cần tư vấn thêm cứ inbox mình nhé!\n{hashtag}"
        )
    return {"caption": wrapped, "source": "rule_based"}


def _sentences(text: str) -> list:
    import re
    return [s.strip() for s in re.split(r"(?<=[.!?…])\s+", text or "") if s.strip()]


def multi_channel_captions(caption: str, chu_de: str, nganh: str) -> dict:
    """
    Từ 1 caption gốc, sinh 3 biến thể theo kênh: Facebook (giữ nguyên bản đầy đủ),
    Zalo (tin nhắn ngắn gọn), TikTok (kịch bản video 30 giây).
    Rule-based — chạy offline; khi có ANTHROPIC_API_KEY có thể nâng cấp từng biến thể.
    """
    sents = _sentences(caption)
    diem_1 = sents[0] if sents else chu_de
    diem_2 = sents[1] if len(sents) > 1 else f"Ngành {nganh} tại Đại học Duy Tân có nhiều điểm nổi bật đáng tìm hiểu."

    zalo = (
        f"📌 {chu_de}\n\n"
        f"{diem_1}\n\n"
        f"👉 Bạn quan tâm ngành {nganh}? Nhắn lại tin nhắn này để được thầy/cô tư vấn trực tiếp, "
        f"hoặc xem chi tiết tại trang tuyển sinh Đại học Duy Tân."
    )
    tiktok = (
        f"🎬 KỊCH BẢN VIDEO 30 GIÂY — {chu_de}\n\n"
        f"• 0-3s (hook): \"{chu_de}\" — điều mà nhiều bạn 2K8 chưa biết!\n"
        f"• 3-15s: {diem_1}\n"
        f"• 15-25s: {diem_2}\n"
        f"• 25-30s (CTA): Ghé trang tuyển sinh Đại học Duy Tân — link ở bio!\n\n"
        f"Nhạc nền: upbeat · Phụ đề: bật · #DaiHocDuyTan #TuyenSinh2026 #{nganh.replace(' ', '')}"
    )
    return {"facebook": caption, "zalo": zalo, "tiktok": tiktok, "source": "rule_based"}


def ab_captions(chu_de: str, giai_doan: str, nganh: str, caption_goc: str = "") -> dict:
    """
    Sinh 2 biến thể caption A/B để người duyệt chọn trước khi đăng:
    A — giọng thông tin, đáng tin cậy; B — giọng cảm xúc, mở đầu bằng câu hỏi gợi tò mò.
    """
    noi_dung = caption_goc or f"{chu_de} — thông tin chính thức dành cho ngành {nganh}, giai đoạn {giai_doan}."
    sents = _sentences(noi_dung)
    loi_ich = sents[0] if sents else chu_de

    variant_a = (
        f"[THÔNG TIN CHÍNH THỨC] {chu_de}\n\n{noi_dung}\n\n"
        f"Chi tiết đầy đủ tại trang tuyển sinh Đại học Duy Tân.\n#DaiHocDuyTan #TuyenSinh2026"
    )
    variant_b = (
        f"Bạn đã biết điều này về ngành {nganh} chưa? 🤔\n\n{loi_ich}\n\n"
        f"Còn nhiều điều thú vị nữa đang chờ bạn khám phá — thả tim nếu bạn quan tâm, "
        f"và inbox ngay để được tư vấn nhé!\n#DaiHocDuyTan #{nganh.replace(' ', '')}"
    )
    ai_a = _call_claude(
        system="Bạn là biên tập viên truyền thông tuyển sinh Đại học Duy Tân.",
        user_message=(
            f"Viết caption Facebook giọng THÔNG TIN, chuyên nghiệp (dưới 100 từ, 2 hashtag) cho: "
            f"{chu_de} (ngành {nganh}, {giai_doan}). Nội dung gốc: {noi_dung}. Chỉ trả về caption."
        ),
    )
    ai_b = _call_claude(
        system="Bạn là biên tập viên truyền thông tuyển sinh Đại học Duy Tân.",
        user_message=(
            f"Viết caption Facebook giọng CẢM XÚC, mở đầu bằng câu hỏi gợi tò mò (dưới 100 từ, 2 hashtag) cho: "
            f"{chu_de} (ngành {nganh}, {giai_doan}). Nội dung gốc: {noi_dung}. Chỉ trả về caption."
        ),
    )
    return {
        "A": {"caption": (ai_a or variant_a).strip(), "phong_cach": "Thông tin — đáng tin cậy"},
        "B": {"caption": (ai_b or variant_b).strip(), "phong_cach": "Cảm xúc — gợi tò mò"},
        "source": "ai" if (ai_a and ai_b) else "rule_based",
    }


def draft_caption(chu_de: str, giai_doan: str, nganh: str, ghi_chu: str = "") -> str:
    """Soạn nháp caption Facebook cho một mục lịch nội dung (dùng ở luồng n8n 01 hoặc gọi trực tiếp từ backend)."""
    ai_text = _call_claude(
        system="Bạn là biên tập viên truyền thông tuyển sinh của Đại học Duy Tân.",
        user_message=(
            f"Hãy soạn 1 caption Facebook (dưới 120 từ, có 2-3 hashtag phù hợp) cho nội dung sau:\n"
            f"Chủ đề: {chu_de}\nGiai đoạn mùa vụ: {giai_doan}\nNgành: {nganh}\nGhi chú thêm: {ghi_chu}\n"
            f"Chỉ trả về đúng phần caption, không giải thích thêm."
        ),
        max_tokens=300,
    )
    if ai_text is None:
        return (
            f"[Nháp tự động - chế độ offline] {chu_de} — thông tin dành cho ngành {nganh}, "
            f"phù hợp giai đoạn {giai_doan}. {ghi_chu}\n#DaiHocDuyTan #{nganh.replace(' ', '')}"
        )
    return ai_text.strip()

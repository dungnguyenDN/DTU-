"""
Logic phân tích & tính toán KPI — tách riêng khỏi route để dễ kiểm thử (unit test)
độc lập với Flask/HTTP.
"""
from config import Config

TIER_THRESHOLDS = [
    (15, "Kim Cương", "diamond"),
    (10, "Vàng", "gold"),
    (5, "Bạc", "silver"),
    (0, "Đồng", "bronze"),
]


def tier_for(total_shares_lifetime: int) -> dict:
    """Xác định cấp bậc giảng viên dựa trên tổng số bài chia sẻ lũy kế (không chỉ đợt hiện tại)."""
    for threshold, label, css_class in TIER_THRESHOLDS:
        if total_shares_lifetime >= threshold:
            return {"label": label, "class": css_class, "threshold": threshold}
    return {"label": "Đồng", "class": "bronze", "threshold": 0}


def progress_ratio(count: int, target: int = None) -> float:
    target = target or Config.SHARE_TARGET_PER_PERIOD
    if target <= 0:
        return 0.0
    return min(count / target, 1.0)


def compute_engagement_rate(impressions: int, engaged_users: int) -> float:
    if not impressions:
        return 0.0
    return round(engaged_users / impressions * 100, 2)


def compute_funnel(stages: list) -> list:
    """
    stages: [{"label": str, "value": int}, ...] theo thứ tự từ rộng đến hẹp.
    Trả về thêm phần trăm so với tầng đầu và tỷ lệ rơi so với tầng liền trước.
    """
    if not stages:
        return []
    top_value = stages[0]["value"] or 1
    result = []
    prev_value = None
    for stage in stages:
        pct_of_top = round(stage["value"] / top_value * 100, 1)
        drop_pct = None
        if prev_value is not None and prev_value > 0:
            drop_pct = round(100 - (stage["value"] / prev_value * 100), 1)
        result.append({
            "label": stage["label"],
            "value": stage["value"],
            "pct_of_top": pct_of_top,
            "drop_from_prev_pct": drop_pct,
        })
        prev_value = stage["value"]
    return result


def compute_conversion_rate(clicks: int, applications: int) -> float:
    if not clicks:
        return 0.0
    return round(applications / clicks * 100, 1)


def build_weekly_insight(top_content: dict, top_chat_topics: list, top_teachers: list, benchmark_leader: bool) -> str:
    """
    Sinh nhận định tuần dạng rule-based (fallback khi không có AI key).
    Khi có ANTHROPIC_API_KEY, ai_service.py sẽ ưu tiên gọi AI để viết tự nhiên hơn.
    """
    parts = []
    if top_content:
        parts.append(
            f"Nội dung \"{top_content.get('chu_de', '')}\" (ngành {top_content.get('nganh', '')}) "
            f"đang có tương tác nổi bật nhất tuần này."
        )
    if top_chat_topics:
        topic_str = ", ".join(t["topic"] for t in top_chat_topics[:2])
        parts.append(f"Chủ đề {topic_str} chiếm tỷ lệ câu hỏi cao nhất từ thí sinh — nên ưu tiên cho đợt nội dung tới.")
    if top_teachers:
        names = ", ".join(t["ho_ten"] for t in top_teachers[:2])
        parts.append(f"{names} là những giảng viên tạo hiệu quả chuyển đổi cao nhất tuần này.")
    if benchmark_leader:
        parts.append("So với các trường đối sánh, tốc độ tăng trưởng hiện đang dẫn đầu nhóm benchmark.")
    if not parts:
        return "Chưa đủ dữ liệu để đưa ra nhận định tuần này — hãy chạy thêm workflow thu thập số liệu."
    return " ".join(parts)

"""
Dịch vụ mùa vụ truyền thông — trái tim của tính năng "AI đề xuất bài đăng theo mùa"
trên Cổng chia sẻ giảng viên.

Logic gồm 3 phần, tất cả đều chạy được offline (không cần API key):
1. Nhận diện giai đoạn mùa vụ hiện tại theo lịch tuyển sinh Việt Nam.
2. Chấm điểm mức phù hợp của từng bài đã đăng với thời điểm hiện tại.
3. Sinh lý do đề xuất dễ hiểu cho giảng viên (rule-based; Claude nâng cấp thêm nếu có key).
"""
from datetime import date, datetime

# Lịch mùa vụ truyền thông tuyển sinh (tháng dương lịch).
# "uu_tien" là thứ tự ưu tiên các nhóm bài (giai_doan trong lich_noi_dung) ở mùa đó.
SEASONS = [
    {
        "key": "huong_nghiep",
        "ten": "Mùa tư vấn hướng nghiệp",
        "months": [1, 2, 3, 4],
        "mo_ta": "Học sinh lớp 12 đang tìm hiểu ngành nghề — ưu tiên bài giới thiệu ngành, trải nghiệm sinh viên.",
        "uu_tien": ["Mùa tuyển sinh", "Sự kiện thường niên", "Mùa thi", "Mùa nhập học"],
        "khung_gio_vang": "19:30 – 21:30",
        "hashtag": "#HuongNghiep2026",
        "icon": "🧭",
    },
    {
        "key": "mua_thi",
        "ten": "Mùa thi THPT",
        "months": [5, 6],
        "mo_ta": "Thí sinh tập trung ôn thi — ưu tiên bài động viên, mẹo ôn tập, thông tin xét tuyển sớm.",
        "uu_tien": ["Mùa thi", "Mùa tuyển sinh", "Sự kiện thường niên", "Mùa nhập học"],
        "khung_gio_vang": "20:00 – 22:00",
        "hashtag": "#VungTinMuaThi",
        "icon": "📚",
    },
    {
        "key": "cao_diem_xet_tuyen",
        "ten": "Cao điểm xét tuyển",
        "months": [7, 8],
        "mo_ta": "Thí sinh đang đăng ký nguyện vọng — thời điểm vàng để lan toả bài về ngành học, học bổng, cơ hội việc làm.",
        "uu_tien": ["Mùa tuyển sinh", "Sự kiện thường niên", "Mùa nhập học", "Mùa thi"],
        "khung_gio_vang": "11:30 – 13:00 và 20:00 – 21:30",
        "hashtag": "#XetTuyen2026",
        "icon": "🔥",
    },
    {
        "key": "nhap_hoc",
        "ten": "Mùa nhập học",
        "months": [9, 10],
        "mo_ta": "Tân sinh viên làm thủ tục nhập học — ưu tiên bài hướng dẫn nhập học, đời sống sinh viên, ký túc xá.",
        "uu_tien": ["Mùa nhập học", "Sự kiện thường niên", "Mùa tuyển sinh", "Mùa thi"],
        "khung_gio_vang": "12:00 – 13:30",
        "hashtag": "#ChaoTanSinhVien",
        "icon": "🎒",
    },
    {
        "key": "gan_ket",
        "ten": "Mùa gắn kết & sự kiện",
        "months": [11, 12],
        "mo_ta": "Giai đoạn nuôi dưỡng cộng đồng — ưu tiên bài sự kiện, thành tích sinh viên, hoạt động khoa.",
        "uu_tien": ["Sự kiện thường niên", "Mùa tuyển sinh", "Mùa nhập học", "Mùa thi"],
        "khung_gio_vang": "19:00 – 21:00",
        "hashtag": "#DTUCommunity",
        "icon": "🎉",
    },
]

# Điểm cộng theo thứ hạng ưu tiên của nhóm bài trong mùa hiện tại.
PRIORITY_POINTS = [50, 30, 15, 5]


def current_season(today: date = None) -> dict:
    """Trả về giai đoạn mùa vụ ứng với ngày hiện tại (mặc định: hôm nay)."""
    today = today or date.today()
    for season in SEASONS:
        if today.month in season["months"]:
            return season
    return SEASONS[0]  # không bao giờ xảy ra, nhưng an toàn


def score_post(post: dict, season: dict, today: date = None, engagement_rate: float = 0.0) -> int:
    """
    Chấm điểm 0-100 mức phù hợp của một bài với thời điểm hiện tại:
    - Nhóm bài (giai_doan) khớp thứ tự ưu tiên của mùa: tối đa 50 điểm.
    - Ngày đăng dự kiến gần hôm nay: tối đa 30 điểm (giảm 3 điểm mỗi ngày lệch).
    - Tỷ lệ tương tác lịch sử của bài: tối đa 20 điểm.
    """
    today = today or date.today()

    try:
        rank = season["uu_tien"].index(post["giai_doan"])
        season_points = PRIORITY_POINTS[rank]
    except (ValueError, IndexError):
        season_points = 0

    try:
        post_date = datetime.strptime(post["ngay_dang_du_kien"], "%Y-%m-%d").date()
        days_diff = abs((post_date - today).days)
        date_points = max(0, 30 - days_diff * 3)
    except (ValueError, TypeError):
        date_points = 0

    engagement_points = min(20, round(engagement_rate * 2.5))

    return min(100, season_points + date_points + engagement_points)


def build_reason(post: dict, season: dict, score: int, engagement_rate: float = 0.0) -> str:
    """Sinh lý do đề xuất ngắn gọn, dễ hiểu cho giảng viên (rule-based, chạy offline)."""
    parts = []
    if post["giai_doan"] == season["uu_tien"][0]:
        parts.append(f"đúng nhóm nội dung được ưu tiên nhất trong {season['ten']}")
    else:
        parts.append(f"phù hợp với {season['ten']}")
    if engagement_rate >= 6:
        parts.append(f"bài đang có tỷ lệ tương tác cao ({engagement_rate:.1f}%)")
    elif engagement_rate > 0:
        parts.append(f"tỷ lệ tương tác {engagement_rate:.1f}%")
    if post.get("nganh") and post["nganh"] != "Toàn trường":
        parts.append(f"giúp lan toả ngành {post['nganh']}")
    return "Bài này " + ", ".join(parts) + f". Nên đăng trong khung giờ vàng {season['khung_gio_vang']}."

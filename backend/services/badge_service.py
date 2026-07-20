"""
Dịch vụ huy hiệu thành tích (gamification) cho Cổng chia sẻ giảng viên.
Logic thuần — nhận số liệu đã tổng hợp, trả danh sách huy hiệu kèm trạng thái
đạt/chưa đạt và tiến độ, để route chỉ lo phần truy vấn DB.
"""
from datetime import datetime, timedelta


def max_streak(date_strings) -> int:
    """Chuỗi ngày liên tiếp dài nhất từ danh sách ngày 'YYYY-MM-DD' (trùng lặp được bỏ qua)."""
    days = sorted({datetime.strptime(d, "%Y-%m-%d").date() for d in date_strings if d})
    if not days:
        return 0
    best = cur = 1
    for prev, nxt in zip(days, days[1:]):
        cur = cur + 1 if nxt - prev == timedelta(days=1) else 1
        best = max(best, cur)
    return best


def compute_badges(tong_luy_ke: int, so_bai_dot_nay: int, target: int,
                   tong_click: int, ngay_chia_se: list, so_nganh: int, hang) -> list:
    """
    Trả về danh sách 6 huy hiệu, mỗi cái: {key, ten, mo_ta, icon, dat, tien_do}.
    tien_do là chuỗi "x/y" cho huy hiệu chưa đạt (để UI vẽ thanh tiến độ).
    """
    streak = max_streak(ngay_chia_se)
    badges = [
        {
            "key": "khoi_dong", "ten": "Khởi động", "icon": "zap",
            "mo_ta": "Chia sẻ bài viết đầu tiên của bạn",
            "dat": tong_luy_ke >= 1,
            "tien_do": f"{min(tong_luy_ke, 1)}/1",
        },
        {
            "key": "dat_chi_tieu", "ten": "Đạt chỉ tiêu", "icon": "target",
            "mo_ta": f"Hoàn thành {target} bài trong một đợt truyền thông",
            "dat": so_bai_dot_nay >= target,
            "tien_do": f"{min(so_bai_dot_nay, target)}/{target}",
        },
        {
            "key": "chuoi_3_ngay", "ten": "Chuỗi 3 ngày", "icon": "flame",
            "mo_ta": "Chia sẻ bài trong 3 ngày liên tiếp",
            "dat": streak >= 3,
            "tien_do": f"{min(streak, 3)}/3",
        },
        {
            "key": "nam_cham_click", "ten": "Nam châm click", "icon": "link",
            "mo_ta": "Đạt 100 lượt click lũy kế từ link bạn chia sẻ",
            "dat": tong_click >= 100,
            "tien_do": f"{min(tong_click, 100)}/100",
        },
        {
            "key": "da_nganh", "ten": "Lan toả đa ngành", "icon": "users",
            "mo_ta": "Chia sẻ bài viết của 3 ngành khác nhau",
            "dat": so_nganh >= 3,
            "tien_do": f"{min(so_nganh, 3)}/3",
        },
        {
            "key": "top3", "ten": "Top 3 toàn trường", "icon": "trophy",
            "mo_ta": "Vào top 3 bảng xếp hạng của đợt",
            "dat": hang is not None and hang <= 3,
            "tien_do": f"hạng #{hang}" if hang else "—",
        },
    ]
    return badges

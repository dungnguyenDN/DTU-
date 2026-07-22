"""
Script tạo dữ liệu mẫu thực tế để chạy demo / kiểm thử.
Chạy: python seed_data.py
"""
import sys
import os
from datetime import date
sys.path.insert(0, os.path.dirname(__file__))

import database as db
from auth import hash_password

TODAY_OFFSET_DAYS = 0  # có thể chỉnh để dữ liệu luôn "gần đây" so với ngày chạy demo


def clear_all():
    # Xóa theo thứ tự an toàn khóa ngoại (bảng con trước, bảng cha sau).
    for table in ["share_log", "kpi_dashboard", "chat_log", "funnel_source",
                  "benchmark_truong", "faq", "lich_noi_dung", "giang_vien", "lead_tu_van"]:
        db.execute(f"DELETE FROM {table}")


def seed():
    db.init_db()
    clear_all()

    # ===== Giảng viên & quản lý =====
    giang_vien_list = [
        ("GV001", "ThS. Nguyễn Văn A", "nguyenvana@duytan.edu.vn", "Khoa CNTT", "giang_vien"),
        ("GV002", "TS. Trần Thị B", "tranthib@duytan.edu.vn", "Khoa Kinh tế", "giang_vien"),
        ("GV003", "ThS. Lê Văn C", "levanc@duytan.edu.vn", "Khoa Kiến trúc", "giang_vien"),
        ("GV004", "TS. Phạm Thị D", "phamthid@duytan.edu.vn", "Khoa Y Dược", "giang_vien"),
        ("GV005", "ThS. Hoàng Văn E", "hoangvane@duytan.edu.vn", "Khoa Du lịch", "giang_vien"),
        ("GV006", "ThS. Ngô Thị F", "ngothif@duytan.edu.vn", "Khoa Ngôn ngữ", "giang_vien"),
        ("GV007", "ThS. Đặng Văn G", "dangvang@duytan.edu.vn", "Khoa CNTT", "giang_vien"),
        ("GV008", "TS. Bùi Thị H", "buithih@duytan.edu.vn", "Khoa Kinh tế", "giang_vien"),
        ("GV009", "ThS. Vũ Văn I", "vuvani@duytan.edu.vn", "Khoa Y Dược", "giang_vien"),
        ("GV010", "CN. Đỗ Thị K", "dothik@duytan.edu.vn", "Khoa Du lịch", "giang_vien"),
        ("GV011", "ThS. Lý Văn L", "lyvanl@duytan.edu.vn", "Khoa Ngôn ngữ", "giang_vien"),
        ("GV012", "TS. Mai Thị M", "maithim@duytan.edu.vn", "Khoa Kiến trúc", "giang_vien"),
        ("QL001", "CN. Truyền thông Tuyển sinh", "truyenthong@duytan.edu.vn", "Phòng Truyền thông", "quan_ly"),
    ]
    teacher_ids = {}
    default_password = "DemoPass123!"
    for ma, ho_ten, email, khoa, vai_tro in giang_vien_list:
        tid = db.execute(
            """INSERT INTO giang_vien (ma_giang_vien, ho_ten, email, khoa, mat_khau_hash, vai_tro)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (ma, ho_ten, email, khoa, hash_password(default_password), vai_tro),
        )
        teacher_ids[ma] = tid

    # ===== Lịch nội dung =====
    # Cột cuối (noi_dung) là nội dung bài đăng đầy đủ — lưu vào caption_cuoi để
    # trang tuyển sinh công khai có nội dung thật để đọc, không chỉ tiêu đề.
    content_items = [
        ("2026-07-08", "Mùa tuyển sinh", "Vì sao chọn Du lịch - Khách sạn", "Du lịch", "", "da_dang",
         "Ngành Du lịch - Khách sạn tại Đại học Duy Tân đưa sinh viên vào môi trường thực hành ngay từ năm 2, "
         "thông qua hệ thống khách sạn 4-5 sao đối tác tại Đà Nẵng. Sinh viên được luân phiên qua các bộ phận "
         "lễ tân, buồng phòng, ẩm thực và tổ chức sự kiện, tích lũy kinh nghiệm thực chiến song song với lý thuyết. "
         "Nhiều cựu sinh viên hiện đang giữ vị trí quản lý tại các chuỗi khách sạn lớn trong và ngoài nước."),
        ("2026-07-09", "Mùa tuyển sinh", "5 lý do học Ngôn ngữ Hàn tại DTU", "Ngôn ngữ", "", "da_dang",
         "Chương trình Ngôn ngữ Hàn của trường có 5 điểm nổi bật: giảng viên bản ngữ tham gia giảng dạy, "
         "chuẩn đầu ra TOPIK cấp 4 trở lên, học bổng trao đổi tại các đại học Hàn Quốc, câu lạc bộ văn hóa Hàn "
         "sinh hoạt hàng tuần, và mạng lưới doanh nghiệp Hàn Quốc tại Đà Nẵng nhận sinh viên thực tập, tuyển dụng."),
        ("2026-07-10", "Mùa tuyển sinh", "Trải nghiệm sinh viên ngành Kinh tế", "Kinh tế", "", "da_dang",
         "\"Học kỳ doanh nghiệp\" là điểm khác biệt của ngành Kinh tế - Quản trị tại DTU: sinh viên năm 3 được "
         "tham gia dự án thật cùng doanh nghiệp đối tác, từ nghiên cứu thị trường đến đề xuất chiến lược. "
         "Chia sẻ từ sinh viên khóa trước cho thấy đây là cơ hội để cọ xát thực tế trước khi ra trường, "
         "nhiều bạn được giữ lại thực tập hưởng lương ngay sau dự án."),
        ("2026-07-11", "Mùa tuyển sinh", "Góc học tập ngành Ngôn ngữ", "Ngôn ngữ", "", "da_dang",
         "Khoa Ngôn ngữ đầu tư phòng lab đa phương tiện phục vụ luyện nghe - nói theo chuẩn quốc tế, cùng thư viện "
         "song ngữ hơn 5.000 đầu sách. Sinh viên 4 chuyên ngành Anh, Trung, Hàn, Nhật đều có không gian luyện tập "
         "riêng và được khuyến khích tham gia câu lạc bộ giao lưu văn hóa để thực hành ngôn ngữ mỗi ngày."),
        ("2026-07-12", "Sự kiện thường niên", "Ngày hội tư vấn tuyển sinh", "Toàn trường", "", "da_dang",
         "Ngày hội tư vấn tuyển sinh 2026 quy tụ đại diện tất cả các khoa, giải đáp trực tiếp về ngành học, "
         "học phí, học bổng và điều kiện xét tuyển. Sự kiện còn có khu trải nghiệm thực tế ảo phòng Lab Kiến trúc, "
         "phòng thực hành Y Dược và khu vực tư vấn hướng nghiệp 1-1 cùng giảng viên từng khoa."),
        ("2026-07-13", "Mùa tuyển sinh", "Phỏng vấn cựu sinh viên CNTT", "CNTT", "", "da_dang",
         "\"Kiến thức nền tảng vững và cơ hội thực tập từ năm 3 là điều giúp mình tự tin ứng tuyển ngay khi "
         "còn ngồi trên ghế nhà trường\" — chia sẻ từ một cựu sinh viên CNTT khóa 2022, hiện đang là kỹ sư phần mềm "
         "tại một công ty công nghệ ở Đà Nẵng. Chương trình đào tạo cập nhật liên tục theo xu hướng AI, dữ liệu lớn."),
        ("2026-07-14", "Mùa tuyển sinh", "Một ngày ở phòng Lab Kiến trúc", "Kiến trúc", "", "da_dang",
         "Xưởng thiết kế (studio) của Khoa Kiến trúc mở cửa xuyên suốt để sinh viên phát triển đồ án, với sự "
         "đồng hành trực tiếp của các kiến trúc sư đang hành nghề. Từ phác thảo tay đến mô hình 3D, sinh viên được "
         "rèn tư duy thiết kế qua các đồ án thật, nhiều sản phẩm từng được trưng bày tại triển lãm kiến trúc trẻ."),
        ("2026-07-15", "Mùa thi", "Quy chế thi học kỳ hè", "Toàn trường", "", "da_dang",
         "Phòng Đào tạo thông báo lịch thi học kỳ hè 2026 dự kiến bắt đầu từ giữa tháng 8. Sinh viên cần đăng ký "
         "học phần qua hệ thống quản lý đào tạo trước ngày 25/7, kiểm tra lại lịch thi chi tiết theo từng khoa "
         "và liên hệ cố vấn học tập nếu có môn học bị trùng lịch."),
        ("2026-07-16", "Mùa tuyển sinh", "Học bổng tân sinh viên", "Toàn trường", "", "da_dang",
         "Đại học Duy Tân dành nhiều suất học bổng cho tân sinh viên 2026: học bổng tuyển sinh giảm 25-100% học phí "
         "năm nhất dựa trên kết quả học tập THPT, học bổng khuyến khích theo kết quả từng học kỳ, và học bổng riêng "
         "cho thí sinh có hoàn cảnh khó khăn vươn lên trong học tập. Hồ sơ xét học bổng nộp cùng hồ sơ xét tuyển."),
        ("2026-07-17", "Mùa tuyển sinh", "Cơ sở vật chất Khoa CNTT", "CNTT", "", "cho_duyet", ""),
        ("2026-07-17", "Mùa tuyển sinh", "Review cựu sinh viên Kinh tế", "Kinh tế", "", "cho_duyet", ""),
        ("2026-07-18", "Mùa tuyển sinh", "Giới thiệu ngành CNTT", "CNTT", "", "da_dang",
         "Ngành Công nghệ thông tin tại DTU đào tạo theo 4 định hướng: Kỹ thuật phần mềm, Khoa học dữ liệu - AI, "
         "An toàn thông tin và Mạng máy tính. Sinh viên được thực hành trên phòng máy cấu hình cao, tham gia dự án "
         "thật cùng doanh nghiệp công nghệ đối tác từ năm 3, và có cơ hội thực tập hưởng lương trước khi tốt nghiệp."),
        ("2026-07-19", "Mùa tuyển sinh", "Học bổng tài năng Kiến trúc", "Kiến trúc", "", "cho_duyet", ""),
        ("2026-07-20", "Mùa tuyển sinh", "Cơ hội việc làm ngành Y Dược", "Y Dược", "", "cho_soan", ""),
        ("2026-07-21", "Mùa nhập học", "Hướng dẫn nhập học trực tuyến", "Toàn trường", "", "cho_duyet", ""),
        ("2026-07-22", "Mùa tuyển sinh", "Trải nghiệm thực tế ngành Du lịch", "Du lịch", "", "cho_soan", ""),
        ("2026-07-23", "Mùa tuyển sinh", "Góc nhìn sinh viên Y Dược", "Y Dược", "", "cho_soan", ""),
        ("2026-07-24", "Mùa tuyển sinh", "Học bổng doanh nghiệp đồng hành", "Kinh tế", "", "cho_soan", ""),
        ("2026-07-25", "Sự kiện thường niên", "Ngày hội thể thao sinh viên", "Toàn trường", "", "cho_soan", ""),
        ("2026-07-26", "Mùa nhập học", "Checklist hồ sơ nhập học", "Toàn trường", "", "cho_soan", ""),
        ("2026-07-20", "Mùa nhập học", "Ký túc xá & đời sống tân sinh viên", "Toàn trường", "", "da_dang",
         "Nhập học xa nhà không đáng lo: ký túc xá Đại học Duy Tân nằm gần các cơ sở đào tạo, phòng ở sạch sẽ, "
         "an ninh 24/7 và chi phí phù hợp với sinh viên. Xung quanh trường là hệ sinh thái quán ăn, thư viện, "
         "sân thể thao — tân sinh viên đăng ký chỗ ở ngay khi làm thủ tục nhập học để được ưu tiên chọn phòng."),
        ("2026-07-21", "Sự kiện thường niên", "DTU Open Day — Một ngày làm sinh viên", "Toàn trường", "", "da_dang",
         "DTU Open Day mở cửa toàn bộ khuôn viên cho học sinh THPT trải nghiệm: ngồi thử một tiết học đại học, "
         "tham quan phòng lab các khoa, giao lưu cùng sinh viên và nhận tư vấn chọn ngành 1-1. Sự kiện diễn ra "
         "cuối tháng 7 — đăng ký miễn phí, kèm xe đưa đón từ trung tâm Đà Nẵng."),
        ("2026-07-19", "Mùa tuyển sinh", "Cơ hội việc làm ngành Y Dược", "Y Dược", "", "da_dang",
         "Nhu cầu nhân lực Y Dược tại miền Trung tăng đều mỗi năm. Sinh viên Y Dược DTU được thực hành tại "
         "bệnh viện và cơ sở y tế đối tác ngay trong chương trình học, có giảng viên là bác sĩ đang hành nghề "
         "hướng dẫn trực tiếp. Tỷ lệ sinh viên có việc làm trong 1 năm sau tốt nghiệp của khoa đạt trên 94%."),
    ]
    content_ids = []
    for ngay, giai_doan, chu_de, nganh, ghi_chu, trang_thai, noi_dung in content_items:
        link = f"https://facebook.com/duytanuniversity/posts/demo-{chu_de[:10]}" if trang_thai == "da_dang" else None
        cid = db.execute(
            """INSERT INTO lich_noi_dung (ngay_dang_du_kien, giai_doan, chu_de, nganh, ghi_chu, trang_thai, link_bai_dang, caption_cuoi)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (ngay, giai_doan, chu_de, nganh, ghi_chu, trang_thai, link, noi_dung or None),
        )
        content_ids.append((cid, nganh, trang_thai))

    # ===== KPI dashboard (số liệu tương tác cho các bài đã đăng) =====
    import random
    random.seed(42)
    for cid, nganh, trang_thai in content_ids:
        if trang_thai != "da_dang":
            continue
        luot_xem = random.randint(15000, 55000)
        luot_tuong_tac = int(luot_xem * random.uniform(0.04, 0.09))
        luot_click = int(luot_tuong_tac * random.uniform(0.15, 0.3))
        ty_le = round(luot_tuong_tac / luot_xem * 100, 2)
        db.execute(
            """INSERT INTO kpi_dashboard (lich_noi_dung_id, ngay, nganh, luot_xem, luot_tuong_tac, luot_click, ty_le_tuong_tac)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (cid, date.today().isoformat(), nganh, luot_xem, luot_tuong_tac, luot_click, ty_le),
        )

    # ===== Share log (giảng viên đã chia sẻ) =====
    # Mỗi giảng viên có (số bài lũy kế các đợt trước, số bài trong đợt hiện tại) —
    # trải đều đủ 4 cấp bậc (Đồng/Bạc/Vàng/Kim Cương) và bảng xếp hạng đợt này sinh động.
    # Tài khoản demo GV001 được xếp 3/5 bài đợt này để màn hình demo có tiến độ đẹp.
    from datetime import datetime, timedelta
    share_plan = {
        "GV001": (10, 3), "GV002": (9, 4), "GV003": (6, 2), "GV004": (4, 2),
        "GV005": (2, 1), "GV006": (1, 0), "GV007": (14, 5), "GV008": (8, 3),
        "GV009": (5, 2), "GV010": (3, 1), "GV011": (1, 1), "GV012": (0, 0),
    }
    published_ids = [cid for cid, _, ts in content_ids if ts == "da_dang"]
    now = datetime.now()
    for ma, (so_bai_cu, so_bai_dot_nay) in share_plan.items():
        # Các đợt trước — mốc thời gian rải trong 2-6 tháng trước.
        for i in range(so_bai_cu):
            cid = published_ids[i % len(published_ids)] if published_ids else None
            ts = now - timedelta(days=random.randint(60, 180), hours=random.randint(0, 23))
            db.execute(
                """INSERT INTO share_log (giang_vien_id, lich_noi_dung_id, dot_truyen_thong, link_bai_dang, utm_link, luot_click, thoi_gian)
                   VALUES (?, ?, 'Đợt học kỳ 2 2025-2026', ?, ?, ?, ?)""",
                (teacher_ids[ma], cid,
                 f"https://facebook.com/duytanuniversity/posts/demo-{i}",
                 f"https://facebook.com/duytanuniversity/posts/demo-{i}?utm_source=giangvien&utm_content={ma}",
                 random.randint(3, 22), ts.strftime("%Y-%m-%d %H:%M:%S")),
            )
        # Đợt hiện tại — rải trong 12 ngày gần nhất để biểu đồ hoạt động 7 ngày có dữ liệu.
        for i in range(so_bai_dot_nay):
            cid = published_ids[(i * 3 + 1) % len(published_ids)] if published_ids else None
            ts = now - timedelta(days=random.randint(0, 11), hours=random.randint(1, 14))
            db.execute(
                """INSERT INTO share_log (giang_vien_id, lich_noi_dung_id, dot_truyen_thong, link_bai_dang, utm_link, luot_click, thoi_gian)
                   VALUES (?, ?, 'Đợt tuyển sinh 2026', ?, ?, ?, ?)""",
                (teacher_ids[ma], cid,
                 f"https://facebook.com/duytanuniversity/posts/demo-{i}",
                 f"https://facebook.com/duytanuniversity/posts/demo-{i}?utm_source=giangvien&utm_content={ma}",
                 random.randint(5, 45), ts.strftime("%Y-%m-%d %H:%M:%S")),
            )

    # ===== FAQ =====
    faq_items = [
        ("Học phí ngành CNTT năm 2026 là bao nhiêu?",
         "Học phí ngành CNTT năm học 2026-2027 dao động khoảng 27-32 triệu đồng/năm tùy chương trình, chi tiết xem tại trang tuyển sinh.",
         "học phí, cntt, công nghệ thông tin"),
        ("Điều kiện xét học bạ là gì?",
         "Thí sinh cần tốt nghiệp THPT và có tổng điểm trung bình 3 học kỳ (lớp 11 và học kỳ 1 lớp 12) đạt từ 18 điểm trở lên tùy ngành.",
         "xét tuyển, học bạ, điều kiện"),
        ("Trường có học bổng cho tân sinh viên không?",
         "Có nhiều loại học bổng: học bổng tuyển sinh (giảm 25-100% học phí năm nhất), học bổng khuyến khích học tập theo kết quả học kỳ.",
         "học bổng, tân sinh viên, ưu đãi"),
        ("Trường có ký túc xá không?",
         "Đại học Duy Tân có ký túc xá dành cho sinh viên ở xa với giá thuê ưu đãi, đăng ký ngay từ khi nhập học.",
         "ký túc xá, chỗ ở, nội trú"),
        ("Lịch thi học kỳ hè 2026 khi nào?",
         "Lịch thi học kỳ hè 2026 dự kiến diễn ra từ giữa tháng 8, sinh viên xem lịch chi tiết trên hệ thống quản lý đào tạo.",
         "lịch thi, quy chế thi, thi cử"),
        ("Ngành Kiến trúc có cơ hội thực tập không?",
         "Ngành Kiến trúc có chương trình thực tập tại các công ty đối tác từ năm 3, sinh viên được hướng dẫn trực tiếp bởi kiến trúc sư.",
         "kiến trúc, thực tập, cơ hội việc làm"),
        ("Ngành Du lịch - Khách sạn có liên kết doanh nghiệp không?",
         "Sinh viên Du lịch - Khách sạn thực hành tại hệ thống khách sạn đối tác ngay từ năm 2, có cơ hội việc làm sau tốt nghiệp.",
         "du lịch, khách sạn, thực tập, doanh nghiệp"),
        ("Điểm chuẩn năm 2025 của ngành CNTT là bao nhiêu?",
         "Điểm chuẩn ngành CNTT năm 2025 theo phương thức xét học bạ là 18 điểm, theo điểm thi THPT là 20 điểm — tham khảo thêm tại trang tuyển sinh.",
         "điểm chuẩn, cntt, xét tuyển"),
        ("Trường có chương trình trao đổi sinh viên quốc tế không?",
         "Đại học Duy Tân có chương trình liên kết và trao đổi sinh viên với các đại học đối tác tại Mỹ, Hàn Quốc, Đài Loan.",
         "trao đổi sinh viên, quốc tế, du học"),
        ("Lệ phí xét tuyển là bao nhiêu?",
         "Lệ phí xét tuyển là 30.000 đồng/hồ sơ theo quy định chung, có thể nộp trực tuyến qua cổng tuyển sinh.",
         "lệ phí, hồ sơ, xét tuyển"),
    ]
    for cau_hoi, cau_tra_loi, tu_khoa in faq_items:
        db.execute(
            "INSERT INTO faq (cau_hoi, cau_tra_loi, tu_khoa) VALUES (?, ?, ?)",
            (cau_hoi, cau_tra_loi, tu_khoa),
        )

    # ===== Chat log =====
    chat_items = [
        ("Học phí ngành CNTT năm 2026 là bao nhiêu?", 0),
        ("Em muốn xét học bạ thì cần điều kiện gì?", 0),
        ("Trường có ký túc xá cho sinh viên ở xa không?", 0),
        ("Em bị mất mã hồ sơ xét tuyển, phải làm sao?", 1),
        ("Ngành Kiến trúc có học bổng du học trao đổi không?", 1),
        ("Học bổng tân sinh viên áp dụng cho ngành nào?", 0),
        ("Lịch thi học kỳ hè có thay đổi không?", 0),
        ("Điểm chuẩn ngành CNTT năm ngoái là bao nhiêu?", 0),
        ("Ngành Du lịch - Khách sạn có thực tập ở đâu?", 0),
        ("Em muốn chuyển ngành sau khi nhập học có được không?", 1),
        ("Lệ phí xét tuyển đóng như thế nào?", 0),
        ("Trường có hỗ trợ vay vốn sinh viên không?", 1),
        ("Ngành Ngôn ngữ Hàn có học bổng trao đổi không?", 0),
        ("Em ở tỉnh xa, nộp hồ sơ xét tuyển online được không?", 0),
        ("Khoa Y Dược có phòng thực hành ra sao?", 0),
        ("Thời gian nhập học dự kiến năm 2026 là khi nào?", 0),
    ]
    for cau_hoi, handoff in chat_items:
        db.execute(
            "INSERT INTO chat_log (cau_hoi, cau_tra_loi, chuyen_tu_van_vien) VALUES (?, ?, ?)",
            (cau_hoi, "(demo log)", handoff),
        )

    # ===== Lead tư vấn (chatbot thu được khi chuyển tư vấn viên) =====
    lead_items = [
        ("Trần Minh Khoa", "0905 123 456", "Em bị mất mã hồ sơ xét tuyển, phải làm sao?", "da_goi", 3),
        ("Lê Thị Hồng Nhung", "zalo: 0912 888 999", "Ngành Kiến trúc có học bổng du học trao đổi không?", "da_nop_ho_so", 5),
        ("Phạm Quốc Bảo", "0987 654 321", "Em muốn chuyển ngành sau khi nhập học có được không?", "moi", 1),
        ("Ngô Thuỳ Dương", "duongnt2k8@gmail.com", "Trường có hỗ trợ vay vốn sinh viên không?", "moi", 0),
    ]
    from datetime import datetime as _dt, timedelta as _td
    for ho_ten, lien_he, cau_hoi, trang_thai, days_ago in lead_items:
        ts = (_dt.now() - _td(days=days_ago, hours=random.randint(1, 9))).strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            "INSERT INTO lead_tu_van (ho_ten, lien_he, cau_hoi, trang_thai, thoi_gian) VALUES (?, ?, ?, ?, ?)",
            (ho_ten, lien_he, cau_hoi, trang_thai, ts),
        )

    # ===== Benchmark đối thủ =====
    benchmark_items = [
        ("Đại học Duy Tân", 23, 6.4, "Video ngắn trải nghiệm sinh viên", 1),
        ("Trường A", 15, 4.8, "Bài viết + ảnh tuyển sinh", 0),
        ("Trường B", 19, 5.6, "Livestream tư vấn", 0),
        ("Trường C", 11, 3.9, "Thông báo tuyển sinh định kỳ", 0),
        ("Trường D", 17, 5.1, "Video phỏng vấn cựu sinh viên", 0),
        ("Trường E", 9, 3.2, "Bài viết học bổng định kỳ", 0),
    ]
    for ten, tt, te, dd, la_minh in benchmark_items:
        db.execute(
            """INSERT INTO benchmark_truong (ten_truong, tang_truong_follower, ty_le_tuong_tac, dinh_dang_chu_dao, la_truong_minh)
               VALUES (?, ?, ?, ?, ?)""",
            (ten, tt, te, dd, la_minh),
        )

    # ===== Funnel theo nguồn =====
    # Số liệu được thiết kế nhất quán với engaged ở kpi_dashboard (phễu phải giảm dần hợp lý)
    funnel_items = [
        ("Fanpage trường", 950, 96),
        ("Giảng viên chia sẻ", 540, 88),
        ("Chatbot dẫn về", 310, 54),
    ]
    for nguon, clicks, apps in funnel_items:
        db.execute(
            "INSERT INTO funnel_source (nguon, luot_click, ho_so_nop) VALUES (?, ?, ?)",
            (nguon, clicks, apps),
        )

    print("Da tao du lieu mau thanh cong.")
    print(f"   Dang nhap demo: nguyenvana@duytan.edu.vn / {default_password}  (vai tro: giang vien)")
    print(f"   Dang nhap demo: truyenthong@duytan.edu.vn / {default_password}  (vai tro: quan ly)")


def seed_if_empty():
    """
    Chỉ tạo dữ liệu mẫu khi CSDL đang trống (bảng giang_vien chưa có ai).
    Dùng cho production Postgres: seed đúng MỘT lần ở lần khởi động đầu, các lần sau
    giữ nguyên dữ liệu người dùng nhập (không bị xóa mỗi lần restart).
    """
    db.init_db()
    row = db.query("SELECT COUNT(*) AS c FROM giang_vien", fetchone=True)
    count = row["c"] if row else 0
    if count and int(count) > 0:
        print(f"CSDL da co {count} nguoi dung - bo qua seed (giu du lieu hien co).")
        return
    seed()


if __name__ == "__main__":
    # `python seed_data.py`            -> tạo lại toàn bộ (xóa sạch rồi seed) — dùng khi reset local
    # `python seed_data.py --if-empty` -> chỉ seed khi CSDL trống — dùng cho production (giữ dữ liệu)
    if "--if-empty" in sys.argv:
        seed_if_empty()
    else:
        seed()

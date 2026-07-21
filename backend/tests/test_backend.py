"""
Bộ kiểm thử tự động — chạy: python -m unittest discover -s tests -v
Dùng unittest (thư viện chuẩn) + Flask test_client(), không phụ thuộc pytest
để đảm bảo chạy được ở mọi môi trường không có internet.
"""
import sys
import os
import unittest
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DATABASE_PATH"] = os.path.join(tempfile.gettempdir(), "dtu_test.db")

import database as db
from auth import hash_password, verify_password, create_token, decode_token
from services.analytics_service import tier_for, compute_funnel, compute_conversion_rate, progress_ratio
from services.ai_service import match_faq, answer_question, personalize_caption
from services.season_service import current_season, score_post, build_reason
from services.badge_service import compute_badges, max_streak


class TestAuthHelpers(unittest.TestCase):
    def test_password_hash_roundtrip(self):
        hashed = hash_password("MatKhauTest123")
        self.assertTrue(verify_password("MatKhauTest123", hashed))
        self.assertFalse(verify_password("SaiMatKhau", hashed))

    def test_password_hash_is_salted(self):
        h1 = hash_password("giong-nhau")
        h2 = hash_password("giong-nhau")
        self.assertNotEqual(h1, h2, "Hai lần băm cùng mật khẩu phải khác nhau nhờ salt ngẫu nhiên")

    def test_jwt_roundtrip(self):
        token = create_token({"sub": "GV001", "vai_tro": "giang_vien"})
        payload = decode_token(token)
        self.assertEqual(payload["sub"], "GV001")
        self.assertEqual(payload["vai_tro"], "giang_vien")

    def test_jwt_invalid_token_returns_none(self):
        self.assertIsNone(decode_token("token-khong-hop-le"))


class TestAnalyticsService(unittest.TestCase):
    def test_tier_thresholds(self):
        self.assertEqual(tier_for(20)["label"], "Kim Cương")
        self.assertEqual(tier_for(15)["label"], "Kim Cương")
        self.assertEqual(tier_for(14)["label"], "Vàng")
        self.assertEqual(tier_for(10)["label"], "Vàng")
        self.assertEqual(tier_for(9)["label"], "Bạc")
        self.assertEqual(tier_for(5)["label"], "Bạc")
        self.assertEqual(tier_for(4)["label"], "Đồng")
        self.assertEqual(tier_for(0)["label"], "Đồng")

    def test_progress_ratio(self):
        self.assertEqual(progress_ratio(5, 5), 1.0)
        self.assertEqual(progress_ratio(3, 5), 0.6)
        self.assertEqual(progress_ratio(10, 5), 1.0, "Không được vượt quá 100%")

    def test_funnel_monotonic_and_percentages(self):
        stages = compute_funnel([
            {"label": "Reach", "value": 1000},
            {"label": "Engaged", "value": 200},
            {"label": "Click", "value": 50},
        ])
        self.assertEqual(stages[0]["pct_of_top"], 100.0)
        self.assertEqual(stages[1]["pct_of_top"], 20.0)
        self.assertEqual(stages[1]["drop_from_prev_pct"], 80.0)
        self.assertEqual(stages[2]["drop_from_prev_pct"], 75.0)

    def test_funnel_empty_input(self):
        self.assertEqual(compute_funnel([]), [])

    def test_conversion_rate(self):
        self.assertEqual(compute_conversion_rate(100, 20), 20.0)
        self.assertEqual(compute_conversion_rate(0, 0), 0.0, "Tránh chia cho 0")


class TestAIServiceFAQMatching(unittest.TestCase):
    def setUp(self):
        self.faq_rows = [
            {"cau_hoi": "Học phí?", "cau_tra_loi": "Khoảng 27-32 triệu/năm.", "tu_khoa": "học phí, chi phí"},
            {"cau_hoi": "Ký túc xá?", "cau_tra_loi": "Có ký túc xá cho sinh viên xa nhà.", "tu_khoa": "ký túc xá, chỗ ở"},
        ]

    def test_match_faq_finds_relevant(self):
        matched = match_faq("Cho em hỏi học phí năm nay bao nhiêu ạ?", self.faq_rows)
        self.assertEqual(len(matched), 1)
        self.assertIn("học phí", matched[0]["tu_khoa"])

    def test_match_faq_no_match_returns_empty(self):
        matched = match_faq("Trường có đội bóng đá không?", self.faq_rows)
        self.assertEqual(matched, [])

    def test_answer_question_handoff_when_no_faq_match(self):
        result = answer_question("Câu hỏi hoàn toàn không liên quan gì cả", self.faq_rows)
        self.assertTrue(result["handoff"])

    def test_answer_question_rule_based_when_matched_and_no_ai_key(self):
        result = answer_question("Học phí bao nhiêu vậy?", self.faq_rows)
        self.assertFalse(result["handoff"])
        self.assertEqual(result["source"], "rule_based")


class TestDatabaseLayer(unittest.TestCase):
    def setUp(self):
        if os.path.exists(os.environ["DATABASE_PATH"]):
            os.remove(os.environ["DATABASE_PATH"])
        db.init_db()

    def test_insert_and_query_teacher(self):
        new_id = db.execute(
            "INSERT INTO giang_vien (ma_giang_vien, ho_ten, email, khoa, mat_khau_hash, vai_tro) VALUES (?, ?, ?, ?, ?, ?)",
            ("GVTEST", "Test User", "test@duytan.edu.vn", "Khoa Test", hash_password("x"), "giang_vien"),
        )
        row = db.query("SELECT * FROM giang_vien WHERE id = ?", (new_id,), fetchone=True)
        self.assertEqual(row["ho_ten"], "Test User")

    def test_foreign_key_relationship_share_log(self):
        teacher_id = db.execute(
            "INSERT INTO giang_vien (ma_giang_vien, ho_ten, email, khoa, mat_khau_hash, vai_tro) VALUES (?, ?, ?, ?, ?, ?)",
            ("GVFK", "FK Test", "fk@duytan.edu.vn", "Khoa Test", hash_password("x"), "giang_vien"),
        )
        db.execute(
            "INSERT INTO share_log (giang_vien_id, dot_truyen_thong, link_bai_dang) VALUES (?, ?, ?)",
            (teacher_id, "Đợt Test", "https://facebook.com/x"),
        )
        count_row = db.query("SELECT COUNT(*) AS c FROM share_log WHERE giang_vien_id = ?", (teacher_id,), fetchone=True)
        self.assertEqual(count_row["c"], 1)


class TestAPIEndpoints(unittest.TestCase):
    """Kiểm thử tích hợp qua Flask test_client — không cần chạy server thật."""

    @classmethod
    def setUpClass(cls):
        if os.path.exists(os.environ["DATABASE_PATH"]):
            os.remove(os.environ["DATABASE_PATH"])
        import app as app_module
        cls.app = app_module.create_app()
        cls.client = cls.app.test_client()
        db.execute(
            "INSERT INTO giang_vien (ma_giang_vien, ho_ten, email, khoa, mat_khau_hash, vai_tro) VALUES (?, ?, ?, ?, ?, ?)",
            ("GV001", "Giảng Viên Test", "gv@duytan.edu.vn", "Khoa CNTT", hash_password("Pass123!"), "giang_vien"),
        )
        db.execute(
            "INSERT INTO giang_vien (ma_giang_vien, ho_ten, email, khoa, mat_khau_hash, vai_tro) VALUES (?, ?, ?, ?, ?, ?)",
            ("QL001", "Quản Lý Test", "ql@duytan.edu.vn", "Phòng TT", hash_password("Pass123!"), "quan_ly"),
        )
        db.execute("INSERT INTO faq (cau_hoi, cau_tra_loi, tu_khoa) VALUES (?, ?, ?)",
                    ("Học phí?", "27-32 triệu/năm", "học phí"))

    def test_health_check(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)

    def test_login_success(self):
        resp = self.client.post("/api/auth/login", json={"email": "gv@duytan.edu.vn", "mat_khau": "Pass123!"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("token", resp.get_json())

    def test_login_wrong_password(self):
        resp = self.client.post("/api/auth/login", json={"email": "gv@duytan.edu.vn", "mat_khau": "sai"})
        self.assertEqual(resp.status_code, 401)

    def test_protected_route_without_token(self):
        resp = self.client.get("/api/teachers")
        self.assertEqual(resp.status_code, 401)

    def test_role_based_access_control(self):
        login_resp = self.client.post("/api/auth/login", json={"email": "gv@duytan.edu.vn", "mat_khau": "Pass123!"})
        token = login_resp.get_json()["token"]
        resp = self.client.get("/api/teachers", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 403, "Giảng viên không được phép xem toàn bộ danh sách giảng viên")

    def test_chatbot_public_endpoint_no_auth_required(self):
        resp = self.client.post("/api/chatbot/hoi", json={"cau_hoi": "Học phí bao nhiêu?"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("answer", resp.get_json())

    def test_chatbot_missing_question_returns_400(self):
        resp = self.client.post("/api/chatbot/hoi", json={})
        self.assertEqual(resp.status_code, 400)


class TestSeasonService(unittest.TestCase):
    """Kiểm thử logic AI đề xuất bài theo mùa vụ (rule-based, chạy offline)."""

    def test_current_season_by_month(self):
        from datetime import date
        self.assertEqual(current_season(date(2026, 7, 18))["key"], "cao_diem_xet_tuyen")
        self.assertEqual(current_season(date(2026, 5, 10))["key"], "mua_thi")
        self.assertEqual(current_season(date(2026, 9, 5))["key"], "nhap_hoc")
        self.assertEqual(current_season(date(2026, 12, 1))["key"], "gan_ket")
        self.assertEqual(current_season(date(2026, 2, 1))["key"], "huong_nghiep")

    def test_score_post_prefers_matching_season(self):
        from datetime import date
        today = date(2026, 7, 18)
        season = current_season(today)
        post_khop = {"giai_doan": "Mùa tuyển sinh", "ngay_dang_du_kien": "2026-07-18", "nganh": "CNTT"}
        post_lech = {"giai_doan": "Mùa thi", "ngay_dang_du_kien": "2026-07-18", "nganh": "CNTT"}
        self.assertGreater(
            score_post(post_khop, season, today=today),
            score_post(post_lech, season, today=today),
            "Bài đúng nhóm ưu tiên của mùa phải được điểm cao hơn",
        )

    def test_score_post_prefers_recent_date(self):
        from datetime import date
        today = date(2026, 7, 18)
        season = current_season(today)
        gan = {"giai_doan": "Mùa tuyển sinh", "ngay_dang_du_kien": "2026-07-18", "nganh": "CNTT"}
        xa = {"giai_doan": "Mùa tuyển sinh", "ngay_dang_du_kien": "2026-06-01", "nganh": "CNTT"}
        self.assertGreater(score_post(gan, season, today=today), score_post(xa, season, today=today))

    def test_score_post_bounded_0_100(self):
        from datetime import date
        today = date(2026, 7, 18)
        season = current_season(today)
        post = {"giai_doan": "Mùa tuyển sinh", "ngay_dang_du_kien": "2026-07-18", "nganh": "CNTT"}
        self.assertLessEqual(score_post(post, season, today=today, engagement_rate=99), 100)

    def test_build_reason_mentions_golden_hour(self):
        from datetime import date
        season = current_season(date(2026, 7, 18))
        post = {"giai_doan": "Mùa tuyển sinh", "ngay_dang_du_kien": "2026-07-18", "nganh": "CNTT"}
        reason = build_reason(post, season, 90, engagement_rate=7.2)
        self.assertIn(season["khung_gio_vang"], reason)


class TestPersonalizeCaption(unittest.TestCase):
    """Kiểm thử AI viết lại caption theo giọng văn — fallback rule-based khi không có API key."""

    def test_all_tones_produce_caption(self):
        for tone in ["than_thien", "chuyen_nghiep", "truyen_cam_hung"]:
            result = personalize_caption("Nội dung bài gốc.", "Giới thiệu ngành CNTT", "CNTT",
                                          "ThS. Nguyễn Văn A", "Khoa CNTT", tone)
            self.assertEqual(result["source"], "rule_based")
            self.assertIn("Nội dung bài gốc.", result["caption"])
            self.assertIn("#DaiHocDuyTan", result["caption"])

    def test_invalid_tone_falls_back_to_friendly(self):
        result = personalize_caption("Bài gốc.", "Chủ đề", "CNTT", "TS. B", "Khoa CNTT", "giong-la")
        self.assertTrue(len(result["caption"]) > 0)


class TestBadgeService(unittest.TestCase):
    """Kiểm thử logic huy hiệu thành tích (gamification)."""

    def test_max_streak(self):
        self.assertEqual(max_streak([]), 0)
        self.assertEqual(max_streak(["2026-07-01"]), 1)
        self.assertEqual(max_streak(["2026-07-01", "2026-07-02", "2026-07-03"]), 3)
        self.assertEqual(max_streak(["2026-07-01", "2026-07-03", "2026-07-04"]), 2)
        self.assertEqual(max_streak(["2026-07-01", "2026-07-01", "2026-07-02"]), 2, "Ngày trùng chỉ tính một lần")

    def test_badges_unlocked_states(self):
        badges = compute_badges(
            tong_luy_ke=13, so_bai_dot_nay=5, target=5, tong_click=120,
            ngay_chia_se=["2026-07-10", "2026-07-11", "2026-07-12"], so_nganh=4, hang=2,
        )
        by_key = {b["key"]: b for b in badges}
        self.assertEqual(len(badges), 6)
        self.assertTrue(all(by_key[k]["dat"] for k in
                            ["khoi_dong", "dat_chi_tieu", "chuoi_3_ngay", "nam_cham_click", "da_nganh", "top3"]))

    def test_badges_locked_with_progress(self):
        badges = compute_badges(
            tong_luy_ke=3, so_bai_dot_nay=3, target=5, tong_click=89,
            ngay_chia_se=["2026-07-10", "2026-07-12"], so_nganh=2, hang=7,
        )
        by_key = {b["key"]: b for b in badges}
        self.assertTrue(by_key["khoi_dong"]["dat"])
        self.assertFalse(by_key["dat_chi_tieu"]["dat"])
        self.assertEqual(by_key["dat_chi_tieu"]["tien_do"], "3/5")
        self.assertEqual(by_key["nam_cham_click"]["tien_do"], "89/100")
        self.assertFalse(by_key["top3"]["dat"])


class TestPortalAPIEndpoints(unittest.TestCase):
    """Kiểm thử các endpoint mới phục vụ Cổng chia sẻ giảng viên."""

    @classmethod
    def setUpClass(cls):
        if os.path.exists(os.environ["DATABASE_PATH"]):
            os.remove(os.environ["DATABASE_PATH"])
        import app as app_module
        cls.app = app_module.create_app()
        cls.client = cls.app.test_client()
        db.execute(
            "INSERT INTO giang_vien (ma_giang_vien, ho_ten, email, khoa, mat_khau_hash, vai_tro) VALUES (?, ?, ?, ?, ?, ?)",
            ("GV900", "GV Portal Test", "gvportal@duytan.edu.vn", "Khoa CNTT", hash_password("Pass123!"), "giang_vien"),
        )
        cls.content_id = db.execute(
            """INSERT INTO lich_noi_dung (ngay_dang_du_kien, giai_doan, chu_de, nganh, trang_thai, caption_cuoi, link_bai_dang)
               VALUES ('2026-07-18', 'Mùa tuyển sinh', 'Giới thiệu ngành CNTT', 'CNTT', 'da_dang', 'Caption test.', 'https://facebook.com/x')""",
        )
        login = cls.client.post("/api/auth/login", json={"email": "gvportal@duytan.edu.vn", "mat_khau": "Pass123!"})
        cls.token = login.get_json()["token"]
        cls.auth = {"Authorization": f"Bearer {cls.token}"}
        db.execute(
            "INSERT INTO giang_vien (ma_giang_vien, ho_ten, email, khoa, mat_khau_hash, vai_tro) VALUES (?, ?, ?, ?, ?, ?)",
            ("QL900", "QL Portal Test", "qlportal@duytan.edu.vn", "Phòng TT", hash_password("Pass123!"), "quan_ly"),
        )
        ql_login = cls.client.post("/api/auth/login", json={"email": "qlportal@duytan.edu.vn", "mat_khau": "Pass123!"})
        cls.ql_auth = {"Authorization": f"Bearer {ql_login.get_json()['token']}"}

    def test_seasonal_suggestions(self):
        resp = self.client.get("/api/content/goi-y-mua-vu", headers=self.auth)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("mua_vu", data)
        self.assertIn("khung_gio_vang", data["mua_vu"])
        self.assertGreaterEqual(len(data["goi_y"]), 1)
        goi_y = data["goi_y"][0]
        self.assertIn("diem_phu_hop", goi_y)
        self.assertIn("ly_do_goi_y", goi_y)
        # danh sách phải xếp theo điểm phù hợp giảm dần
        scores = [g["diem_phu_hop"] for g in data["goi_y"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_personalized_caption_endpoint(self):
        resp = self.client.post(f"/api/content/{self.content_id}/caption-ca-nhan",
                                 json={"giong_van": "chuyen_nghiep"}, headers=self.auth)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("Caption test.", data["caption"])

    def test_personalized_caption_not_found(self):
        resp = self.client.post("/api/content/99999/caption-ca-nhan", json={}, headers=self.auth)
        self.assertEqual(resp.status_code, 404)

    def test_leaderboard_marks_current_user(self):
        resp = self.client.get("/api/teachers/bang-xep-hang", headers=self.auth)
        self.assertEqual(resp.status_code, 200)
        board = resp.get_json()["bang_xep_hang"]
        self.assertTrue(any(item["la_toi"] for item in board))

    def test_my_stats_shape(self):
        resp = self.client.get("/api/teachers/toi/thong-ke", headers=self.auth)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        for field in ["so_bai_dot_nay", "target", "cap_bac", "hang", "lich_su", "hoat_dong_7_ngay", "huy_hieu"]:
            self.assertIn(field, data)
        self.assertEqual(len(data["huy_hieu"]), 6)
        for badge in data["huy_hieu"]:
            self.assertIn("dat", badge)
            self.assertIn("tien_do", badge)

    def test_funnel_what_if_simulation(self):
        resp = self.client.get("/api/funnel/mo-phong?so_giang_vien=50&so_bai=5", headers=self.ql_auth)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["du_bao"]["luot_chia_se"], 250)
        self.assertIn("click_trung_binh_moi_bai", data["gia_dinh"])
        # Nhiều giảng viên tham gia hơn thì dự báo không được giảm
        resp2 = self.client.get("/api/funnel/mo-phong?so_giang_vien=100&so_bai=5", headers=self.ql_auth)
        self.assertGreaterEqual(resp2.get_json()["du_bao"]["luot_click"], data["du_bao"]["luot_click"])

    def test_funnel_what_if_requires_manager_role(self):
        resp = self.client.get("/api/funnel/mo-phong", headers=self.auth)
        self.assertEqual(resp.status_code, 403)

    def test_funnel_what_if_invalid_params(self):
        resp = self.client.get("/api/funnel/mo-phong?so_giang_vien=abc", headers=self.ql_auth)
        self.assertEqual(resp.status_code, 400)

    def test_ai_month_plan_creates_items(self):
        resp = self.client.post("/api/content/ke-hoach-thang", json={"so_bai": 6}, headers=self.ql_auth)
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data["tao_moi"], 6)
        self.assertEqual(len(data["items"]), 6)
        # Các dòng phải thật sự nằm trong DB với trạng thái chờ soạn
        row = db.query("SELECT trang_thai FROM lich_noi_dung WHERE id = ?", (data["items"][0]["id"],), fetchone=True)
        self.assertEqual(row["trang_thai"], "cho_soan")

    def test_ab_captions_two_distinct_variants(self):
        resp = self.client.post(f"/api/content/{self.content_id}/ab-caption", json={}, headers=self.ql_auth)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("A", data)
        self.assertIn("B", data)
        self.assertNotEqual(data["A"]["caption"], data["B"]["caption"])

    def test_choose_caption_saves_winner(self):
        # Dùng bản ghi riêng để không ảnh hưởng các test khác dùng chung self.content_id
        cid = db.execute(
            """INSERT INTO lich_noi_dung (ngay_dang_du_kien, giai_doan, chu_de, nganh, trang_thai)
               VALUES ('2026-07-25', 'Mùa tuyển sinh', 'Bài test A/B', 'CNTT', 'cho_soan')""",
        )
        resp = self.client.post(f"/api/content/{cid}/chon-caption",
                                 json={"caption": "Caption thắng A/B.", "bien_the": "A"}, headers=self.ql_auth)
        self.assertEqual(resp.status_code, 200)
        row = db.query("SELECT caption_cuoi, trang_thai FROM lich_noi_dung WHERE id = ?", (cid,), fetchone=True)
        self.assertEqual(row["caption_cuoi"], "Caption thắng A/B.")
        self.assertEqual(row["trang_thai"], "cho_duyet")

    def test_multi_channel_captions(self):
        resp = self.client.post(f"/api/content/{self.content_id}/da-kenh", json={}, headers=self.auth)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["facebook"], "Caption test.", "Kênh Facebook giữ nguyên bản gốc")
        for channel in ["zalo", "tiktok"]:
            self.assertIn(channel, data)
            self.assertTrue(len(data[channel]) > 50, f"Biến thể {channel} phải là nội dung được soạn lại")

    def test_lead_capture_public_and_rbac_list(self):
        resp = self.client.post("/api/chatbot/lead",
                                 json={"ho_ten": "Thí sinh Test", "lien_he": "0900000000", "cau_hoi": "Hỏi thử?"})
        self.assertEqual(resp.status_code, 201)
        # Giảng viên không được xem danh sách lead
        resp2 = self.client.get("/api/chatbot/leads", headers=self.auth)
        self.assertEqual(resp2.status_code, 403)
        # Quản lý xem được và cập nhật được trạng thái
        resp3 = self.client.get("/api/chatbot/leads", headers=self.ql_auth)
        self.assertEqual(resp3.status_code, 200)
        lead = resp3.get_json()[0]
        resp4 = self.client.put(f"/api/chatbot/leads/{lead['id']}", json={"trang_thai": "da_goi"}, headers=self.ql_auth)
        self.assertEqual(resp4.status_code, 200)
        resp5 = self.client.put(f"/api/chatbot/leads/{lead['id']}", json={"trang_thai": "sai"}, headers=self.ql_auth)
        self.assertEqual(resp5.status_code, 400)

    def test_lead_capture_missing_fields(self):
        resp = self.client.post("/api/chatbot/lead", json={"ho_ten": "X"})
        self.assertEqual(resp.status_code, 400)

    def test_leaderboard_by_khoa(self):
        resp = self.client.get("/api/teachers/bang-xep-hang-khoa", headers=self.auth)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("bang_xep_hang", data)
        self.assertGreaterEqual(len(data["bang_xep_hang"]), 1)
        self.assertEqual(data["bang_xep_hang"][0]["hang"], 1)

    # ---------- Quản trị người dùng ----------
    def test_admin_list_requires_manager(self):
        self.assertEqual(self.client.get("/api/admin/users", headers=self.auth).status_code, 403)
        self.assertEqual(self.client.get("/api/admin/users", headers=self.ql_auth).status_code, 200)

    def test_admin_create_and_duplicate(self):
        payload = {"ma_giang_vien": "GVNEW1", "ho_ten": "GV Mới", "email": "gvnew1@duytan.edu.vn",
                   "khoa": "Khoa CNTT", "mat_khau": "Pass123!", "vai_tro": "giang_vien"}
        r1 = self.client.post("/api/admin/users", json=payload, headers=self.ql_auth)
        self.assertEqual(r1.status_code, 201)
        self.assertNotIn("mat_khau_hash", r1.get_json())
        # Trùng email/mã -> 409
        r2 = self.client.post("/api/admin/users", json=payload, headers=self.ql_auth)
        self.assertEqual(r2.status_code, 409)

    def test_admin_created_user_can_login(self):
        payload = {"ma_giang_vien": "GVNEW2", "ho_ten": "GV Login", "email": "gvnew2@duytan.edu.vn",
                   "khoa": "Khoa CNTT", "mat_khau": "Pass123!"}
        self.client.post("/api/admin/users", json=payload, headers=self.ql_auth)
        login = self.client.post("/api/auth/login", json={"email": "gvnew2@duytan.edu.vn", "mat_khau": "Pass123!"})
        self.assertEqual(login.status_code, 200)

    def test_admin_lock_blocks_login(self):
        self.client.post("/api/admin/users", json={
            "ma_giang_vien": "GVLOCK", "ho_ten": "GV Khoa", "email": "gvlock@duytan.edu.vn",
            "khoa": "Khoa CNTT", "mat_khau": "Pass123!"}, headers=self.ql_auth)
        uid = db.query("SELECT id FROM giang_vien WHERE email = 'gvlock@duytan.edu.vn'", fetchone=True)["id"]
        lock = self.client.post(f"/api/admin/users/{uid}/khoa", json={"kich_hoat": 0}, headers=self.ql_auth)
        self.assertEqual(lock.status_code, 200)
        login = self.client.post("/api/auth/login", json={"email": "gvlock@duytan.edu.vn", "mat_khau": "Pass123!"})
        self.assertEqual(login.status_code, 403, "Tài khoản bị khóa không được đăng nhập")

    def test_admin_reset_password(self):
        self.client.post("/api/admin/users", json={
            "ma_giang_vien": "GVRESET", "ho_ten": "GV Reset", "email": "gvreset@duytan.edu.vn",
            "khoa": "Khoa CNTT", "mat_khau": "Pass123!"}, headers=self.ql_auth)
        uid = db.query("SELECT id FROM giang_vien WHERE email = 'gvreset@duytan.edu.vn'", fetchone=True)["id"]
        r = self.client.post(f"/api/admin/users/{uid}/reset-mat-khau", json={"mat_khau": "MoiPass456!"}, headers=self.ql_auth)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["mat_khau_moi"], "MoiPass456!")
        login = self.client.post("/api/auth/login", json={"email": "gvreset@duytan.edu.vn", "mat_khau": "MoiPass456!"})
        self.assertEqual(login.status_code, 200)

    def test_admin_cannot_delete_or_lock_self(self):
        me = db.query("SELECT id FROM giang_vien WHERE email = 'qlportal@duytan.edu.vn'", fetchone=True)["id"]
        self.assertEqual(self.client.delete(f"/api/admin/users/{me}", headers=self.ql_auth).status_code, 400)
        self.assertEqual(self.client.post(f"/api/admin/users/{me}/khoa", json={"kich_hoat": 0}, headers=self.ql_auth).status_code, 400)

    def test_db_stats(self):
        r = self.client.get("/api/admin/thong-ke-db", headers=self.ql_auth)
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data["engine"], "SQLite")
        self.assertTrue(any(t["bang"] == "giang_vien" for t in data["tables"]))

    # ---------- Duyệt bài ----------
    def test_approve_publish_with_edited_caption(self):
        cid = db.execute(
            """INSERT INTO lich_noi_dung (ngay_dang_du_kien, giai_doan, chu_de, nganh, trang_thai, caption_cuoi)
               VALUES ('2026-07-28', 'Mùa tuyển sinh', 'Bài chờ duyệt', 'CNTT', 'cho_duyet', 'Bản nháp.')""")
        r = self.client.post(f"/api/content/{cid}/duyet-va-dang",
                             json={"caption_cuoi": "Bản đã duyệt cuối cùng."}, headers=self.ql_auth)
        self.assertEqual(r.status_code, 200)
        row = db.query("SELECT trang_thai, caption_cuoi FROM lich_noi_dung WHERE id = ?", (cid,), fetchone=True)
        self.assertEqual(row["trang_thai"], "da_dang")
        self.assertEqual(row["caption_cuoi"], "Bản đã duyệt cuối cùng.")

    def test_send_back_to_draft(self):
        cid = db.execute(
            """INSERT INTO lich_noi_dung (ngay_dang_du_kien, giai_doan, chu_de, nganh, trang_thai)
               VALUES ('2026-07-29', 'Mùa tuyển sinh', 'Bài trả lại', 'CNTT', 'cho_duyet')""")
        r = self.client.post(f"/api/content/{cid}/tra-lai", headers=self.ql_auth)
        self.assertEqual(r.status_code, 200)
        row = db.query("SELECT trang_thai FROM lich_noi_dung WHERE id = ?", (cid,), fetchone=True)
        self.assertEqual(row["trang_thai"], "cho_soan")


if __name__ == "__main__":
    unittest.main(verbosity=2)

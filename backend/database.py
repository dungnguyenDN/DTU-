"""
Lớp truy cập dữ liệu — dùng sqlite3 (thư viện chuẩn của Python, không cần cài thêm).
Thiết kế theo đúng 6 thực thể trong đề cương nghiên cứu:
LichNoiDung, GiangVien, ShareLog, KpiDashboard, FAQ, ChatLog
"""
import sqlite3
import os
from config import Config

SCHEMA = """
CREATE TABLE IF NOT EXISTS giang_vien (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ma_giang_vien TEXT UNIQUE NOT NULL,
    ho_ten TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    khoa TEXT NOT NULL,
    mat_khau_hash TEXT NOT NULL,
    vai_tro TEXT NOT NULL DEFAULT 'giang_vien',  -- giang_vien | quan_ly
    kich_hoat INTEGER NOT NULL DEFAULT 1,        -- 1 = hoạt động, 0 = đã khóa
    ngay_tao TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lich_noi_dung (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ngay_dang_du_kien TEXT NOT NULL,
    giai_doan TEXT NOT NULL,           -- Mùa thi | Mùa tuyển sinh | Mùa nhập học | Sự kiện thường niên
    chu_de TEXT NOT NULL,
    nganh TEXT NOT NULL,
    ghi_chu TEXT,
    trang_thai TEXT NOT NULL DEFAULT 'cho_soan',  -- cho_soan | cho_duyet | da_dang
    link_bai_dang TEXT,
    caption_cuoi TEXT,
    ngay_tao TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS share_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    giang_vien_id INTEGER NOT NULL,
    lich_noi_dung_id INTEGER,
    dot_truyen_thong TEXT NOT NULL,
    link_bai_dang TEXT,
    utm_link TEXT,
    luot_click INTEGER DEFAULT 0,
    thoi_gian TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (giang_vien_id) REFERENCES giang_vien(id),
    FOREIGN KEY (lich_noi_dung_id) REFERENCES lich_noi_dung(id)
);

CREATE TABLE IF NOT EXISTS kpi_dashboard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lich_noi_dung_id INTEGER,
    ngay TEXT NOT NULL,
    nganh TEXT,
    luot_xem INTEGER DEFAULT 0,
    luot_tuong_tac INTEGER DEFAULT 0,
    luot_click INTEGER DEFAULT 0,
    ty_le_tuong_tac REAL DEFAULT 0,
    FOREIGN KEY (lich_noi_dung_id) REFERENCES lich_noi_dung(id)
);

CREATE TABLE IF NOT EXISTS faq (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cau_hoi TEXT NOT NULL,
    cau_tra_loi TEXT NOT NULL,
    tu_khoa TEXT NOT NULL   -- phân cách bằng dấu phẩy
);

CREATE TABLE IF NOT EXISTS chat_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cau_hoi TEXT NOT NULL,
    cau_tra_loi TEXT,
    chuyen_tu_van_vien INTEGER DEFAULT 0,
    thoi_gian TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS benchmark_truong (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten_truong TEXT NOT NULL,
    tang_truong_follower REAL,
    ty_le_tuong_tac REAL,
    dinh_dang_chu_dao TEXT,
    la_truong_minh INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS lead_tu_van (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ho_ten TEXT NOT NULL,
    lien_he TEXT NOT NULL,              -- SĐT hoặc Zalo/email
    cau_hoi TEXT,                        -- câu hỏi khiến chatbot chuyển tư vấn viên
    trang_thai TEXT NOT NULL DEFAULT 'moi',  -- moi | da_goi | da_nop_ho_so
    thoi_gian TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS funnel_source (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nguon TEXT NOT NULL,          -- Fanpage | Giảng viên chia sẻ | Chatbot
    luot_click INTEGER DEFAULT 0,
    ho_so_nop INTEGER DEFAULT 0,
    thoi_gian TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def get_connection():
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    # Migration an toàn cho CSDL cũ đã tạo trước khi có cột kich_hoat.
    try:
        conn.execute("ALTER TABLE giang_vien ADD COLUMN kich_hoat INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError:
        pass  # cột đã tồn tại
    conn.commit()
    conn.close()


def query(sql, params=(), fetchone=False):
    conn = get_connection()
    try:
        cur = conn.execute(sql, params)
        rows = cur.fetchone() if fetchone else cur.fetchall()
        return rows
    finally:
        conn.close()


def execute(sql, params=()):
    conn = get_connection()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def row_to_dict(row):
    return dict(row) if row is not None else None


def rows_to_list(rows):
    return [dict(r) for r in rows]

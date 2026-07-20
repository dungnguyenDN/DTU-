import subprocess, time, json, sys, os, signal
import urllib.parse

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(BACKEND_DIR)

# reset db
subprocess.run(["python3", "seed_data.py"], check=True)

# start server
proc = subprocess.Popen(["python3", "app.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(2)

import urllib.request

def req(method, path, token=None, body=None):
    url = f"http://localhost:8000{path}"
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

try:
    print("== health ==")
    print(req("GET", "/api/health"))

    print("== login quan_ly ==")
    status, data = req("POST", "/api/auth/login", body={"email": "truyenthong@duytan.edu.vn", "mat_khau": "DemoPass123!"})
    print(status, data.get("user"))
    token_ql = data["token"]

    print("== login giang_vien ==")
    status, data = req("POST", "/api/auth/login", body={"email": "nguyenvana@duytan.edu.vn", "mat_khau": "DemoPass123!"})
    print(status, data.get("user"))
    token_gv = data["token"]

    print("== login sai mat khau (phai loi 401) ==")
    print(req("POST", "/api/auth/login", body={"email": "nguyenvana@duytan.edu.vn", "mat_khau": "sai"}))

    print("== KPI tong quan ==")
    print(req("GET", "/api/kpi/tong-quan", token=token_ql))

    print("== KPI theo nganh ==")
    print(req("GET", "/api/kpi/theo-nganh", token=token_ql))

    print("== Nhan dinh tuan ==")
    print(req("GET", "/api/kpi/nhan-dinh-tuan", token=token_ql))

    print("== Benchmark ==")
    print(req("GET", "/api/benchmark", token=token_ql))

    print("== Funnel ==")
    print(req("GET", "/api/funnel", token=token_ql))

    print("== Funnel theo nguon ==")
    print(req("GET", "/api/funnel/theo-nguon", token=token_ql))

    print("== Teachers list ==")
    status, data = req("GET", "/api/teachers", token=token_ql)
    print(status, len(data), "giang vien")
    print(data[0])

    print("== Teacher: quyen truy cap sai vai tro (giang vien khong duoc xem /api/teachers) ==")
    print(req("GET", "/api/teachers", token=token_gv))

    print("== My progress (giang vien) ==")
    dot_encoded = urllib.parse.quote("Đợt tuyển sinh 2026")
    print(req("GET", f"/api/teachers/toi/tien-do?dot_truyen_thong={dot_encoded}", token=token_gv))

    print("== Chia se bai (giang vien) ==")
    print(req("POST", "/api/teachers/chia-se", token=token_gv, body={
        "dot_truyen_thong": "Đợt tuyển sinh 2026",
        "link_bai_dang": "https://facebook.com/test-post-moi"
    }))

    print("== Goi y hom nay (cong khai qua token, dung cho portal) ==")
    print(req("GET", "/api/content/goi-y-hom-nay", token=token_gv))

    print("== Chatbot hoi (CONG KHAI - khong can token) ==")
    status, data = req("POST", "/api/chatbot/hoi", body={"cau_hoi": "Học phí ngành CNTT bao nhiêu vậy ạ?"})
    print(status, data)

    print("== Chatbot hoi cau khong co trong FAQ (phai handoff=True) ==")
    status, data = req("POST", "/api/chatbot/hoi", body={"cau_hoi": "Trường có tổ chức thi đấu bóng đá không?"})
    print(status, data)

    print("== Chu de noi bat ==")
    print(req("GET", "/api/chatbot/chu-de-noi-bat", token=token_ql))

    print("== Tao goi y tu chu de (vong phan hoi khep kin) ==")
    print(req("POST", "/api/chatbot/tao-goi-y-tu-chu-de", token=token_ql, body={"topic": "Học phí"}))

    print("== Kiem tra da them vao lich noi dung chua ==")
    print(req("GET", "/api/content?trang_thai=cho_soan", token=token_ql))

    print("\n✅ TẤT CẢ ENDPOINT ĐÃ TEST XONG")

finally:
    proc.send_signal(signal.SIGTERM)
    time.sleep(1)
    proc.kill()
    out, _ = proc.communicate(timeout=5)
    print("\n--- SERVER LOG (đuôi) ---")
    print(out[-2000:] if out else "(trống)")

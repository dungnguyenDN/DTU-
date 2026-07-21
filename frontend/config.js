/* ============================================================
   CẤU HÌNH KẾT NỐI BACKEND — sửa DUY NHẤT file này khi deploy.
   ------------------------------------------------------------
   - Chạy trên máy local (localhost / 127.0.0.1): tự gọi backend ở cổng 8000.
   - Khi deploy lên internet: điền URL backend thật (Render/Railway...) vào
     PRODUCTION_API_BASE bên dưới — TẤT CẢ các trang sẽ dùng chung.
   ============================================================ */
(function () {
  // 👉 SAU KHI DEPLOY BACKEND, đổi dòng dưới thành URL thật, ví dụ:
  //    "https://dtu-backend.onrender.com/api"
  var PRODUCTION_API_BASE = "https://dtu-backend.onrender.com/api";

  var isLocal = ["localhost", "127.0.0.1", ""].indexOf(location.hostname) !== -1;
  window.DTU_API_BASE = isLocal ? "http://localhost:8000/api" : PRODUCTION_API_BASE;
})();

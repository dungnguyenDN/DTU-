"""
Ứng dụng Flask chính — Nền tảng quản lý truyền thông tuyển sinh Đại học Duy Tân.
Chạy: python app.py  (mặc định cổng 8000)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify
from config import Config
import database as db

from routes import auth_routes, content_routes, teacher_routes, kpi_routes, chatbot_routes, benchmark_routes, funnel_routes, admin_routes


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_db()

    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(content_routes.bp)
    app.register_blueprint(teacher_routes.bp)
    app.register_blueprint(kpi_routes.bp)
    app.register_blueprint(chatbot_routes.bp)
    app.register_blueprint(benchmark_routes.bp)
    app.register_blueprint(funnel_routes.bp)
    app.register_blueprint(admin_routes.bp)

    # CORS thủ công (không phụ thuộc flask-cors) — cho phép frontend (platform/portal)
    # gọi API từ domain khác khi deploy tách rời (ví dụ frontend trên Netlify, backend trên Render).
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = Config.CORS_ALLOWED_ORIGINS
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "ok",
            "service": "dtu-marketing-platform-backend",
            "db": "postgres" if db.IS_POSTGRES else "sqlite",
        })

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Không tìm thấy endpoint"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Lỗi hệ thống nội bộ"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "0") == "1")

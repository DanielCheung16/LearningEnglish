from flask import Flask, send_from_directory
from flask_cors import CORS
import os

from backend.routes.word_routes import word_bp
from backend.routes.review_routes import review_bp
from backend.routes.config_routes import config_bp
from backend.modules.scheduler import get_scheduler


def create_app(data_dir: str = "backend/data"):
    """Create and configure the Flask application."""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(backend_dir)
    frontend_dir = os.path.join(project_root, "frontend")

    resolved_data_dir = data_dir
    if not os.path.isabs(resolved_data_dir):
        resolved_data_dir = os.path.join(project_root, resolved_data_dir)

    app = Flask(__name__, static_folder=frontend_dir, static_url_path="")
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    os.makedirs(resolved_data_dir, exist_ok=True)

    app.register_blueprint(word_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(config_bp)

    try:
        scheduler = get_scheduler(resolved_data_dir)
        if not scheduler.is_running:
            scheduler.start()
    except Exception as exc:
        print(f"Warning: scheduler failed to start: {exc}")

    @app.route("/")
    def index():
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/study")
    def study():
        return send_from_directory(frontend_dir, "study.html")

    @app.route("/review")
    def review():
        return send_from_directory(frontend_dir, "review.html")

    @app.route("/settings")
    def settings():
        return send_from_directory(frontend_dir, "settings.html")

    @app.route("/api/health", methods=["GET"])
    def health_check():
        return {
            "status": "ok",
            "message": "backend is running",
        }, 200

    @app.errorhandler(404)
    def not_found(_error):
        return {
            "success": False,
            "error": "requested resource was not found",
        }, 404

    @app.errorhandler(500)
    def internal_error(_error):
        return {
            "success": False,
            "error": "internal server error",
        }, 500

    def shutdown_scheduler():
        try:
            scheduler = get_scheduler(resolved_data_dir)
            if scheduler.is_running:
                scheduler.stop()
        except Exception:
            pass

    app.teardown_appcontext(lambda _exc: shutdown_scheduler())

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)

"""
app.py
Flask application factory.
Creates and configures the Flask app with all extensions and blueprints.
"""

import logging
import os
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail

from config import (
    get_config,
    MongoManager,
    ChromaManager,
    setup_logger,
)

# Extensions (instantiated here, bound to app in create_app)
jwt = JWTManager()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)


def create_app(config_name: str | None = None) -> Flask:
    """
    Application factory.

    Args:
        config_name: One of 'development', 'testing', 'production'.
                     Falls back to FLASK_ENV environment variable.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=False)

    # ── Load config ────────────────────────────────────────────
    cfg = get_config() if config_name is None else _resolve_config(config_name)

    # Fail loudly on startup if production secrets are missing or still placeholders —
    # better to crash here than silently run with a guessable SECRET_KEY.
    if hasattr(cfg, "validate"):
        cfg.validate()

    app.config.from_object(cfg)

    # ── Logging ────────────────────────────────────────────────
    setup_logger(app)

    # ── Create upload directories ──────────────────────────────
    _ensure_directories(app)

    # ── Extensions ────────────────────────────────────────────
    _init_extensions(app)

    # ── Database connections ───────────────────────────────────
    _init_databases(app)

    # ── Blueprints / Routes ────────────────────────────────────
    _register_blueprints(app)

    # ── Global error handlers ──────────────────────────────────
    _register_error_handlers(app)

    # ── Health check (no auth required) ───────────────────────
    _register_health_routes(app)

    logger.info("[START] %s started in %s mode", app.config["APP_NAME"], os.getenv("FLASK_ENV", "development"))
    return app


# ── Private helpers ────────────────────────────────────────────

def _resolve_config(name: str):
    from config.settings import config_by_name
    return config_by_name.get(name, config_by_name["default"])


def _ensure_directories(app: Flask) -> None:
    """Create upload and log directories if they don't exist."""
    base = Path(app.config["UPLOAD_FOLDER"])
    for subdir in app.config["UPLOAD_DIRS"].values():
        (base / subdir).mkdir(parents=True, exist_ok=True)

    log_file = Path(app.config.get("LOG_FILE", "./logs/app.log"))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Chroma persist dir
    Path(app.config["CHROMA_PERSIST_DIR"]).mkdir(parents=True, exist_ok=True)


def _init_extensions(app: Flask) -> None:
    """Bind Flask extensions to the app instance."""

    # CORS — allow frontend origin
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    # JWT
    jwt.init_app(app)
    _configure_jwt_callbacks(app)

    # Mail
    mail.init_app(app)

    # Rate limiter
    limiter.init_app(app)


def _configure_jwt_callbacks(app: Flask) -> None:
    """Register JWT error and loader callbacks."""

    @jwt.expired_token_loader
    def expired_token(_jwt_header, _jwt_data):
        return jsonify({"error": "Token has expired", "code": "TOKEN_EXPIRED"}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": f"Invalid token: {reason}", "code": "TOKEN_INVALID"}), 401

    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({"error": "Authorization token required", "code": "TOKEN_MISSING"}), 401

    @jwt.revoked_token_loader
    def revoked_token(_jwt_header, _jwt_data):
        return jsonify({"error": "Token has been revoked", "code": "TOKEN_REVOKED"}), 401


def _init_databases(app: Flask) -> None:
    """Initialise MongoDB and ChromaDB connections."""
    try:
        MongoManager.init_app(app)
    except Exception as exc:
        logger.warning("[WARNING] MongoDB init failed (non-fatal in dev): %s", exc)

    try:
        ChromaManager.init_app(app)
    except Exception as exc:
        logger.warning("[WARNING] ChromaDB init failed (non-fatal in dev): %s", exc)


def _register_blueprints(app: Flask) -> None:
    """Register all route blueprints."""
    from routes.auth_routes import auth_bp
    from routes.user_routes import user_bp
    from routes.document_routes import document_bp
    from routes.chat_routes import chat_bp
    from routes.analytics_routes import analytics_bp
    from routes.student_routes import student_bp
    from routes.faculty_routes import faculty_bp
    from routes.admin_routes import admin_bp
    from routes.notification_routes import notification_bp
    from routes.health_routes import health_bp
    from routes.excel_routes import excel_bp
    from routes.csv_routes import csv_bp
    from routes.mongo_query_routes import mongo_query_bp
    from routes.router_routes import router_bp
    from routes.resume_routes import resume_bp
    from routes.ml_routes import ml_bp
    from routes.ocr_routes import ocr_bp

    blueprints = [
        (auth_bp,         "/api/auth"),
        (user_bp,         "/api/users"),
        (document_bp,     "/api/documents"),
        (chat_bp,         "/api/chat"),
        (analytics_bp,    "/api/analytics"),
        (student_bp,      "/api/students"),
        (faculty_bp,      "/api/faculty"),
        (admin_bp,        "/api/admin"),
        (notification_bp, "/api/notifications"),
        (health_bp,       "/api"),
        (excel_bp,        "/api/excel"),
        (csv_bp,          "/api/csv"),
        (mongo_query_bp,  "/api/mongo-query"),
        (router_bp,       "/api/router"),
        (resume_bp,       "/api/resume"),
        (ml_bp,           "/api/ml"),
        (ocr_bp,          "/api/ocr"),
    ]

    for blueprint, url_prefix in blueprints:
        app.register_blueprint(blueprint, url_prefix=url_prefix)
        logger.debug("Registered blueprint: %s -> %s", blueprint.name, url_prefix)


def _register_error_handlers(app: Flask) -> None:
    """Register global HTTP error handlers."""

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request", "details": str(e)}), 400

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Forbidden — insufficient permissions"}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(413)
    def request_too_large(e):
        return jsonify({"error": "File too large. Maximum size is 50 MB"}), 413

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({"error": "Rate limit exceeded. Please slow down."}), 429

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Internal server error: %s", e)
        return jsonify({"error": "Internal server error"}), 500


def _register_health_routes(app: Flask) -> None:
    """Quick inline health check — no blueprint overhead."""

    @app.get("/")
    def root():
        return jsonify({
            "name": app.config["APP_NAME"],
            "version": "1.0.0",
            "status": "running",
        })


# ── Entry point ────────────────────────────────────────────────
if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=flask_app.config["DEBUG"],
    )

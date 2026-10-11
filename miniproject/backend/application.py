"""Application factory and cross-cutting Flask configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

from .blueprints import auth, elections, events, notifications, reports
from .common.errors import error
from .extensions import jwt, migrate
from .models import db

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent


def create_app(test_config=None):
    app = Flask(__name__, static_folder=str(ROOT / "ELECTICORE_frontend" / "static"), static_url_path="/static")
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///electicore.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=os.getenv("SECRET_KEY", "local-development-secret-must-be-replaced-123456"),
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "local-development-jwt-must-be-replaced-123456"),
        MAX_CONTENT_LENGTH=int(os.getenv("MAX_UPLOAD_BYTES", 15 * 1024 * 1024)),
        UPLOAD_DIR=str(Path(os.getenv("UPLOAD_DIR", str(ROOT / "backend" / "uploads")))),
    )
    if test_config:
        app.config.update(test_config)
    if os.getenv("APP_ENV") == "production" and (
        app.config["SECRET_KEY"].startswith("local-development-")
        or app.config["JWT_SECRET_KEY"].startswith("local-development-")
    ):
        raise RuntimeError("Set strong SECRET_KEY and JWT_SECRET_KEY values before deploying ELECTICORE.")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    _register_blueprints(app)
    _register_handlers(app)
    with app.app_context():
        Path(app.config["UPLOAD_DIR"]).mkdir(parents=True, exist_ok=True)
    return app


def _register_blueprints(app):
    for blueprint in (auth.bp, elections.bp, reports.bp, events.bp, notifications.bp):
        app.register_blueprint(blueprint)


def _register_handlers(app):
    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response

    @app.errorhandler(413)
    def file_too_large(_error):
        return error("File is too large. The maximum upload size is 15 MB.", 413)

    @app.get("/")
    def home():
        return send_from_directory(app.static_folder, "index.html")


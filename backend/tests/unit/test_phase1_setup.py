"""
tests/unit/test_phase1_setup.py
Phase 1 smoke tests — verify app factory, config, and health endpoint.
"""

import pytest
from app import create_app
from config.settings import DevelopmentConfig, TestingConfig, ProductionConfig


class TestAppFactory:
    """Tests for the Flask application factory."""

    def test_creates_app(self):
        app = create_app("testing")
        assert app is not None

    def test_testing_config(self):
        app = create_app("testing")
        assert app.config["TESTING"] is True
        assert app.config["DEBUG"] is True

    def test_development_config(self):
        app = create_app("development")
        assert app.config["DEBUG"] is True

    def test_upload_dirs_exist(self, tmp_path, monkeypatch):
        monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path / "uploads"))
        monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
        app = create_app("testing")
        assert app is not None


class TestConfig:
    """Tests for configuration classes."""

    def test_dev_config_debug(self):
        assert DevelopmentConfig.DEBUG is True

    def test_test_config_testing(self):
        assert TestingConfig.TESTING is True

    def test_prod_config_no_debug(self):
        assert ProductionConfig.DEBUG is False

    def test_jwt_secret_has_default(self):
        import os
        # Should not raise even without env var
        assert DevelopmentConfig.JWT_SECRET_KEY is not None

    def test_allowed_extensions(self):
        assert "pdf" in DevelopmentConfig.ALLOWED_EXTENSIONS
        assert "xlsx" in DevelopmentConfig.ALLOWED_EXTENSIONS
        assert "exe" not in DevelopmentConfig.ALLOWED_EXTENSIONS


class TestHealthEndpoints:
    """Tests for health check routes."""

    def test_ping(self, client):
        resp = client.get("/api/health/ping")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["message"] == "pong"

    def test_health_check_returns_json(self, client):
        resp = client.get("/api/health")
        assert resp.content_type == "application/json"

    def test_root_endpoint(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "name" in data
        assert data["status"] == "running"


class TestFileUtils:
    """Tests for file utility helpers."""

    def test_allowed_extensions(self):
        from services.file_utils import allowed_file
        assert allowed_file("report.pdf") is True
        assert allowed_file("data.xlsx") is True
        assert allowed_file("data.csv") is True
        assert allowed_file("photo.jpg") is True
        assert allowed_file("malware.exe") is False
        assert allowed_file("no_extension") is False

    def test_get_file_category(self):
        from services.file_utils import get_file_category
        assert get_file_category("report.pdf") == "pdf"
        assert get_file_category("data.xlsx") == "excel"
        assert get_file_category("data.csv") == "csv"
        assert get_file_category("photo.png") == "image"

    def test_generate_safe_filename(self):
        from services.file_utils import generate_safe_filename
        name = generate_safe_filename("my report (final).pdf")
        assert name.endswith(".pdf")
        assert " " not in name
        assert "(" not in name

    def test_human_readable_size(self):
        from services.file_utils import human_readable_size
        assert human_readable_size(1024) == "1.0 KB"
        assert human_readable_size(1024 * 1024) == "1.0 MB"
        assert human_readable_size(500) == "500.0 B"

    def test_validate_upload_no_file(self):
        from services.file_utils import validate_upload
        valid, msg = validate_upload(None)
        assert valid is False
        assert "No file" in msg


class TestResponseHelpers:
    """Tests for API response helper functions."""

    def test_success_response(self, app):
        with app.app_context():
            from models.response import success
            resp, code = success(data={"key": "val"}, message="OK")
            assert code == 200
            json_data = resp.get_json()
            assert json_data["success"] is True
            assert json_data["data"]["key"] == "val"

    def test_error_response(self, app):
        with app.app_context():
            from models.response import error
            resp, code = error("Something failed", status_code=400)
            assert code == 400
            json_data = resp.get_json()
            assert json_data["success"] is False
            assert "error" in json_data

    def test_not_found_response(self, app):
        with app.app_context():
            from models.response import not_found
            resp, code = not_found("Student")
            assert code == 404

    def test_paginated_response(self, app):
        with app.app_context():
            from models.response import paginated
            resp, code = paginated(
                items=[1, 2, 3], total=30, page=1, per_page=10
            )
            assert code == 200
            data = resp.get_json()
            assert data["pagination"]["total_pages"] == 3
            assert data["pagination"]["has_next"] is True
            assert data["pagination"]["has_prev"] is False

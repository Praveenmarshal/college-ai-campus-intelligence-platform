"""
tests/conftest.py
Pytest fixtures shared across all test suites.
"""

import pytest
from app import create_app
from config.database import MongoManager


@pytest.fixture(scope="session")
def app():
    """Create test Flask app."""
    flask_app = create_app("testing")
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
    })
    return flask_app


@pytest.fixture(scope="session")
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope="session")
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def auth_headers(client):
    """Return JWT auth headers for a test admin user."""
    resp = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "testpassword123",
    })
    if resp.status_code == 200:
        token = resp.get_json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture(autouse=True)
def clean_test_db(app):
    """Clean test collections before and after each test."""
    def _clean():
        try:
            db = MongoManager.get_db()
            for collection in ["users", "students", "chats", "audit_logs", "attendance", "placements", "results", "timetable", "library", "hostel", "events"]:
                db[collection].delete_many({})
        except Exception:
            pass
    _clean()
    yield
    _clean()

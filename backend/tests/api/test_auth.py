"""
tests/api/test_auth.py
Phase 2 — Authentication API integration tests.
Tests cover: register, login, token refresh, logout, me, change-password, RBAC.
"""

import pytest
import time


# ── Fixtures ───────────────────────────────────────────────
@pytest.fixture
def reg_data():
    return {
        "name":     "Test User",
        "email":    "testuser_phase2@campus.edu",
        "password": "testpass123",
        "role":     "student",
    }


@pytest.fixture
def admin_data():
    return {
        "name":     "Test Admin",
        "email":    "testadmin_phase2@campus.edu",
        "password": "adminpass123",
        "role":     "admin",
    }


def _register(client, data):
    return client.post("/api/auth/register", json=data)


def _login(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ── Register tests ─────────────────────────────────────────
class TestRegister:

    def test_register_success(self, client, reg_data):
        resp = _register(client, reg_data)
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert "access_token" in body["data"]
        assert "user" in body["data"]
        assert body["data"]["user"]["email"] == reg_data["email"]

    def test_register_missing_fields(self, client):
        resp = _register(client, {"email": "incomplete@test.com"})
        assert resp.status_code == 422
        body = resp.get_json()
        assert "name" in body.get("details", {})
        assert "password" in body.get("details", {})

    def test_register_invalid_email(self, client):
        resp = _register(client, {"name": "A", "email": "notanemail", "password": "pass1234"})
        assert resp.status_code == 422

    def test_register_weak_password(self, client):
        resp = _register(client, {"name": "A", "email": "x@x.com", "password": "short"})
        assert resp.status_code == 422
        body = resp.get_json()
        assert "password" in body.get("details", {})

    def test_register_duplicate_email(self, client, reg_data):
        _register(client, reg_data)
        resp = _register(client, reg_data)
        assert resp.status_code == 409

    def test_register_invalid_role(self, client):
        data = {"name": "X", "email": "x2@test.com", "password": "pass1234", "role": "superuser"}
        resp = _register(client, data)
        assert resp.status_code in (400, 422)

    def test_register_default_role_is_student(self, client):
        data = {"name": "No Role", "email": "norole@test.com", "password": "pass1234"}
        resp = _register(client, data)
        assert resp.status_code == 201
        assert resp.get_json()["data"]["user"]["role"] == "student"


# ── Login tests ────────────────────────────────────────────
class TestLogin:

    def test_login_success(self, client, reg_data):
        _register(client, reg_data)
        resp = _login(client, reg_data["email"], reg_data["password"])
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert "access_token" in body["data"]
        assert "refresh_token" in body["data"]

    def test_login_wrong_password(self, client, reg_data):
        _register(client, reg_data)
        resp = _login(client, reg_data["email"], "wrongpassword9")
        assert resp.status_code == 401

    def test_login_nonexistent_email(self, client):
        resp = _login(client, "nobody@nowhere.com", "anypassword9")
        assert resp.status_code == 401

    def test_login_missing_email(self, client):
        resp = client.post("/api/auth/login", json={"password": "pass1234"})
        assert resp.status_code == 422

    def test_login_missing_password(self, client):
        resp = client.post("/api/auth/login", json={"email": "x@x.com"})
        assert resp.status_code == 422

    def test_login_returns_user_data(self, client, reg_data):
        _register(client, reg_data)
        resp = _login(client, reg_data["email"], reg_data["password"])
        user = resp.get_json()["data"]["user"]
        assert user["name"] == reg_data["name"]
        assert "password_hash" not in user
        assert "id" in user


# ── Me / profile tests ─────────────────────────────────────
class TestMe:

    def test_me_returns_profile(self, client, reg_data):
        reg_resp = _register(client, reg_data)
        token = reg_resp.get_json()["data"]["access_token"]
        resp = client.get("/api/auth/me", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.get_json()["data"]["email"] == reg_data["email"]

    def test_me_requires_auth(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_bad_token(self, client):
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer badtoken"})
        assert resp.status_code == 401


# ── Logout tests ───────────────────────────────────────────
class TestLogout:

    def test_logout_success(self, client, reg_data):
        token = _register(client, reg_data).get_json()["data"]["access_token"]
        resp = client.post("/api/auth/logout", headers=_auth_header(token))
        assert resp.status_code == 200

    def test_logout_requires_auth(self, client):
        resp = client.post("/api/auth/logout")
        assert resp.status_code == 401


# ── Change password tests ──────────────────────────────────
class TestChangePassword:

    def test_change_password_success(self, client, reg_data):
        token = _register(client, reg_data).get_json()["data"]["access_token"]
        resp = client.put(
            "/api/auth/change-password",
            json={"current_password": reg_data["password"], "new_password": "newpass456"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200

    def test_change_password_wrong_current(self, client, reg_data):
        token = _register(client, reg_data).get_json()["data"]["access_token"]
        resp = client.put(
            "/api/auth/change-password",
            json={"current_password": "wrongcurrent9", "new_password": "newpass456"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 400

    def test_change_password_same_as_current(self, client, reg_data):
        token = _register(client, reg_data).get_json()["data"]["access_token"]
        resp = client.put(
            "/api/auth/change-password",
            json={"current_password": reg_data["password"], "new_password": reg_data["password"]},
            headers=_auth_header(token),
        )
        assert resp.status_code == 400

    def test_change_password_weak_new(self, client, reg_data):
        token = _register(client, reg_data).get_json()["data"]["access_token"]
        resp = client.put(
            "/api/auth/change-password",
            json={"current_password": reg_data["password"], "new_password": "weak"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 422


# ── RBAC tests ─────────────────────────────────────────────
class TestRBAC:

    def test_student_cannot_access_user_list(self, client, reg_data):
        token = _register(client, reg_data).get_json()["data"]["access_token"]
        resp = client.get("/api/users", headers=_auth_header(token))
        assert resp.status_code == 403

    def test_unauthenticated_cannot_access_protected(self, client):
        for endpoint in ["/api/users", "/api/admin/status"]:
            resp = client.get(endpoint)
            assert resp.status_code == 401


# ── Validator unit tests ───────────────────────────────────
class TestValidators:

    def test_register_schema_valid(self):
        from models.validators import RegisterSchema, validate_body
        schema = RegisterSchema()
        data, errs = validate_body(schema, {
            "name": "John Doe", "email": "john@test.com", "password": "securepass1"
        })
        assert not errs
        assert data["role"] == "student"

    def test_login_schema_strips_whitespace(self):
        from models.validators import LoginSchema, validate_body
        schema = LoginSchema()
        data, errs = validate_body(schema, {
            "email": "  user@test.com  ", "password": "pass1"
        })
        assert not errs
        assert data["email"] == "user@test.com"


# ── User model unit tests ──────────────────────────────────
class TestUserModel:

    def test_hash_and_verify_password(self):
        from models.user_model import UserModel
        hashed = UserModel.hash_password("mypassword9")
        assert hashed != "mypassword9"
        assert UserModel.verify_password("mypassword9", hashed)
        assert not UserModel.verify_password("wrongpass9", hashed)

    def test_invalid_role_raises(self, app):
        with app.app_context():
            from models.user_model import UserModel
            with pytest.raises(ValueError, match="Invalid role"):
                UserModel.create("X", "x@x.com", "pass1234", role="hacker")

    def test_serialise_removes_password_hash(self, app):
        with app.app_context():
            doc = {
                "_id": __import__("bson").ObjectId(),
                "name": "Test",
                "email": "t@t.com",
                "password_hash": "secret_hash",
                "role": "student",
                "is_active": True,
                "created_at": None,
                "updated_at": None,
                "last_login": None,
            }
            from models.user_model import UserModel
            result = UserModel._serialise(doc)
            assert "password_hash" not in result
            assert "id" in result
            assert "_id" not in result

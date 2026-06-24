"""
routes/auth_routes.py
Authentication endpoints — full Phase 2 implementation.
"""

import logging
import os

from flask import Blueprint, request, g
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, get_jwt, create_access_token
)

from models.user_model import UserModel
from models.validators import (
    RegisterSchema, LoginSchema, ChangePasswordSchema, validate_body
)
from models.response import success, created, error
from models.audit_model import AuditModel
from services.auth_service import AuthService, active_user_required

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)

_register_schema        = RegisterSchema()
_login_schema           = LoginSchema()
_change_password_schema = ChangePasswordSchema()


@auth_bp.post("/google")
def google_login():
    """Authenticate via Google OAuth Access Token."""
    import requests

    payload = request.get_json(silent=True) or {}
    credential = payload.get("credential", "")
    if not credential:
        return error("Google credential (access token) is required", 400)

    try:
        response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {credential}"},
            timeout=10,
        )
        if response.status_code != 200:
            logger.warning("Google userinfo API returned status code %s", response.status_code)
            return error("Invalid Google credential", 401)
        idinfo = response.json()
    except Exception as exc:
        logger.exception("Failed to connect to Google API: %s", exc)
        return error("Failed to verify Google credential", 500)

    email = idinfo.get("email", "")
    name = idinfo.get("name", "")
    picture = idinfo.get("picture", "")

    if not email:
        return error("Google account has no email", 400)

    user = UserModel.find_or_create_google_user(
        email=email, name=name, picture=picture
    )

    if not user.get("is_active"):
        return error("Account is inactive. Contact an administrator.", 403)

    tokens = AuthService.create_tokens(user)

    AuditModel.log(
        user_id=user["id"], action="google_login", resource="auth",
        ip_address=AuthService.get_ip(), user_agent=AuthService.get_ua(),
    )
    return success(tokens, "Google login successful")


@auth_bp.post("/register")
def register():
    data, errs = validate_body(_register_schema, request.get_json(silent=True) or {})
    if errs:
        return error("Validation failed", 422, errs)

    try:
        user = UserModel.create(
            name=data["name"],
            email=data["email"],
            password=data["password"],
            role=data.get("role", "student"),
            department=data.get("department", ""),
            phone=data.get("phone", ""),
        )
    except ValueError as exc:
        return error(str(exc), 409)

    AuditModel.log(
        user_id=user["id"], action="register", resource="users",
        resource_id=user["id"], ip_address=AuthService.get_ip(),
        user_agent=AuthService.get_ua(),
    )

    tokens = AuthService.create_tokens(user)
    return created(tokens, "Account created successfully")


@auth_bp.post("/login")
def login():
    data, errs = validate_body(_login_schema, request.get_json(silent=True) or {})
    if errs:
        return error("Validation failed", 422, errs)

    raw = UserModel.find_by_email(data["email"], include_password=True)
    if not raw:
        return error("Invalid email or password", 401)

    if not raw.get("is_active"):
        return error("Account is inactive. Contact an administrator.", 403)

    if not UserModel.verify_password(data["password"], raw.get("password_hash", "")):
        AuditModel.log(
            user_id=raw["id"], action="login_failed", resource="auth",
            status="failure", ip_address=AuthService.get_ip(),
            details={"reason": "wrong_password"},
        )
        return error("Invalid email or password", 401)

    user = UserModel.find_by_id(raw["id"])
    tokens = AuthService.create_tokens(user)

    AuditModel.log(
        user_id=user["id"], action="login", resource="auth",
        ip_address=AuthService.get_ip(), user_agent=AuthService.get_ua(),
    )
    return success(tokens, "Login successful")


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    claims = get_jwt()
    stored_jti = UserModel.get_refresh_jti(user_id)

    if stored_jti != claims.get("jti_ref"):
        return error("Refresh token has been revoked", 401)

    user = UserModel.find_by_id(user_id)
    if not user or not user.get("is_active"):
        return error("User not found or inactive", 401)

    access_token = create_access_token(
        identity=user_id,
        additional_claims={
            "role": user["role"],
            "name": user["name"],
            "email": user["email"],
            "jti_ref": claims.get("jti_ref"),
        },
    )
    return success({"access_token": access_token}, "Token refreshed")


@auth_bp.post("/logout")
@jwt_required()
def logout():
    user_id = get_jwt_identity()
    UserModel.revoke_refresh_token(user_id)
    AuditModel.log(
        user_id=user_id, action="logout", resource="auth",
        ip_address=AuthService.get_ip(), user_agent=AuthService.get_ua(),
    )
    return success(message="Logged out successfully")


@auth_bp.get("/me")
@jwt_required()
@active_user_required
def me():
    return success(g.current_user, "Profile fetched")


@auth_bp.put("/change-password")
@jwt_required()
@active_user_required
def change_password():
    data, errs = validate_body(_change_password_schema, request.get_json(silent=True) or {})
    if errs:
        return error("Validation failed", 422, errs)

    user_id = g.current_user["id"]
    raw = UserModel.find_by_email(g.current_user["email"], include_password=True)

    if not UserModel.verify_password(data["current_password"], raw.get("password_hash", "")):
        return error("Current password is incorrect", 400)

    if data["current_password"] == data["new_password"]:
        return error("New password must differ from the current password", 400)

    UserModel.change_password(user_id, data["new_password"])
    UserModel.revoke_refresh_token(user_id)

    AuditModel.log(
        user_id=user_id, action="change_password", resource="auth",
        ip_address=AuthService.get_ip(), user_agent=AuthService.get_ua(),
    )
    return success(message="Password changed. Please log in again.")


@auth_bp.post("/seed")
@auth_bp.post("/seed")
def seed_admin():
    """
    Create demo accounts.

    Allowed when EITHER:
      - FLASK_ENV=development (local dev — no extra auth needed), OR
      - the request includes header X-Seed-Secret matching the SEED_SECRET
        env var (lets you seed a production demo deployment exactly once
        without permanently relaxing the production gate — e.g. on Render,
        set SEED_SECRET to a random value, call this once, then optionally
        unset it).
    """
    is_dev = os.getenv("FLASK_ENV", "development") == "development"
    seed_secret = os.getenv("SEED_SECRET", "")
    provided_secret = request.headers.get("X-Seed-Secret", "")

    if not is_dev:
        if not seed_secret or provided_secret != seed_secret:
            return error(
                "Seeding requires development mode, or a matching X-Seed-Secret "
                "header if SEED_SECRET is configured.", 403
            )

    users_to_seed = [
        {"name": "Admin User",  "email": "admin@campus.edu",   "password": "admin123",   "role": "admin"},
        {"name": "Dr. Faculty", "email": "faculty@campus.edu", "password": "faculty123", "role": "faculty", "department": "Computer Science"},
        {"name": "Student One", "email": "student@campus.edu", "password": "student123", "role": "student", "department": "Computer Science"},
    ]

    created_list, skipped = [], []
    for u in users_to_seed:
        try:
            user = UserModel.create(**u)
            created_list.append(user["email"])
        except ValueError:
            skipped.append(u["email"])

    return success({
        "created": created_list,
        "skipped_existing": skipped,
        "credentials": [{"email": u["email"], "password": u["password"], "role": u["role"]} for u in users_to_seed],
    }, f"Seeded {len(created_list)} user(s)")

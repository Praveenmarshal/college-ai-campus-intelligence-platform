"""
services/auth_service.py
Authentication business logic.
Token generation, RBAC decorators, and session helpers.
"""

import logging
import uuid
from datetime import datetime, timezone
from functools import wraps
from typing import Optional

from flask import request, g
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    verify_jwt_in_request,
)

from models.user_model import UserModel
from models.audit_model import AuditModel
from models.response import error, forbidden

logger = logging.getLogger(__name__)


class AuthService:
    """Handles token creation, verification, and user session management."""

    # ── Token generation ────────────────────────────────────
    @staticmethod
    def create_tokens(user: dict) -> dict:
        """
        Generate a fresh access + refresh token pair for a user.
        Embeds role and name in the JWT claims for quick access.
        """
        user_id = user["id"]
        jti = str(uuid.uuid4())

        access_token = create_access_token(
            identity=user_id,
            additional_claims={
                "role": user["role"],
                "name": user["name"],
                "email": user["email"],
                "jti_ref": jti,      # links access token to its refresh counterpart
            },
        )
        refresh_token = create_refresh_token(
            identity=user_id,
            additional_claims={"jti_ref": jti},
        )

        # Persist JTI so we can revoke on logout
        UserModel.record_login(user_id, jti)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "user": user,
        }

    # ── Session helpers ─────────────────────────────────────
    @staticmethod
    def get_current_user() -> Optional[dict]:
        """Return the authenticated user's full profile from the DB."""
        try:
            user_id = get_jwt_identity()
            return UserModel.find_by_id(user_id)
        except Exception:
            return None

    @staticmethod
    def get_current_role() -> Optional[str]:
        """Extract the role claim directly from the JWT (no DB round-trip)."""
        try:
            claims = get_jwt()
            return claims.get("role")
        except Exception:
            return None

    # ── Request metadata ────────────────────────────────────
    @staticmethod
    def get_ip() -> str:
        return request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")

    @staticmethod
    def get_ua() -> str:
        return request.headers.get("User-Agent", "")


# ── RBAC decorators ────────────────────────────────────────

def roles_required(*roles):
    """
    Decorator: protect a route to specific roles.
    Usage:
        @roles_required("admin")
        @roles_required("admin", "faculty")
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                user_role = claims.get("role", "")
                if user_role not in roles:
                    AuditModel.log(
                        user_id=get_jwt_identity(),
                        action="access_denied",
                        resource=request.path,
                        status="failure",
                        ip_address=AuthService.get_ip(),
                    )
                    return forbidden(
                        f"Access denied. Required role(s): {', '.join(roles)}"
                    )
            except Exception as exc:
                return error(str(exc), 401)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    """Shorthand for @roles_required('admin')."""
    return roles_required("admin")(fn)


def faculty_or_admin_required(fn):
    """Shorthand for @roles_required('faculty', 'admin')."""
    return roles_required("faculty", "admin")(fn)


def active_user_required(fn):
    """
    Decorator: ensure the user account is still active.
    Use AFTER jwt_required so identity is already verified.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = UserModel.find_by_id(user_id)
        if not user or not user.get("is_active"):
            return error("Account is inactive. Please contact an administrator.", 403)
        g.current_user = user
        return fn(*args, **kwargs)
    return wrapper

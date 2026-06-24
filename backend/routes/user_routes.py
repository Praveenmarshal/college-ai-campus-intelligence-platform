"""
routes/user_routes.py — Phase 2 full implementation
"""
import logging
from flask import Blueprint, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.user_model import UserModel
from models.validators import UpdateProfileSchema, UpdateRoleSchema, validate_body
from models.response import success, error, not_found, paginated
from models.audit_model import AuditModel
from services.auth_service import AuthService, admin_required, active_user_required

logger = logging.getLogger(__name__)
user_bp = Blueprint("user", __name__)

_profile_schema = UpdateProfileSchema()
_role_schema    = UpdateRoleSchema()


@user_bp.get("")
@jwt_required()
@admin_required
def list_users():
    page     = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    role     = request.args.get("role")
    search   = request.args.get("search")
    users, total = UserModel.find_all(page=page, per_page=per_page, role=role, search=search)
    return paginated(users, total, page, per_page)


@user_bp.get("/stats")
@jwt_required()
@admin_required
def user_stats():
    counts = UserModel.count_by_role()
    return success({"total": sum(counts.values()), "by_role": counts})


@user_bp.get("/<string:user_id>")
@jwt_required()
@admin_required
def get_user(user_id):
    user = UserModel.find_by_id(user_id)
    return success(user) if user else not_found("User")


@user_bp.put("/profile")
@jwt_required()
@active_user_required
def update_profile():
    data, errs = validate_body(_profile_schema, request.get_json(silent=True) or {})
    if errs:
        return error("Validation failed", 422, errs)
    if not data:
        return error("No fields provided", 400)
    updated = UserModel.update(g.current_user["id"], data)
    if not updated:
        return not_found("User")
    AuditModel.log(user_id=g.current_user["id"], action="update_profile",
                   resource="users", ip_address=AuthService.get_ip())
    return success(updated, "Profile updated")


@user_bp.put("/<string:user_id>/role")
@jwt_required()
@admin_required
def update_role(user_id):
    data, errs = validate_body(_role_schema, request.get_json(silent=True) or {})
    if errs:
        return error("Validation failed", 422, errs)
    try:
        updated = UserModel.update_role(user_id, data["role"])
    except ValueError as exc:
        return error(str(exc), 400)
    if not updated:
        return not_found("User")
    AuditModel.log(user_id=get_jwt_identity(), action="update_role",
                   resource="users", resource_id=user_id,
                   details={"new_role": data["role"]}, ip_address=AuthService.get_ip())
    return success(updated, f"Role updated to '{data['role']}'")


@user_bp.put("/<string:user_id>/status")
@jwt_required()
@admin_required
def update_status(user_id):
    body = request.get_json(silent=True) or {}
    is_active = body.get("is_active")
    if not isinstance(is_active, bool):
        return error("'is_active' must be a boolean", 400)
    ok = UserModel.set_active(user_id, is_active)
    if not ok:
        return not_found("User")
    AuditModel.log(user_id=get_jwt_identity(),
                   action="activate_user" if is_active else "deactivate_user",
                   resource="users", resource_id=user_id, ip_address=AuthService.get_ip())
    return success(message=f"User {'activated' if is_active else 'deactivated'}")


@user_bp.delete("/<string:user_id>")
@jwt_required()
@admin_required
def delete_user(user_id):
    if user_id == get_jwt_identity():
        return error("Cannot delete your own account", 400)
    ok = UserModel.delete(user_id)
    if not ok:
        return not_found("User")
    AuditModel.log(user_id=get_jwt_identity(), action="delete_user",
                   resource="users", resource_id=user_id, ip_address=AuthService.get_ip())
    return success(message="User deleted")

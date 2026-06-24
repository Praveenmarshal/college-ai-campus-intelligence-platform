"""
routes/faculty_routes.py
Faculty CRUD endpoints.
"""
import logging
from flask import Blueprint, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.faculty_model import FacultyModel
from models.audit_model import AuditModel
from models.response import success, created, error, not_found, paginated
from services.auth_service import AuthService, admin_required, active_user_required

logger = logging.getLogger(__name__)
faculty_bp = Blueprint("faculty", __name__)


@faculty_bp.get("")
@jwt_required()
@active_user_required
def list_faculty():
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    department = request.args.get("department")
    search = request.args.get("search")
    items, total = FacultyModel.find_all(page, per_page, department, search)
    return paginated(items, total, page, per_page)


@faculty_bp.get("/me")
@jwt_required()
@active_user_required
def my_profile():
    f = FacultyModel.find_by_user_id(g.current_user["id"])
    if not f:
        return not_found("Faculty profile")
    return success(f)


@faculty_bp.get("/<string:faculty_id>")
@jwt_required()
@active_user_required
def get_faculty(faculty_id):
    f = FacultyModel.find_by_id(faculty_id)
    if not f:
        return not_found("Faculty")
    return success(f)


@faculty_bp.post("")
@jwt_required()
@admin_required
def create_faculty():
    body = request.get_json(silent=True) or {}
    required = ["faculty_id", "name", "email"]
    missing = [x for x in required if not body.get(x)]
    if missing:
        return error(f"Missing required fields: {missing}", 422)
    try:
        f = FacultyModel.create(**body)
    except ValueError as exc:
        return error(str(exc), 409)
    AuditModel.log(user_id=get_jwt_identity(), action="create_faculty", resource="faculty",
                   resource_id=f["id"], ip_address=AuthService.get_ip())
    return created(f, "Faculty created")


@faculty_bp.put("/<string:faculty_id>")
@jwt_required()
@admin_required
def update_faculty(faculty_id):
    body = request.get_json(silent=True) or {}
    updated = FacultyModel.update(faculty_id, body)
    if not updated:
        return not_found("Faculty")
    AuditModel.log(user_id=get_jwt_identity(), action="update_faculty", resource="faculty",
                   resource_id=faculty_id, ip_address=AuthService.get_ip())
    return success(updated, "Faculty updated")


@faculty_bp.delete("/<string:faculty_id>")
@jwt_required()
@admin_required
def delete_faculty(faculty_id):
    ok = FacultyModel.delete(faculty_id)
    if not ok:
        return not_found("Faculty")
    AuditModel.log(user_id=get_jwt_identity(), action="delete_faculty", resource="faculty",
                   resource_id=faculty_id, ip_address=AuthService.get_ip())
    return success(message="Faculty deleted")

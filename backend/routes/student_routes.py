"""
routes/student_routes.py
Student CRUD endpoints.
"""
import logging
from flask import Blueprint, request, g, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.student_model import StudentModel
from models.audit_model import AuditModel
from models.response import success, created, error, not_found, paginated
from services.auth_service import AuthService, admin_required, faculty_or_admin_required, active_user_required

logger = logging.getLogger(__name__)
student_bp = Blueprint("student", __name__)


@student_bp.get("")
@jwt_required()
@active_user_required
def list_students():
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    department = request.args.get("department")
    batch_year = request.args.get("batch_year", type=int)
    search = request.args.get("search")

    students, total = StudentModel.find_all(page, per_page, department, batch_year, search)
    return paginated(students, total, page, per_page)


@student_bp.get("/me")
@jwt_required()
@active_user_required
def my_profile():
    student = StudentModel.find_by_user_id(g.current_user["id"])
    if not student:
        return not_found("Student profile")
    return success(student)


@student_bp.get("/<string:student_id>")
@jwt_required()
@active_user_required
def get_student(student_id):
    student = StudentModel.find_by_id(student_id)
    if not student:
        return not_found("Student")
    return success(student)


@student_bp.post("")
@jwt_required()
@admin_required
def create_student():
    body = request.get_json(silent=True) or {}
    required = ["student_id", "name", "email"]
    missing = [f for f in required if not body.get(f)]
    if missing:
        return error(f"Missing required fields: {missing}", 422)

    try:
        student = StudentModel.create(**body)
    except ValueError as exc:
        return error(str(exc), 409)

    AuditModel.log(user_id=get_jwt_identity(), action="create_student", resource="students",
                   resource_id=student["id"], ip_address=AuthService.get_ip())
    return created(student, "Student created")


@student_bp.put("/<string:student_id>")
@jwt_required()
@faculty_or_admin_required
def update_student(student_id):
    body = request.get_json(silent=True) or {}
    updated = StudentModel.update(student_id, body)
    if not updated:
        return not_found("Student")
    AuditModel.log(user_id=get_jwt_identity(), action="update_student", resource="students",
                   resource_id=student_id, ip_address=AuthService.get_ip())
    return success(updated, "Student updated")


@student_bp.delete("/<string:student_id>")
@jwt_required()
@admin_required
def delete_student(student_id):
    ok = StudentModel.delete(student_id)
    if not ok:
        return not_found("Student")
    AuditModel.log(user_id=get_jwt_identity(), action="delete_student", resource="students",
                   resource_id=student_id, ip_address=AuthService.get_ip())
    return success(message="Student deleted")


@student_bp.post("/bulk-upload")
@jwt_required()
@admin_required
def bulk_upload_students():
    """Bulk-create students from an uploaded Excel/CSV file."""
    if "file" not in request.files:
        return error("No file part in request", 400)

    file = request.files["file"]
    from services.file_utils import validate_upload, generate_safe_filename, get_upload_path, get_file_category
    valid, msg = validate_upload(file)
    if not valid:
        return error(msg, 400)

    category = get_file_category(file.filename)
    safe_name = generate_safe_filename(file.filename)
    dest_path = get_upload_path(current_app.config["UPLOAD_FOLDER"], category, safe_name)
    file.save(str(dest_path))

    try:
        if category == "excel":
            from services.excel.excel_processor import ExcelProcessor
            sheets = ExcelProcessor.load_workbook(dest_path)
            df = list(sheets.values())[0]
        elif category == "csv":
            from services.csv_engine.csv_processor import CSVProcessor
            df = CSVProcessor.load_csv(dest_path)
        else:
            return error("Bulk upload supports Excel or CSV only", 400)

        records = df.fillna("").to_dict("records")
        result = StudentModel.bulk_create(records)

        AuditModel.log(user_id=get_jwt_identity(), action="bulk_upload_students", resource="students",
                       ip_address=AuthService.get_ip(), details=result)

        return created(result, f"Bulk upload complete — {result['created']} created, {result['skipped']} skipped")
    except Exception as exc:
        logger.exception("Bulk student upload failed")
        return error(f"Bulk upload failed: {exc}", 500)

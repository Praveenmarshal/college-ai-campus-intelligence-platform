"""
routes/resume_routes.py
Phase 9 — Resume upload and analysis endpoints.
"""

import logging

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.document_model import DocumentModel
from models.audit_model import AuditModel
from models.response import success, created, error, not_found
from services.auth_service import AuthService, active_user_required
from services.file_utils import validate_upload, generate_safe_filename, get_upload_path, get_file_category
from services.resume.resume_analyzer import ResumeAnalyzer

logger = logging.getLogger(__name__)
resume_bp = Blueprint("resume", __name__)


@resume_bp.post("/analyze")
@jwt_required()
@active_user_required
def analyze_resume():
    """Upload a resume PDF and get ATS score + skill gap analysis."""
    if "file" not in request.files:
        return error("No file part in request", 400)

    file = request.files["file"]
    valid, msg = validate_upload(file)
    if not valid:
        return error(msg, 400)

    if get_file_category(file.filename) != "pdf":
        return error("Resumes must be uploaded as PDF files", 400)

    target_role = request.form.get("target_role", "")

    safe_name = generate_safe_filename(file.filename)
    dest_path = get_upload_path(current_app.config["UPLOAD_FOLDER"], "resume", safe_name)
    file.save(str(dest_path))
    file_size = dest_path.stat().st_size

    user_id = get_jwt_identity()
    doc = DocumentModel.create(
        filename=safe_name, original_name=file.filename, file_path=str(dest_path),
        file_type="resume", file_size=file_size, mime_type=file.mimetype or "application/pdf",
        uploaded_by=user_id, description=f"Resume analysis (target role: {target_role or 'general'})",
    )

    try:
        analysis = ResumeAnalyzer.process_resume(dest_path, resume_id=doc["id"], target_role=target_role or None)
        DocumentModel.mark_processed(doc["id"], chunk_count=0, page_count=1)

        AuditModel.log(
            user_id=user_id, action="resume_analysis", resource="documents",
            resource_id=doc["id"], ip_address=AuthService.get_ip(),
            details={"ats_score": analysis.get("ats_score")},
        )

        return created({
            "resume_id": doc["id"],
            "filename": file.filename,
            "analysis": analysis,
        }, "Resume analyzed successfully")

    except ValueError as exc:
        DocumentModel.mark_failed(doc["id"], str(exc))
        return error(str(exc), 422)
    except Exception as exc:
        logger.exception("Resume analysis failed")
        DocumentModel.mark_failed(doc["id"], str(exc))
        return error(f"Analysis failed: {exc}", 500)


@resume_bp.get("/<string:resume_id>")
@jwt_required()
@active_user_required
def get_resume_analysis(resume_id):
    """Retrieve a cached resume analysis."""
    analysis = ResumeAnalyzer.get_cached_analysis(resume_id)
    if not analysis:
        return not_found("Resume analysis")
    doc = DocumentModel.find_by_id(resume_id)
    return success({"resume_id": resume_id, "document": doc, "analysis": analysis})

"""
routes/csv_routes.py
Phase 5 — CSV upload, profiling, and natural language query endpoints.
"""

import logging
from pathlib import Path

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.document_model import DocumentModel
from models.audit_model import AuditModel
from models.response import success, created, error, not_found, paginated
from services.auth_service import AuthService, admin_required, active_user_required
from services.file_utils import validate_upload, generate_safe_filename, get_upload_path, get_file_category, human_readable_size
from services.csv_engine.csv_processor import CSVProcessor
from services.excel.nl_query import NLQueryEngine

logger = logging.getLogger(__name__)
csv_bp = Blueprint("csv", __name__)

_csv_cache: dict[str, "object"] = {}


@csv_bp.post("/upload")
@jwt_required()
@admin_required
def upload_csv():
    if "file" not in request.files:
        return error("No file part in request", 400)

    file = request.files["file"]
    valid, msg = validate_upload(file)
    if not valid:
        return error(msg, 400)

    if get_file_category(file.filename) != "csv":
        return error("Only CSV files are allowed", 400)

    description = request.form.get("description", "")
    safe_name = generate_safe_filename(file.filename)
    dest_path = get_upload_path(current_app.config["UPLOAD_FOLDER"], "csv", safe_name)
    file.save(str(dest_path))
    file_size = dest_path.stat().st_size

    user_id = get_jwt_identity()
    doc = DocumentModel.create(
        filename=safe_name, original_name=file.filename, file_path=str(dest_path),
        file_type="csv", file_size=file_size, mime_type=file.mimetype or "text/csv",
        uploaded_by=user_id, description=description,
    )

    try:
        result = CSVProcessor.process_file(dest_path)
        df = CSVProcessor.load_csv(dest_path)
        _csv_cache[doc["id"]] = df

        DocumentModel.mark_processed(doc["id"], chunk_count=0, page_count=1)

        AuditModel.log(
            user_id=user_id, action="upload_csv", resource="documents",
            resource_id=doc["id"], ip_address=AuthService.get_ip(),
            details={"rows": result["profile"]["row_count"]},
        )

        return created({
            "document": doc,
            "result": result,
            "file_size_readable": human_readable_size(file_size),
        }, f"CSV processed — {result['profile']['row_count']} rows analysed")

    except Exception as exc:
        logger.exception("CSV processing failed for %s", file.filename)
        DocumentModel.mark_failed(doc["id"], str(exc))
        return error(f"File uploaded but analysis failed: {exc}", 500)


@csv_bp.get("")
@jwt_required()
@active_user_required
def list_csv_files():
    page     = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    docs, total = DocumentModel.find_all(page=page, per_page=per_page, file_type="csv")
    return paginated(docs, total, page, per_page)


@csv_bp.get("/<string:doc_id>")
@jwt_required()
@active_user_required
def get_csv_analysis(doc_id):
    doc = DocumentModel.find_by_id(doc_id)
    if not doc or doc["file_type"] != "csv":
        return not_found("CSV document")

    file_path = Path(doc["file_path"])
    if not file_path.exists():
        return error("Original file no longer exists on disk", 404)

    try:
        result = CSVProcessor.process_file(file_path)
        return success({"document": doc, "result": result})
    except Exception as exc:
        return error(f"Failed to load analysis: {exc}", 500)


@csv_bp.post("/<string:doc_id>/query")
@jwt_required()
@active_user_required
def query_csv(doc_id):
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    if not question:
        return error("Question cannot be empty", 400)

    doc = DocumentModel.find_by_id(doc_id)
    if not doc or doc["file_type"] != "csv":
        return not_found("CSV document")

    df = _csv_cache.get(doc_id)
    if df is None:
        file_path = Path(doc["file_path"])
        if not file_path.exists():
            return error("Original file no longer exists on disk", 404)
        df = CSVProcessor.load_csv(file_path)
        _csv_cache[doc_id] = df

    try:
        result = NLQueryEngine.query(question, df)
        AuditModel.log(
            user_id=get_jwt_identity(), action="csv_nl_query", resource="documents",
            resource_id=doc_id, ip_address=AuthService.get_ip(),
            details={"question": question[:200]},
        )
        return success(result, "Query executed")
    except (ValueError, RuntimeError) as exc:
        return error(str(exc), 422)

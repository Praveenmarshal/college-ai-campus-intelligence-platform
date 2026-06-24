"""
routes/excel_routes.py
Phase 4 — Excel upload, processing, and natural language query endpoints.

Endpoints:
  POST /api/excel/upload         — upload + analyse an Excel workbook
  GET  /api/excel/:id            — get stored analysis result
  POST /api/excel/:id/query      — ask a natural language question about the data
  GET  /api/excel                — list uploaded Excel files
"""

import logging
from pathlib import Path

from flask import Blueprint, request, g, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.document_model import DocumentModel
from models.audit_model import AuditModel
from models.response import success, created, error, not_found, paginated
from services.auth_service import AuthService, admin_required, active_user_required
from services.file_utils import validate_upload, generate_safe_filename, get_upload_path, get_file_category, human_readable_size
from services.excel.excel_processor import ExcelProcessor
from services.excel.nl_query import NLQueryEngine

logger = logging.getLogger(__name__)
excel_bp = Blueprint("excel", __name__)

# In-memory cache of loaded DataFrames keyed by document id (per-process)
# In production this would use Redis; fine for the platform's scale.
_dataframe_cache: dict[str, dict] = {}


@excel_bp.post("/upload")
@jwt_required()
@admin_required
def upload_excel():
    if "file" not in request.files:
        return error("No file part in request", 400)

    file = request.files["file"]
    valid, msg = validate_upload(file)
    if not valid:
        return error(msg, 400)

    if get_file_category(file.filename) != "excel":
        return error("Only Excel files (.xlsx, .xls) are allowed", 400)

    description = request.form.get("description", "")
    safe_name = generate_safe_filename(file.filename)
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    dest_path = get_upload_path(upload_folder, "excel", safe_name)
    file.save(str(dest_path))
    file_size = dest_path.stat().st_size

    user_id = get_jwt_identity()
    doc = DocumentModel.create(
        filename=safe_name, original_name=file.filename, file_path=str(dest_path),
        file_type="excel", file_size=file_size, mime_type=file.mimetype or "",
        uploaded_by=user_id, description=description,
    )

    try:
        analysis = ExcelProcessor.process_file(dest_path)
        sheet_count = len(analysis)

        # Cache raw dataframes for NL querying
        sheets = ExcelProcessor.load_workbook(dest_path)
        _dataframe_cache[doc["id"]] = sheets

        # Save contents to MongoDB collections
        db_save_stats = ExcelProcessor.save_to_mongodb(sheets)
        logger.info("Saved Excel sheets to MongoDB: %s", db_save_stats)

        DocumentModel.mark_processed(doc["id"], chunk_count=0, page_count=sheet_count)

        AuditModel.log(
            user_id=user_id, action="upload_excel", resource="documents",
            resource_id=doc["id"], ip_address=AuthService.get_ip(),
            details={"sheets": sheet_count},
        )

        return created({
            "document": doc,
            "analysis": analysis,
            "sheet_count": sheet_count,
            "file_size_readable": human_readable_size(file_size),
        }, f"Excel file processed — {sheet_count} sheet(s) analysed")

    except Exception as exc:
        logger.exception("Excel processing failed for %s", file.filename)
        DocumentModel.mark_failed(doc["id"], str(exc))
        return error(f"File uploaded but analysis failed: {exc}", 500)


@excel_bp.get("")
@jwt_required()
@active_user_required
def list_excel_files():
    page     = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    docs, total = DocumentModel.find_all(page=page, per_page=per_page, file_type="excel")
    return paginated(docs, total, page, per_page)


@excel_bp.get("/<string:doc_id>")
@jwt_required()
@active_user_required
def get_excel_analysis(doc_id):
    doc = DocumentModel.find_by_id(doc_id)
    if not doc or doc["file_type"] != "excel":
        return not_found("Excel document")

    file_path = Path(doc["file_path"])
    if not file_path.exists():
        return error("Original file no longer exists on disk", 404)

    try:
        analysis = ExcelProcessor.process_file(file_path)
        return success({"document": doc, "analysis": analysis})
    except Exception as exc:
        return error(f"Failed to load analysis: {exc}", 500)


@excel_bp.post("/<string:doc_id>/query")
@jwt_required()
@active_user_required
def query_excel(doc_id):
    """
    Ask a natural language question about an uploaded Excel file.
    Body: { question: str, sheet_name?: str }
    """
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    sheet_name = body.get("sheet_name")

    if not question:
        return error("Question cannot be empty", 400)

    doc = DocumentModel.find_by_id(doc_id)
    if not doc or doc["file_type"] != "excel":
        return not_found("Excel document")

    # Load from cache or disk
    sheets = _dataframe_cache.get(doc_id)
    if sheets is None:
        file_path = Path(doc["file_path"])
        if not file_path.exists():
            return error("Original file no longer exists on disk", 404)
        sheets = ExcelProcessor.load_workbook(file_path)
        _dataframe_cache[doc_id] = sheets

    if not sheet_name:
        sheet_name = list(sheets.keys())[0]
    if sheet_name not in sheets:
        return error(f"Sheet '{sheet_name}' not found. Available: {list(sheets.keys())}", 400)

    df = sheets[sheet_name]

    try:
        result = NLQueryEngine.query(question, df)
        AuditModel.log(
            user_id=get_jwt_identity(), action="excel_nl_query", resource="documents",
            resource_id=doc_id, ip_address=AuthService.get_ip(),
            details={"question": question[:200]},
        )
        return success(result, "Query executed")
    except (ValueError, RuntimeError) as exc:
        return error(str(exc), 422)

"""
routes/ocr_routes.py
Phase 12 — OCR and question paper analysis endpoints.

Endpoints:
  POST /api/ocr/extract                — extract text from an image or scanned PDF
  POST /api/ocr/question-paper/analyze — analyze a single question paper
  POST /api/ocr/question-paper/trends  — frequency analysis across multiple papers
"""

import logging

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.document_model import DocumentModel
from models.audit_model import AuditModel
from models.response import success, created, error
from services.auth_service import AuthService, active_user_required, admin_required
from services.file_utils import validate_upload, generate_safe_filename, get_upload_path, get_file_category
from services.ocr.ocr_processor import OCRProcessor
from services.ocr.question_paper_analyzer import QuestionPaperAnalyzer

logger = logging.getLogger(__name__)
ocr_bp = Blueprint("ocr", __name__)


@ocr_bp.post("/extract")
@jwt_required()
@active_user_required
def extract_text():
    """Extract text from an uploaded image or scanned PDF via OCR."""
    if "file" not in request.files:
        return error("No file part in request", 400)

    file = request.files["file"]
    valid, msg = validate_upload(file)
    if not valid:
        return error(msg, 400)

    category = get_file_category(file.filename)
    if category not in ("image", "pdf"):
        return error("Only image or PDF files are supported for OCR", 400)

    safe_name = generate_safe_filename(file.filename)
    dest_path = get_upload_path(current_app.config["UPLOAD_FOLDER"], "image" if category == "image" else "pdf", safe_name)
    file.save(str(dest_path))

    try:
        if category == "image":
            result = OCRProcessor.extract_text(dest_path)
        else:
            result = OCRProcessor.extract_from_scanned_pdf(dest_path)

        AuditModel.log(
            user_id=get_jwt_identity(), action="ocr_extract", resource="ocr",
            ip_address=AuthService.get_ip(), details={"filename": file.filename, "engine": result.get("engine")},
        )

        return success(result, "Text extracted successfully")
    except Exception as exc:
        logger.exception("OCR extraction failed")
        return error(f"OCR extraction failed: {exc}", 500)


@ocr_bp.post("/question-paper/analyze")
@jwt_required()
@active_user_required
def analyze_question_paper():
    """Upload and analyze a single question paper (topics, difficulty, question types)."""
    if "file" not in request.files:
        return error("No file part in request", 400)

    file = request.files["file"]
    valid, msg = validate_upload(file)
    if not valid:
        return error(msg, 400)

    category = get_file_category(file.filename)
    if category not in ("image", "pdf"):
        return error("Only image or PDF files are supported", 400)

    safe_name = generate_safe_filename(file.filename)
    dest_path = get_upload_path(current_app.config["UPLOAD_FOLDER"], "image" if category == "image" else "pdf", safe_name)
    file.save(str(dest_path))
    file_size = dest_path.stat().st_size

    user_id = get_jwt_identity()
    doc = DocumentModel.create(
        filename=safe_name, original_name=file.filename, file_path=str(dest_path),
        file_type=category, file_size=file_size, mime_type=file.mimetype or "",
        uploaded_by=user_id, description="Question paper analysis",
    )

    try:
        result = QuestionPaperAnalyzer.process_paper(dest_path)
        DocumentModel.mark_processed(doc["id"], chunk_count=0, page_count=1)

        AuditModel.log(
            user_id=user_id, action="question_paper_analysis", resource="documents",
            resource_id=doc["id"], ip_address=AuthService.get_ip(),
        )

        return created({"document_id": doc["id"], "filename": file.filename, "analysis": result},
                       "Question paper analyzed")
    except ValueError as exc:
        DocumentModel.mark_failed(doc["id"], str(exc))
        return error(str(exc), 422)
    except Exception as exc:
        logger.exception("Question paper analysis failed")
        DocumentModel.mark_failed(doc["id"], str(exc))
        return error(f"Analysis failed: {exc}", 500)


@ocr_bp.post("/question-paper/trends")
@jwt_required()
@admin_required
def analyze_trends():
    """
    Upload multiple question papers (e.g. last 5 years) and get frequency/trend analysis.
    Accepts multiple files under the 'files' key.
    """
    files = request.files.getlist("files")
    if not files:
        return error("No files provided. Upload multiple question papers under 'files'.", 400)
    if len(files) > 10:
        return error("Maximum 10 files per trend analysis", 400)

    papers_topics = []
    processed_files = []

    for file in files:
        valid, msg = validate_upload(file)
        if not valid:
            continue

        category = get_file_category(file.filename)
        if category not in ("image", "pdf"):
            continue

        safe_name = generate_safe_filename(file.filename)
        dest_path = get_upload_path(
            current_app.config["UPLOAD_FOLDER"], "image" if category == "image" else "pdf", safe_name
        )
        file.save(str(dest_path))

        try:
            result = QuestionPaperAnalyzer.process_paper(dest_path)
            papers_topics.append(result.get("topics", []))
            processed_files.append({"filename": file.filename, "topics_found": len(result.get("topics", []))})
        except Exception as exc:
            logger.warning("Skipping %s in trend analysis: %s", file.filename, exc)
            continue

    if not papers_topics:
        return error("Could not process any of the uploaded files", 422)

    trends = QuestionPaperAnalyzer.analyze_frequency(papers_topics)
    trends["processed_files"] = processed_files

    AuditModel.log(
        user_id=get_jwt_identity(), action="question_paper_trends", resource="ocr",
        ip_address=AuthService.get_ip(), details={"file_count": len(processed_files)},
    )

    return success(trends, f"Trend analysis complete across {len(processed_files)} paper(s)")

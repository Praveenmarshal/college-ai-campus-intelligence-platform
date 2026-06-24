"""
routes/document_routes.py
Phase 3 — Document upload, processing (PDF RAG), and management endpoints.

Endpoints:
  POST   /api/documents/upload/pdf      — upload + process a PDF into ChromaDB
  GET    /api/documents                 — list documents (paginated)
  GET    /api/documents/:id             — get document detail
  DELETE /api/documents/:id             — delete document + its vectors
  POST   /api/documents/:id/reprocess   — re-run the RAG pipeline on a doc
"""

import logging
import os
from pathlib import Path

from flask import Blueprint, request, g, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.document_model import DocumentModel
from models.audit_model import AuditModel
from models.response import success, created, error, not_found, paginated
from services.auth_service import AuthService, admin_required, active_user_required
from services.file_utils import (
    validate_upload, allowed_file, generate_safe_filename,
    get_upload_path, get_file_category, human_readable_size,
)
from rag.pdf_processor import PDFProcessor
from rag.embedder import embed_chunks
from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)
document_bp = Blueprint("document", __name__)


@document_bp.post("/upload/pdf")
@jwt_required()
@admin_required
def upload_pdf():
    """Upload a PDF and run it through the full RAG ingestion pipeline."""
    if "file" not in request.files:
        return error("No file part in request", 400)

    file = request.files["file"]
    valid, msg = validate_upload(file)
    if not valid:
        return error(msg, 400)

    if get_file_category(file.filename) != "pdf":
        return error("Only PDF files are allowed on this endpoint", 400)

    description = request.form.get("description", "")
    safe_name = generate_safe_filename(file.filename)
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    dest_path = get_upload_path(upload_folder, "pdf", safe_name)
    file.save(str(dest_path))
    file_size = dest_path.stat().st_size

    user_id = get_jwt_identity()
    doc = DocumentModel.create(
        filename=safe_name,
        original_name=file.filename,
        file_path=str(dest_path),
        file_type="pdf",
        file_size=file_size,
        mime_type=file.mimetype or "application/pdf",
        uploaded_by=user_id,
        description=description,
        collection_name="campus_docs",
    )

    try:
        result = PDFProcessor.process_pdf(dest_path, doc_id=doc["id"])
        chunks = result["chunks"]

        if chunks:
            ids, embeddings, metadatas = embed_chunks(chunks)
            documents_text = [c["text"] for c in chunks]
            store = VectorStore("campus_docs")
            store.add_chunks(ids, embeddings, documents_text, metadatas)

        updated_doc = DocumentModel.mark_processed(
            doc["id"], chunk_count=len(chunks), page_count=result["page_count"]
        )

        AuditModel.log(
            user_id=user_id, action="upload_pdf", resource="documents",
            resource_id=doc["id"], ip_address=AuthService.get_ip(),
            details={"filename": file.filename, "chunks": len(chunks)},
        )

        return created({
            **updated_doc,
            "chunks_created": len(chunks),
            "file_size_readable": human_readable_size(file_size),
        }, f"PDF processed successfully — {len(chunks)} chunks indexed")

    except Exception as exc:
        logger.exception("PDF processing failed for %s", file.filename)
        DocumentModel.mark_failed(doc["id"], str(exc))
        return error(f"PDF uploaded but processing failed: {exc}", 500)


@document_bp.post("/upload/excel")
@jwt_required()
@admin_required
def upload_excel_delegate():
    """Delegate to excel upload route handler."""
    from routes.excel_routes import upload_excel
    return upload_excel()


@document_bp.post("/upload/csv")
@jwt_required()
@admin_required
def upload_csv_delegate():
    """Delegate to csv upload route handler."""
    from routes.csv_routes import upload_csv
    return upload_csv()


@document_bp.get("")
@jwt_required()
@active_user_required
def list_documents():
    page     = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    file_type = request.args.get("file_type")
    search    = request.args.get("search")

    docs, total = DocumentModel.find_all(page=page, per_page=per_page, file_type=file_type, search=search)
    return paginated(docs, total, page, per_page)


@document_bp.get("/<string:doc_id>")
@jwt_required()
@active_user_required
def get_document(doc_id):
    doc = DocumentModel.find_by_id(doc_id)
    if not doc:
        return not_found("Document")
    return success(doc)


@document_bp.delete("/<string:doc_id>")
@jwt_required()
@admin_required
def delete_document(doc_id):
    doc = DocumentModel.find_by_id(doc_id)
    if not doc:
        return not_found("Document")

    # Remove vectors
    try:
        store = VectorStore(doc.get("collection_name", "campus_docs"))
        store.delete_by_doc_id(doc_id)
    except Exception as exc:
        logger.warning("Failed to delete vectors for doc %s: %s", doc_id, exc)

    # Remove file from disk
    try:
        file_path = Path(doc["file_path"])
        if file_path.exists():
            file_path.unlink()
    except Exception as exc:
        logger.warning("Failed to delete file %s: %s", doc.get("file_path"), exc)

    DocumentModel.delete(doc_id)

    AuditModel.log(
        user_id=get_jwt_identity(), action="delete_document", resource="documents",
        resource_id=doc_id, ip_address=AuthService.get_ip(),
    )
    return success(message="Document deleted")


@document_bp.post("/<string:doc_id>/reprocess")
@jwt_required()
@admin_required
def reprocess_document(doc_id):
    doc = DocumentModel.find_by_id(doc_id)
    if not doc:
        return not_found("Document")

    if doc["file_type"] != "pdf":
        return error("Reprocessing currently only supports PDF documents", 400)

    file_path = Path(doc["file_path"])
    if not file_path.exists():
        return error("Original file no longer exists on disk", 404)

    try:
        store = VectorStore(doc.get("collection_name", "campus_docs"))
        store.delete_by_doc_id(doc_id)

        result = PDFProcessor.process_pdf(file_path, doc_id=doc_id)
        chunks = result["chunks"]
        if chunks:
            ids, embeddings, metadatas = embed_chunks(chunks)
            store.add_chunks(ids, embeddings, [c["text"] for c in chunks], metadatas)

        updated = DocumentModel.mark_processed(doc_id, len(chunks), result["page_count"])
        return success(updated, f"Reprocessed — {len(chunks)} chunks")
    except Exception as exc:
        DocumentModel.mark_failed(doc_id, str(exc))
        return error(f"Reprocessing failed: {exc}", 500)

"""
models/document_model.py
MongoDB operations for the 'documents' collection.
Tracks every uploaded file and its processing status.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from pymongo import ReturnDocument

from config.database import get_db

logger = logging.getLogger(__name__)


def utcnow():
    return datetime.now(timezone.utc)


class DocumentModel:
    COLLECTION = "documents"

    @staticmethod
    def _serialise(doc: dict) -> dict:
        if not doc:
            return doc
        out = dict(doc)
        out["id"] = str(out.pop("_id"))
        if out.get("uploaded_by"):
            out["uploaded_by"] = str(out["uploaded_by"])
        for f in ("created_at", "updated_at"):
            if isinstance(out.get(f), datetime):
                out[f] = out[f].isoformat()
        return out

    @classmethod
    def create(cls, filename: str, original_name: str, file_path: str,
               file_type: str, file_size: int, mime_type: str,
               uploaded_by: str, description: str = "",
               collection_name: str = "campus_docs") -> dict:
        now = utcnow()
        doc = {
            "filename": filename,
            "original_name": original_name,
            "file_path": file_path,
            "file_type": file_type,
            "file_size": file_size,
            "mime_type": mime_type,
            "uploaded_by": ObjectId(uploaded_by) if uploaded_by else None,
            "description": description,
            "tags": [],
            "is_processed": False,
            "collection_name": collection_name,
            "chunk_count": 0,
            "page_count": 0,
            "processing_error": None,
            "created_at": now,
            "updated_at": now,
        }
        result = get_db()[cls.COLLECTION].insert_one(doc)
        doc["_id"] = result.inserted_id
        return cls._serialise(doc)

    @classmethod
    def find_by_id(cls, doc_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(doc_id)
        except Exception:
            return None
        doc = get_db()[cls.COLLECTION].find_one({"_id": oid})
        return cls._serialise(doc) if doc else None

    @classmethod
    def find_all(cls, page: int = 1, per_page: int = 20,
                 file_type: str = None, search: str = None,
                 uploaded_by: str = None) -> tuple[list, int]:
        db = get_db()
        query = {}
        if file_type:
            query["file_type"] = file_type
        if uploaded_by:
            query["uploaded_by"] = ObjectId(uploaded_by)
        if search:
            query["original_name"] = {"$regex": search, "$options": "i"}

        total = db[cls.COLLECTION].count_documents(query)
        skip = (page - 1) * per_page
        docs = list(
            db[cls.COLLECTION].find(query)
            .sort("created_at", -1)
            .skip(skip).limit(per_page)
        )
        return [cls._serialise(d) for d in docs], total

    @classmethod
    def mark_processed(cls, doc_id: str, chunk_count: int, page_count: int = 0) -> Optional[dict]:
        try:
            oid = ObjectId(doc_id)
        except Exception:
            return None
        doc = get_db()[cls.COLLECTION].find_one_and_update(
            {"_id": oid},
            {"$set": {
                "is_processed": True,
                "chunk_count": chunk_count,
                "page_count": page_count,
                "processing_error": None,
                "updated_at": utcnow(),
            }},
            return_document=ReturnDocument.AFTER,
        )
        return cls._serialise(doc) if doc else None

    @classmethod
    def mark_failed(cls, doc_id: str, error_msg: str) -> None:
        try:
            oid = ObjectId(doc_id)
        except Exception:
            return
        get_db()[cls.COLLECTION].update_one(
            {"_id": oid},
            {"$set": {
                "is_processed": False,
                "processing_error": error_msg,
                "updated_at": utcnow(),
            }}
        )

    @classmethod
    def delete(cls, doc_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(doc_id)
        except Exception:
            return None
        doc = get_db()[cls.COLLECTION].find_one({"_id": oid})
        if doc:
            get_db()[cls.COLLECTION].delete_one({"_id": oid})
        return cls._serialise(doc) if doc else None

    @classmethod
    def count_by_type(cls) -> dict:
        pipeline = [{"$group": {"_id": "$file_type", "count": {"$sum": 1}}}]
        return {r["_id"]: r["count"] for r in get_db()[cls.COLLECTION].aggregate(pipeline)}

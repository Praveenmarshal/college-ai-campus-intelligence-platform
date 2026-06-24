"""
models/faculty_model.py
MongoDB operations for the 'faculty' collection.
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


class FacultyModel:
    COLLECTION = "faculty"

    @staticmethod
    def _serialise(doc):
        if not doc:
            return doc
        out = dict(doc)
        out["id"] = str(out.pop("_id"))
        if out.get("user_id"):
            out["user_id"] = str(out["user_id"])
        for f in ("created_at", "updated_at"):
            if isinstance(out.get(f), datetime):
                out[f] = out[f].isoformat()
        return out

    @classmethod
    def create(cls, **kwargs) -> dict:
        now = utcnow()
        doc = {
            "faculty_id": kwargs["faculty_id"],
            "user_id": ObjectId(kwargs["user_id"]) if kwargs.get("user_id") else None,
            "name": kwargs["name"],
            "email": kwargs["email"].lower().strip(),
            "phone": kwargs.get("phone", ""),
            "department": kwargs.get("department", ""),
            "designation": kwargs.get("designation", ""),
            "subjects": kwargs.get("subjects", []),
            "qualification": kwargs.get("qualification", ""),
            "experience_years": kwargs.get("experience_years", 0),
            "created_at": now, "updated_at": now,
        }
        db = get_db()
        if db[cls.COLLECTION].find_one({"faculty_id": doc["faculty_id"]}):
            raise ValueError(f"Faculty ID '{doc['faculty_id']}' already exists")
        result = db[cls.COLLECTION].insert_one(doc)
        doc["_id"] = result.inserted_id
        return cls._serialise(doc)

    @classmethod
    def find_by_id(cls, fid: str) -> Optional[dict]:
        try:
            doc = get_db()[cls.COLLECTION].find_one({"_id": ObjectId(fid)})
        except Exception:
            doc = get_db()[cls.COLLECTION].find_one({"faculty_id": fid})
        return cls._serialise(doc) if doc else None

    @classmethod
    def find_by_user_id(cls, user_id: str) -> Optional[dict]:
        try:
            doc = get_db()[cls.COLLECTION].find_one({"user_id": ObjectId(user_id)})
        except Exception:
            return None
        return cls._serialise(doc) if doc else None

    @classmethod
    def find_all(cls, page=1, per_page=20, department=None, search=None) -> tuple[list, int]:
        db = get_db()
        query = {}
        if department:
            query["department"] = department
        if search:
            query["$or"] = [{"name": {"$regex": search, "$options": "i"}}, {"faculty_id": {"$regex": search, "$options": "i"}}]
        total = db[cls.COLLECTION].count_documents(query)
        skip = (page - 1) * per_page
        docs = list(db[cls.COLLECTION].find(query).sort("name", 1).skip(skip).limit(per_page))
        return [cls._serialise(d) for d in docs], total

    @classmethod
    def update(cls, fid: str, updates: dict) -> Optional[dict]:
        forbidden = {"_id", "id", "faculty_id", "user_id"}
        safe = {k: v for k, v in updates.items() if k not in forbidden}
        safe["updated_at"] = utcnow()
        try:
            query = {"_id": ObjectId(fid)}
        except Exception:
            query = {"faculty_id": fid}
        doc = get_db()[cls.COLLECTION].find_one_and_update(query, {"$set": safe}, return_document=ReturnDocument.AFTER)
        return cls._serialise(doc) if doc else None

    @classmethod
    def delete(cls, fid: str) -> bool:
        try:
            query = {"_id": ObjectId(fid)}
        except Exception:
            query = {"faculty_id": fid}
        result = get_db()[cls.COLLECTION].delete_one(query)
        return result.deleted_count > 0

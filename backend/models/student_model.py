"""
models/student_model.py
MongoDB operations for the 'students' collection.
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


class StudentModel:
    COLLECTION = "students"

    @staticmethod
    def _serialise(doc: dict) -> dict:
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
            "student_id": kwargs["student_id"],
            "user_id": ObjectId(kwargs["user_id"]) if kwargs.get("user_id") else None,
            "name": kwargs["name"],
            "email": kwargs["email"].lower().strip(),
            "phone": kwargs.get("phone", ""),
            "department": kwargs.get("department", ""),
            "batch_year": kwargs.get("batch_year"),
            "semester": kwargs.get("semester", 1),
            "section": kwargs.get("section", ""),
            "cgpa": kwargs.get("cgpa", 0.0),
            "address": kwargs.get("address", ""),
            "guardian_name": kwargs.get("guardian_name", ""),
            "guardian_phone": kwargs.get("guardian_phone", ""),
            "is_hostel": kwargs.get("is_hostel", False),
            "created_at": now,
            "updated_at": now,
        }
        db = get_db()
        if db[cls.COLLECTION].find_one({"student_id": doc["student_id"]}):
            raise ValueError(f"Student ID '{doc['student_id']}' already exists")

        result = db[cls.COLLECTION].insert_one(doc)
        doc["_id"] = result.inserted_id
        return cls._serialise(doc)

    @classmethod
    def find_by_id(cls, student_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(student_id)
            doc = get_db()[cls.COLLECTION].find_one({"_id": oid})
        except Exception:
            doc = get_db()[cls.COLLECTION].find_one({"student_id": student_id})
        return cls._serialise(doc) if doc else None

    @classmethod
    def find_by_student_id(cls, student_id: str) -> Optional[dict]:
        doc = get_db()[cls.COLLECTION].find_one({"student_id": student_id})
        return cls._serialise(doc) if doc else None

    @classmethod
    def find_by_user_id(cls, user_id: str) -> Optional[dict]:
        try:
            doc = get_db()[cls.COLLECTION].find_one({"user_id": ObjectId(user_id)})
        except Exception:
            return None
        return cls._serialise(doc) if doc else None

    @classmethod
    def find_all(cls, page: int = 1, per_page: int = 20, department: str = None,
                 batch_year: int = None, search: str = None) -> tuple[list, int]:
        db = get_db()
        query = {}
        if department:
            query["department"] = department
        if batch_year:
            query["batch_year"] = batch_year
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"student_id": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
            ]

        total = db[cls.COLLECTION].count_documents(query)
        skip = (page - 1) * per_page
        docs = list(db[cls.COLLECTION].find(query).sort("name", 1).skip(skip).limit(per_page))
        return [cls._serialise(d) for d in docs], total

    @classmethod
    def update(cls, student_id: str, updates: dict) -> Optional[dict]:
        forbidden = {"_id", "id", "student_id", "user_id"}
        safe = {k: v for k, v in updates.items() if k not in forbidden}
        safe["updated_at"] = utcnow()

        try:
            oid = ObjectId(student_id)
            query = {"_id": oid}
        except Exception:
            query = {"student_id": student_id}

        doc = get_db()[cls.COLLECTION].find_one_and_update(
            query, {"$set": safe}, return_document=ReturnDocument.AFTER
        )
        return cls._serialise(doc) if doc else None

    @classmethod
    def delete(cls, student_id: str) -> bool:
        try:
            oid = ObjectId(student_id)
            query = {"_id": oid}
        except Exception:
            query = {"student_id": student_id}
        result = get_db()[cls.COLLECTION].delete_one(query)
        return result.deleted_count > 0

    @classmethod
    def count_by_department(cls) -> dict:
        pipeline = [{"$group": {"_id": "$department", "count": {"$sum": 1}}}]
        return {r["_id"]: r["count"] for r in get_db()[cls.COLLECTION].aggregate(pipeline)}

    @classmethod
    def bulk_create(cls, students: list[dict]) -> dict:
        """Bulk insert students (used by Excel bulk upload). Skips duplicates."""
        db = get_db()
        created, skipped = 0, 0
        now = utcnow()

        for s in students:
            if not s.get("student_id") or not s.get("email"):
                skipped += 1
                continue
            if db[cls.COLLECTION].find_one({"student_id": s["student_id"]}):
                skipped += 1
                continue
            doc = {**s, "created_at": now, "updated_at": now}
            db[cls.COLLECTION].insert_one(doc)
            created += 1

        return {"created": created, "skipped": skipped, "total": len(students)}

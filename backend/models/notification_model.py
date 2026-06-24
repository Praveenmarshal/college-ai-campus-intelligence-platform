"""
models/notification_model.py
MongoDB operations for the 'notifications' collection.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId

from config.database import get_db

logger = logging.getLogger(__name__)


def utcnow():
    return datetime.now(timezone.utc)


class NotificationModel:
    COLLECTION = "notifications"

    @staticmethod
    def _serialise(doc: dict) -> dict:
        if not doc:
            return doc
        out = dict(doc)
        out["id"] = str(out.pop("_id"))
        out["user_id"] = str(out["user_id"])
        for f in ("created_at", "sent_at"):
            if isinstance(out.get(f), datetime):
                out[f] = out[f].isoformat()
        return out

    @classmethod
    def create(cls, user_id: str, title: str, message: str,
               notification_type: str = "system", channel: str = "in-app") -> dict:
        doc = {
            "user_id": ObjectId(user_id),
            "title": title,
            "message": message,
            "notification_type": notification_type,
            "channel": channel,
            "is_read": False,
            "is_sent": True,
            "sent_at": utcnow(),
            "created_at": utcnow(),
        }
        result = get_db()[cls.COLLECTION].insert_one(doc)
        doc["_id"] = result.inserted_id
        return cls._serialise(doc)

    @classmethod
    def find_by_user(cls, user_id: str, page: int = 1, per_page: int = 20, unread_only: bool = False) -> tuple[list, int]:
        db = get_db()
        query = {"user_id": ObjectId(user_id)}
        if unread_only:
            query["is_read"] = False

        total = db[cls.COLLECTION].count_documents(query)
        skip = (page - 1) * per_page
        docs = list(
            db[cls.COLLECTION].find(query).sort("created_at", -1).skip(skip).limit(per_page)
        )
        return [cls._serialise(d) for d in docs], total

    @classmethod
    def mark_read(cls, notification_id: str, user_id: str) -> bool:
        result = get_db()[cls.COLLECTION].update_one(
            {"_id": ObjectId(notification_id), "user_id": ObjectId(user_id)},
            {"$set": {"is_read": True}},
        )
        return result.modified_count > 0

    @classmethod
    def mark_all_read(cls, user_id: str) -> int:
        result = get_db()[cls.COLLECTION].update_many(
            {"user_id": ObjectId(user_id), "is_read": False},
            {"$set": {"is_read": True}},
        )
        return result.modified_count

    @classmethod
    def delete(cls, notification_id: str, user_id: str) -> bool:
        result = get_db()[cls.COLLECTION].delete_one(
            {"_id": ObjectId(notification_id), "user_id": ObjectId(user_id)}
        )
        return result.deleted_count > 0

    @classmethod
    def count_unread(cls, user_id: str) -> int:
        return get_db()[cls.COLLECTION].count_documents(
            {"user_id": ObjectId(user_id), "is_read": False}
        )

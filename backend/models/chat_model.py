"""
models/chat_model.py
MongoDB operations for the 'chats' collection — conversation sessions.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId

from config.database import get_db

logger = logging.getLogger(__name__)


def utcnow():
    return datetime.now(timezone.utc)


class ChatModel:
    COLLECTION = "chats"

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
        for msg in out.get("messages", []):
            if isinstance(msg.get("timestamp"), datetime):
                msg["timestamp"] = msg["timestamp"].isoformat()
        return out

    @classmethod
    def create_session(cls, user_id: str, first_message: str = "") -> dict:
        session_id = str(uuid.uuid4())
        now = utcnow()
        title = (first_message[:60] + "…") if len(first_message) > 60 else (first_message or "New Chat")

        doc = {
            "session_id": session_id,
            "user_id": ObjectId(user_id),
            "title": title,
            "messages": [],
            "agent_type": None,
            "created_at": now,
            "updated_at": now,
        }
        result = get_db()[cls.COLLECTION].insert_one(doc)
        doc["_id"] = result.inserted_id
        return cls._serialise(doc)

    @classmethod
    def find_by_session_id(cls, session_id: str, user_id: str = None) -> Optional[dict]:
        query = {"session_id": session_id}
        if user_id:
            query["user_id"] = ObjectId(user_id)
        doc = get_db()[cls.COLLECTION].find_one(query)
        return cls._serialise(doc) if doc else None

    @classmethod
    def append_message(cls, session_id: str, role: str, content: str,
                        sources: list = None, agent_used: str = None) -> Optional[dict]:
        message = {
            "role": role,
            "content": content,
            "sources": sources or [],
            "agent_used": agent_used,
            "timestamp": utcnow(),
        }
        update = {"$push": {"messages": message}, "$set": {"updated_at": utcnow()}}
        if agent_used:
            update["$set"]["agent_type"] = agent_used

        doc = get_db()[cls.COLLECTION].find_one_and_update(
            {"session_id": session_id},
            update,
            return_document=True,
        )
        return cls._serialise(doc) if doc else None

    @classmethod
    def list_sessions(cls, user_id: str, limit: int = 50) -> list:
        docs = list(
            get_db()[cls.COLLECTION]
            .find({"user_id": ObjectId(user_id)}, {"messages": {"$slice": -1}})
            .sort("updated_at", -1)
            .limit(limit)
        )
        return [cls._serialise(d) for d in docs]

    @classmethod
    def delete_session(cls, session_id: str, user_id: str) -> bool:
        result = get_db()[cls.COLLECTION].delete_one({
            "session_id": session_id,
            "user_id": ObjectId(user_id),
        })
        return result.deleted_count > 0

    @classmethod
    def delete_all_sessions(cls, user_id: str) -> int:
        result = get_db()[cls.COLLECTION].delete_many({"user_id": ObjectId(user_id)})
        return result.deleted_count

    @classmethod
    def get_recent_messages(cls, session_id: str, limit: int = 10) -> list:
        """Return last N messages formatted for LLM chat history."""
        doc = get_db()[cls.COLLECTION].find_one({"session_id": session_id})
        if not doc:
            return []
        msgs = doc.get("messages", [])[-limit:]
        return [{"role": m["role"], "content": m["content"]} for m in msgs]

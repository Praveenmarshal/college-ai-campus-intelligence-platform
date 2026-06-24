"""
models/audit_model.py
Audit log — records every significant user action for compliance and security.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from config.database import get_db

logger = logging.getLogger(__name__)


def utcnow():
    return datetime.now(timezone.utc)


class AuditModel:
    COLLECTION = "audit_logs"

    @classmethod
    def log(cls, user_id: str, action: str, resource: str = "",
            resource_id: str = "", status: str = "success",
            ip_address: str = "", user_agent: str = "", details: dict = None) -> None:
        """
        Record an audit event. Fire-and-forget — never raises.
        """
        try:
            doc = {
                "user_id": ObjectId(user_id) if user_id else None,
                "action": action,
                "resource": resource,
                "resource_id": resource_id,
                "status": status,
                "ip_address": ip_address,
                "user_agent": user_agent[:200] if user_agent else "",
                "details": details or {},
                "timestamp": utcnow(),
            }
            get_db()[cls.COLLECTION].insert_one(doc)
        except Exception as exc:
            logger.warning("Audit log failed (non-fatal): %s", exc)

    @classmethod
    def find_by_user(cls, user_id: str, limit: int = 50) -> list:
        try:
            oid = ObjectId(user_id)
        except Exception:
            return []
        docs = list(
            get_db()[cls.COLLECTION]
            .find({"user_id": oid})
            .sort("timestamp", -1)
            .limit(limit)
        )
        for d in docs:
            d["id"] = str(d.pop("_id"))
            d["user_id"] = str(d["user_id"])
            if isinstance(d.get("timestamp"), datetime):
                d["timestamp"] = d["timestamp"].isoformat()
        return docs

    @classmethod
    def find_recent(cls, limit: int = 100, action: str = None) -> list:
        query = {}
        if action:
            query["action"] = action
        docs = list(
            get_db()[cls.COLLECTION]
            .find(query)
            .sort("timestamp", -1)
            .limit(limit)
        )
        for d in docs:
            d["id"] = str(d.pop("_id"))
            d["user_id"] = str(d["user_id"]) if d.get("user_id") else None
            if isinstance(d.get("timestamp"), datetime):
                d["timestamp"] = d["timestamp"].isoformat()
        return docs

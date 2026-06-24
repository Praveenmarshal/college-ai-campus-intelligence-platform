"""
models/user_model.py
User domain model — wraps MongoDB operations for the users collection.
Handles password hashing, token management, and RBAC.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import bcrypt
from bson import ObjectId
from pymongo import ReturnDocument

from config.database import get_db

logger = logging.getLogger(__name__)

VALID_ROLES = {"admin", "faculty", "student"}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserModel:
    """
    All database operations for the 'users' collection.
    Returns plain dicts (serialisable), never raw BSON.
    """

    COLLECTION = "users"

    # ── Serialisation ──────────────────────────────────────
    @staticmethod
    def _serialise(doc: dict) -> dict:
        """Convert ObjectId fields to strings and strip password hash."""
        if not doc:
            return doc
        out = dict(doc)
        out["id"] = str(out.pop("_id"))
        out.pop("password_hash", None)
        out.pop("refresh_token_jti", None)
        if isinstance(out.get("created_at"), datetime):
            out["created_at"] = out["created_at"].isoformat()
        if isinstance(out.get("updated_at"), datetime):
            out["updated_at"] = out["updated_at"].isoformat()
        if isinstance(out.get("last_login"), datetime):
            out["last_login"] = out["last_login"].isoformat()
        return out

    # ── Password helpers ───────────────────────────────────
    @staticmethod
    def hash_password(plain: str) -> str:
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False

    # ── Create ─────────────────────────────────────────────
    @classmethod
    def create(cls, name: str, email: str, password: str, role: str = "student",
               department: str = "", phone: str = "") -> dict:
        """
        Create a new user. Raises ValueError on duplicate email or bad role.
        Returns serialised user dict (no password hash).
        """
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role '{role}'. Must be one of: {VALID_ROLES}")

        db = get_db()
        if db[cls.COLLECTION].find_one({"email": email.lower().strip()}):
            raise ValueError(f"Email '{email}' is already registered.")

        now = utcnow()
        doc = {
            "name": name.strip(),
            "email": email.lower().strip(),
            "password_hash": cls.hash_password(password),
            "role": role,
            "department": department.strip(),
            "phone": phone.strip(),
            "is_active": True,
            "profile_picture": "",
            "refresh_token_jti": None,
            "created_at": now,
            "updated_at": now,
            "last_login": None,
        }

        result = db[cls.COLLECTION].insert_one(doc)
        doc["_id"] = result.inserted_id
        logger.info("User created: %s (%s)", email, role)
        return cls._serialise(doc)

    @classmethod
    def find_or_create_google_user(cls, email: str, name: str,
                                    picture: str = "") -> dict:
        """
        Find a user by email or create one from Google OAuth profile.
        Google users have no password_hash — they authenticate via OAuth only.
        Returns serialised user dict.
        """
        db = get_db()
        doc = db[cls.COLLECTION].find_one({"email": email.lower().strip()})

        if doc:
            # Update name/picture from Google on every login (keeps data fresh)
            updates = {"last_login": utcnow(), "updated_at": utcnow()}
            if name:
                updates["name"] = name.strip()
            if picture:
                updates["profile_picture"] = picture
            doc = db[cls.COLLECTION].find_one_and_update(
                {"_id": doc["_id"]},
                {"$set": updates},
                return_document=ReturnDocument.AFTER,
            )
            return cls._serialise(doc)

        # New user — create with default student role
        now = utcnow()
        new_doc = {
            "name": name.strip(),
            "email": email.lower().strip(),
            "password_hash": "",          # no password for OAuth users
            "auth_provider": "google",
            "role": "student",
            "department": "",
            "phone": "",
            "is_active": True,
            "profile_picture": picture or "",
            "refresh_token_jti": None,
            "created_at": now,
            "updated_at": now,
            "last_login": now,
        }
        result = db[cls.COLLECTION].insert_one(new_doc)
        new_doc["_id"] = result.inserted_id
        logger.info("Google user created: %s", email)
        return cls._serialise(new_doc)

    # ── Read ───────────────────────────────────────────────
    @classmethod
    def find_by_email(cls, email: str, include_password: bool = False) -> Optional[dict]:
        db = get_db()
        doc = db[cls.COLLECTION].find_one({"email": email.lower().strip()})
        if not doc:
            return None
        if include_password:
            out = dict(doc)
            out["id"] = str(out.pop("_id"))
            return out
        return cls._serialise(doc)

    @classmethod
    def find_by_id(cls, user_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(user_id)
        except Exception:
            return None
        db = get_db()
        doc = db[cls.COLLECTION].find_one({"_id": oid})
        return cls._serialise(doc) if doc else None

    @classmethod
    def find_all(cls, page: int = 1, per_page: int = 20,
                 role: str = None, search: str = None) -> tuple[list, int]:
        db = get_db()
        query: dict = {}
        if role and role in VALID_ROLES:
            query["role"] = role
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
            ]
        total = db[cls.COLLECTION].count_documents(query)
        skip = (page - 1) * per_page
        docs = list(
            db[cls.COLLECTION]
            .find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(per_page)
        )
        return [cls._serialise(d) for d in docs], total

    # ── Update ─────────────────────────────────────────────
    @classmethod
    def update(cls, user_id: str, updates: dict) -> Optional[dict]:
        """Update allowed fields. Never allows password or role updates directly."""
        try:
            oid = ObjectId(user_id)
        except Exception:
            return None

        # Strip fields that should never be updated via this method
        forbidden = {"password_hash", "role", "email", "_id", "id", "refresh_token_jti"}
        safe = {k: v for k, v in updates.items() if k not in forbidden}
        safe["updated_at"] = utcnow()

        db = get_db()
        doc = db[cls.COLLECTION].find_one_and_update(
            {"_id": oid},
            {"$set": safe},
            return_document=ReturnDocument.AFTER,
        )
        return cls._serialise(doc) if doc else None

    @classmethod
    def change_password(cls, user_id: str, new_password: str) -> bool:
        try:
            oid = ObjectId(user_id)
        except Exception:
            return False
        db = get_db()
        result = db[cls.COLLECTION].update_one(
            {"_id": oid},
            {"$set": {
                "password_hash": cls.hash_password(new_password),
                "updated_at": utcnow(),
            }}
        )
        return result.modified_count > 0

    @classmethod
    def update_role(cls, user_id: str, new_role: str) -> Optional[dict]:
        if new_role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {new_role}")
        try:
            oid = ObjectId(user_id)
        except Exception:
            return None
        db = get_db()
        doc = db[cls.COLLECTION].find_one_and_update(
            {"_id": oid},
            {"$set": {"role": new_role, "updated_at": utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
        return cls._serialise(doc) if doc else None

    @classmethod
    def set_active(cls, user_id: str, is_active: bool) -> bool:
        try:
            oid = ObjectId(user_id)
        except Exception:
            return False
        db = get_db()
        result = db[cls.COLLECTION].update_one(
            {"_id": oid},
            {"$set": {"is_active": is_active, "updated_at": utcnow()}}
        )
        return result.modified_count > 0

    @classmethod
    def record_login(cls, user_id: str, jti: str) -> None:
        """Record last login time and store active refresh token JTI."""
        try:
            oid = ObjectId(user_id)
        except Exception:
            return
        get_db()[cls.COLLECTION].update_one(
            {"_id": oid},
            {"$set": {"last_login": utcnow(), "refresh_token_jti": jti}}
        )

    @classmethod
    def revoke_refresh_token(cls, user_id: str) -> None:
        """Invalidate the stored refresh token JTI (logout)."""
        try:
            oid = ObjectId(user_id)
        except Exception:
            return
        get_db()[cls.COLLECTION].update_one(
            {"_id": oid},
            {"$set": {"refresh_token_jti": None}}
        )

    @classmethod
    def get_refresh_jti(cls, user_id: str) -> Optional[str]:
        try:
            oid = ObjectId(user_id)
        except Exception:
            return None
        doc = get_db()[cls.COLLECTION].find_one({"_id": oid}, {"refresh_token_jti": 1})
        return doc.get("refresh_token_jti") if doc else None

    # ── Delete ─────────────────────────────────────────────
    @classmethod
    def delete(cls, user_id: str) -> bool:
        try:
            oid = ObjectId(user_id)
        except Exception:
            return False
        result = get_db()[cls.COLLECTION].delete_one({"_id": oid})
        return result.deleted_count > 0

    # ── Stats ──────────────────────────────────────────────
    @classmethod
    def count_by_role(cls) -> dict:
        db = get_db()
        pipeline = [{"$group": {"_id": "$role", "count": {"$sum": 1}}}]
        return {r["_id"]: r["count"] for r in db[cls.COLLECTION].aggregate(pipeline)}

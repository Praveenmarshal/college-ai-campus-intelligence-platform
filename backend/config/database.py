"""
config/database.py
MongoDB connection manager using PyMongo.
Provides a singleton database client shared across the app.
"""

import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ConfigurationError

logger = logging.getLogger(__name__)


class MongoManager:
    """Singleton MongoDB connection manager."""

    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    @classmethod
    def init_app(cls, app) -> None:
        """
        Initialise MongoDB connection from Flask app config.
        Called once during application startup.
        """
        mongo_uri = app.config.get("MONGO_URI")
        db_name = app.config.get("MONGO_DB_NAME", "campus_ai")

        try:
            cls._client = MongoClient(
    		mongo_uri,
    		serverSelectionTimeoutMS=8000,
    		connectTimeoutMS=8000,
    		socketTimeoutMS=10000,
    		maxPoolSize=10,
    		minPoolSize=1,
    		tls=True,
    		tlsAllowInvalidCertificates=True,
	    )
            # Verify the connection works
            cls._client.admin.command("ping")
            cls._db = cls._client[db_name]
            logger.info("[OK] MongoDB connected - database: %s", db_name)

            # Create indexes on first connect
            cls._create_indexes()

        except ConnectionFailure as exc:
            logger.error("❌ MongoDB connection failed: %s", exc)
            raise
        except ConfigurationError as exc:
            logger.error("❌ MongoDB configuration error: %s", exc)
            raise

    @classmethod
    def get_db(cls) -> Database:
        """Return the active database instance."""
        if cls._db is None:
            raise RuntimeError(
                "MongoDB not initialised. Call MongoManager.init_app(app) first."
            )
        return cls._db

    @classmethod
    def close(cls) -> None:
        """Close the MongoDB connection."""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            logger.info("MongoDB connection closed")

    @classmethod
    def _create_indexes(cls) -> None:
        """Create all required indexes for optimal query performance."""
        db = cls._db

        # Users
        db.users.create_index("email", unique=True)
        db.users.create_index("role")

        # Students
        db.students.create_index("student_id", unique=True)
        db.students.create_index("email", unique=True)
        db.students.create_index("department")
        db.students.create_index("batch_year")

        # Faculty
        db.faculty.create_index("faculty_id", unique=True)
        db.faculty.create_index("email", unique=True)
        db.faculty.create_index("department")

        # Attendance
        db.attendance.create_index([("student_id", 1), ("date", -1)])
        db.attendance.create_index([("course_id", 1), ("date", -1)])
        db.attendance.create_index("status")

        # Placements
        db.placements.create_index("student_id")
        db.placements.create_index("company_name")
        db.placements.create_index("year")
        db.placements.create_index("status")

        # Chats
        db.chats.create_index([("user_id", 1), ("created_at", -1)])
        db.chats.create_index("session_id")

        # Documents (uploaded files)
        db.documents.create_index("uploaded_by")
        db.documents.create_index("file_type")
        db.documents.create_index("created_at")

        # Fees
        db.fees.create_index("student_id")
        db.fees.create_index([("student_id", 1), ("semester", 1)])
        db.fees.create_index("payment_status")

        # Events
        db.events.create_index("event_date")
        db.events.create_index("department")

        # Library
        db.library.create_index("isbn")
        db.library.create_index("title")
        db.library.create_index("author")

        # Hostel
        db.hostel.create_index("student_id", unique=True)
        db.hostel.create_index("room_number")

        # Notifications
        db.notifications.create_index([("user_id", 1), ("is_read", 1)])
        db.notifications.create_index("created_at")

        # Audit Logs
        db.audit_logs.create_index([("user_id", 1), ("timestamp", -1)])
        db.audit_logs.create_index("action")

        logger.info("[OK] MongoDB indexes created")


# Convenience accessor
def get_db() -> Database:
    return MongoManager.get_db()

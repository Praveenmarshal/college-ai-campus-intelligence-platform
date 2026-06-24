"""
routes/admin_routes.py
Admin-only system management endpoints: audit logs, system health, seed data.
"""
import logging
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.audit_model import AuditModel
from models.response import success, error
from services.auth_service import admin_required
from config.database import get_db
from config.chromadb_config import ChromaManager

logger = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/status")
@jwt_required()
@admin_required
def status():
    return success({"module": "admin", "status": "ok"})


@admin_bp.get("/audit-logs")
@jwt_required()
@admin_required
def audit_logs():
    limit = min(200, max(1, int(request.args.get("limit", 100))))
    action = request.args.get("action")
    logs = AuditModel.find_recent(limit=limit, action=action)
    return success(logs)


@admin_bp.get("/system-overview")
@jwt_required()
@admin_required
def system_overview():
    db = get_db()
    collections_stats = {}
    for coll_name in ["users", "students", "faculty", "attendance", "placements",
                       "documents", "chats", "fees", "events", "library", "hostel"]:
        try:
            collections_stats[coll_name] = db[coll_name].count_documents({})
        except Exception:
            collections_stats[coll_name] = 0

    chroma_health = ChromaManager.health_check()

    return success({
        "mongodb_collections": collections_stats,
        "chromadb": chroma_health,
    })

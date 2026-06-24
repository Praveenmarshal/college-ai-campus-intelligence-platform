"""
routes/mongo_query_routes.py
Phase 6 — Natural language MongoDB query endpoints.
"""

import logging

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.response import success, error
from models.audit_model import AuditModel
from services.auth_service import AuthService, active_user_required
from services.mongo_query_service import MongoQueryEngine

logger = logging.getLogger(__name__)
mongo_query_bp = Blueprint("mongo_query", __name__)


@mongo_query_bp.get("/collections")
@jwt_required()
@active_user_required
def list_collections():
    """List collections and fields available for NL querying."""
    return success(MongoQueryEngine.list_collections())


@mongo_query_bp.post("/ask")
@jwt_required()
@active_user_required
def ask():
    """
    Ask a natural language question about MongoDB data.
    Body: { question: str, collection: str }
    """
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    collection = (body.get("collection") or "").strip()

    if not question:
        return error("Question cannot be empty", 400)
    if not collection:
        return error("Collection name is required", 400)

    try:
        result = MongoQueryEngine.query(question, collection)
        AuditModel.log(
            user_id=get_jwt_identity(), action="mongo_nl_query", resource=collection,
            ip_address=AuthService.get_ip(), details={"question": question[:200]},
        )
        return success(result, "Query executed successfully")
    except ValueError as exc:
        return error(str(exc), 400)
    except RuntimeError as exc:
        return error(str(exc), 503)

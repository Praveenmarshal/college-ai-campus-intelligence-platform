"""
routes/router_routes.py
Phase 7/8 — Smart Query Router + Multi-Agent endpoints.

Endpoints:
  POST /api/router/ask           — classify + route + dispatch to best agent
  POST /api/router/ask-hybrid    — combine multiple agents for complex queries
  GET  /api/router/agents        — list all available agents
  POST /api/router/classify      — classify only (debug/admin tool)
"""

import logging

from flask import Blueprint, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.response import success, error
from models.audit_model import AuditModel
from models.chat_model import ChatModel
from services.auth_service import AuthService, active_user_required
from services.query_router import QueryRouter
from agents.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)
router_bp = Blueprint("router", __name__)


@router_bp.post("/ask")
@jwt_required()
@active_user_required
def ask():
    """
    Smart-routed query — classifies intent and dispatches to the best agent.
    Body: { query: str, session_id?: str, context?: dict }
    """
    body = request.get_json(silent=True) or {}
    query = (body.get("query") or "").strip()
    session_id = body.get("session_id")
    extra_context = body.get("context", {})

    if not query:
        return error("Query cannot be empty", 400)

    user_id = g.current_user["id"]

    # Build chat history context if session provided
    context = dict(extra_context)
    if session_id:
        context["chat_history"] = ChatModel.get_recent_messages(session_id, limit=6)

    result = QueryRouter.route(query, context)

    # Persist to chat session if provided
    if session_id:
        ChatModel.append_message(session_id, "user", query)
        ChatModel.append_message(
            session_id, "assistant", result["answer"],
            sources=result.get("sources", []), agent_used=result.get("agent"),
        )

    AuditModel.log(
        user_id=user_id, action="smart_route_query", resource="router",
        ip_address=AuthService.get_ip(),
        details={"agent": result.get("agent"), "routing": result.get("routing")},
    )

    return success(result, "Query routed and answered")


@router_bp.post("/ask-hybrid")
@jwt_required()
@active_user_required
def ask_hybrid():
    """Combine multiple agents for complex multi-domain questions."""
    body = request.get_json(silent=True) or {}
    query = (body.get("query") or "").strip()
    max_agents = min(int(body.get("max_agents", 2)), 4)

    if not query:
        return error("Query cannot be empty", 400)

    result = QueryRouter.route_hybrid(query, context=body.get("context", {}), max_agents=max_agents)

    AuditModel.log(
        user_id=get_jwt_identity(), action="hybrid_route_query", resource="router",
        ip_address=AuthService.get_ip(), details={"agent": result.get("agent")},
    )

    return success(result, "Hybrid query answered")


@router_bp.get("/agents")
@jwt_required()
@active_user_required
def list_agents():
    """List all available specialised agents."""
    return success(AgentOrchestrator.list_agents())


@router_bp.post("/classify")
@jwt_required()
@active_user_required
def classify_only():
    """Debug endpoint — classify a query without executing it."""
    body = request.get_json(silent=True) or {}
    query = (body.get("query") or "").strip()
    if not query:
        return error("Query cannot be empty", 400)

    classification = QueryRouter.classify(query)
    return success(classification)

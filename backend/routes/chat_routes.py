"""
routes/chat_routes.py
Phase 3 — Conversational AI chat endpoints (PDF RAG powered).
Phase 7/8 will extend this with the smart router and multi-agent dispatch.

Endpoints:
  POST   /api/chat/message          — send a message, get an AI response
  GET    /api/chat/sessions         — list user's chat sessions
  GET    /api/chat/sessions/:id     — get full session with messages
  DELETE /api/chat/sessions/:id     — delete one session
  DELETE /api/chat/sessions         — clear all sessions for user
"""

import logging

from flask import Blueprint, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.chat_model import ChatModel
from models.audit_model import AuditModel
from models.response import success, created, error, not_found
from services.auth_service import AuthService, active_user_required
from services.query_router import QueryRouter

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)


@chat_bp.post("/message")
@jwt_required()
@active_user_required
def send_message():
    """
    Send a message to the AI and get a response.
    Body: { message: str, session_id?: str }
    """
    body = request.get_json(silent=True) or {}
    message = (body.get("message") or "").strip()
    session_id = body.get("session_id")

    if not message:
        return error("Message cannot be empty", 400)
    if len(message) > 2000:
        return error("Message too long (max 2000 characters)", 400)

    user_id = g.current_user["id"]

    # Create session if needed
    if session_id:
        session = ChatModel.find_by_session_id(session_id, user_id)
        if not session:
            return not_found("Chat session")
    else:
        session = ChatModel.create_session(user_id, first_message=message)
        session_id = session["session_id"]

    # Get recent history for context (excludes current message)
    history = ChatModel.get_recent_messages(session_id, limit=6)

    # Persist user message
    ChatModel.append_message(session_id, "user", message)

    # Run query router
    context = {"chat_history": history}
    result = QueryRouter.route(message, context=context)

    # Persist assistant message
    ChatModel.append_message(
        session_id, "assistant", result["answer"],
        sources=result.get("sources", []), agent_used=result.get("agent", "general_agent"),
    )

    AuditModel.log(
        user_id=user_id, action="chat_message", resource="chat",
        resource_id=session_id, ip_address=AuthService.get_ip(),
        details={"agent": result.get("agent"), "routing": result.get("routing")},
    )

    return success({
        "response": result["answer"],
        "sources": result.get("sources", []),
        "session_id": session_id,
        "agent_used": result.get("agent", "general_agent"),
    }, "Response generated")


@chat_bp.get("/sessions")
@jwt_required()
@active_user_required
def list_sessions():
    sessions = ChatModel.list_sessions(g.current_user["id"])
    # Reshape for sidebar display
    out = [{
        "id": s["session_id"],
        "title": s["title"],
        "updated_at": s["updated_at"],
        "agent_type": s.get("agent_type"),
        "last_message": s["messages"][0]["content"][:80] if s.get("messages") else "",
    } for s in sessions]
    return success(out)


@chat_bp.get("/sessions/<string:session_id>")
@jwt_required()
@active_user_required
def get_session(session_id):
    session = ChatModel.find_by_session_id(session_id, g.current_user["id"])
    if not session:
        return not_found("Chat session")
    return success({
        "id": session["session_id"],
        "title": session["title"],
        "messages": session["messages"],
        "created_at": session["created_at"],
        "updated_at": session["updated_at"],
    })


@chat_bp.delete("/sessions/<string:session_id>")
@jwt_required()
@active_user_required
def delete_session(session_id):
    ok = ChatModel.delete_session(session_id, g.current_user["id"])
    if not ok:
        return not_found("Chat session")
    return success(message="Chat session deleted")


@chat_bp.delete("/sessions")
@jwt_required()
@active_user_required
def clear_all_sessions():
    count = ChatModel.delete_all_sessions(g.current_user["id"])
    return success({"deleted_count": count}, f"Deleted {count} session(s)")

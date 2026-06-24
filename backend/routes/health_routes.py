"""
routes/health_routes.py
Health check endpoints for monitoring and DevOps.
No authentication required.
"""

from flask import Blueprint, jsonify
from config.database import MongoManager
from config.chromadb_config import ChromaManager
import requests
import os

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    """
    Full system health check.
    Returns status of MongoDB, ChromaDB, and the active LLM provider
    (Ollama or Groq, depending on LLM_PROVIDER).
    """
    results = {
        "status": "healthy",
        "version": "1.0.0",
        "services": {},
    }

    # MongoDB
    try:
        MongoManager.get_db().command("ping")
        results["services"]["mongodb"] = {"status": "healthy"}
    except Exception as exc:
        results["services"]["mongodb"] = {"status": "unhealthy", "error": str(exc)}
        results["status"] = "degraded"

    # ChromaDB
    try:
        chroma_health = ChromaManager.health_check()
        results["services"]["chromadb"] = chroma_health
    except Exception as exc:
        results["services"]["chromadb"] = {"status": "unhealthy", "error": str(exc)}
        results["status"] = "degraded"

    # LLM provider (Ollama or Groq)
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    try:
        from rag.llm_client import llm_client
        if llm_client.is_available():
            results["services"]["llm"] = {
                "status": "healthy",
                "provider": provider,
                "model": llm_client.model,
                "available_models": llm_client.list_models()[:10],
            }
        else:
            results["services"]["llm"] = {
                "status": "unhealthy",
                "provider": provider,
                "reason": (
                    "GEMINI_API_KEY not set" if provider == "gemini"
                    else "GROQ_API_KEY not set or invalid" if provider == "groq"
                    else "Ollama not reachable — ensure 'ollama serve' is running"
                ),
            }
            results["status"] = "degraded"
    except Exception as exc:
        results["services"]["llm"] = {"status": "unhealthy", "provider": provider, "error": str(exc)}
        results["status"] = "degraded"

    http_status = 200 if results["status"] == "healthy" else 503
    return jsonify(results), http_status


@health_bp.get("/health/ping")
def ping():
    """Lightweight liveness probe — just returns pong."""
    return jsonify({"status": "ok", "message": "pong"}), 200

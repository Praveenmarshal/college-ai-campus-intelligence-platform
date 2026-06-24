"""
services/query_router.py
Phase 7 — Smart Query Router.

Classifies an incoming query's intent and routes it to the correct agent
(or combination of agents for hybrid responses). Uses a fast keyword/embedding
classifier first; falls back to an LLM classification call for ambiguous queries.
"""

import logging
import re
from typing import Optional

from agents.orchestrator import AgentOrchestrator
from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

# ── Keyword signatures per route ───────────────────────────
ROUTE_KEYWORDS = {
    "document_agent": [
        "document", "pdf", "syllabus", "policy", "brochure", "uploaded",
        "according to", "in the file", "circular", "notice", "calendar",
        "holiday", "vacation", "reopen", "midterm", "exam date", "holidays"
    ],
    "placement_agent": [
        "placement", "package", "recruiter", "company", "package", "ctc",
        "offer", "lpa", "job", "hire", "hiring",
    ],
    "academic_agent": [
        "cgpa", "gpa", "grade", "result", "marks", "exam", "semester result",
        "academic performance", "top performer",
    ],
    "prediction_agent": [
        "predict", "forecast", "risk", "likely", "chance of", "will fail",
        "at risk", "probability",
    ],
    "library_agent": [
        "book", "library", "borrow", "isbn", "author", "fine", "due date for book",
    ],
    "hostel_agent": [
        "hostel", "room", "block", "warden", "vacancy", "roommate",
    ],
    "event_agent": [
        "event", "fest", "seminar", "workshop", "registration", "competition",
    ],
    "resume_agent": [
        "resume", "cv", "ats score", "skill gap", "job match",
    ],
    "analytics_agent": [
        "attendance", "how many", "average", "count", "total", "statistics",
        "trend", "department", "students in",
    ],
    "general_agent": [
        "hello", "hi", "hey", "who are you", "what can you do", "help",
        "write", "explain", "code", "general", "tell me about"
    ],
    "timetable_agent": [
        "timetable", "schedule", "class", "lecture", "period", "teach",
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        "tomorrow", "today", "slot"
    ],
}

CLASSIFY_SYSTEM_PROMPT = """You are an intent classifier for a campus AI platform. \
Given a user question, respond with ONLY the name of the best-matching agent from this list:
document_agent, analytics_agent, placement_agent, academic_agent, prediction_agent, \
library_agent, hostel_agent, event_agent, resume_agent, general_agent, timetable_agent

Respond with ONLY the agent name, nothing else."""

VALID_AGENTS = set(ROUTE_KEYWORDS.keys())


class QueryRouter:
    """Classifies query intent and dispatches to the appropriate agent(s)."""

    @staticmethod
    def classify_keyword(query: str) -> tuple[Optional[str], float]:
        """
        Fast keyword-based classification.
        Returns (agent_name, confidence) — confidence is keyword match ratio.
        """
        q_lower = query.lower()
        scores = {}

        for agent, keywords in ROUTE_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in q_lower)
            if matches > 0:
                scores[agent] = matches

        if not scores:
            return None, 0.0

        best_agent = max(scores, key=scores.get)
        confidence = min(scores[best_agent] / 3, 1.0)  # normalise — 3+ matches = full confidence
        return best_agent, confidence

    @staticmethod
    def classify_llm(query: str) -> str:
        """LLM-based classification fallback for ambiguous queries."""
        try:
            response = gemini_service.generate(
                prompt=query,
                system_instruction=CLASSIFY_SYSTEM_PROMPT,
            )
            agent_name = response.strip().lower()
            # Extract a valid agent name even if LLM adds extra text
            for valid in VALID_AGENTS:
                if valid in agent_name:
                    return valid
        except Exception as exc:
            logger.warning("LLM classification unavailable: %s", exc)

        return "general_agent"  # safe default — falls back to general chat

    @classmethod
    def classify(cls, query: str, confidence_threshold: float = 0.4) -> dict:
        """
        Classify a query's intent.
        Tries keyword matching first (fast, free); falls back to LLM if uncertain.

        Returns: { agent, confidence, method }
        """
        agent, confidence = cls.classify_keyword(query)

        if agent and confidence >= confidence_threshold:
            return {"agent": agent, "confidence": confidence, "method": "keyword"}

        # Fall back to LLM classification
        agent = cls.classify_llm(query)
        return {"agent": agent, "confidence": 0.6, "method": "llm"}

    @classmethod
    def route(cls, query: str, context: Optional[dict] = None) -> dict:
        """
        Full pipeline: classify → dispatch → return agent response with routing metadata.
        """
        classification = cls.classify(query)
        agent_name = classification["agent"]

        logger.info(
            "Routed query to '%s' (confidence=%.2f, method=%s)",
            agent_name, classification["confidence"], classification["method"],
        )

        result = AgentOrchestrator.dispatch(agent_name, query, context)
        result["routing"] = classification
        return result

    @classmethod
    def route_hybrid(cls, query: str, context: Optional[dict] = None, max_agents: int = 2) -> dict:
        """
        Hybrid response: when a query may need multiple data sources,
        dispatch to the top N candidate agents and combine their answers.
        """
        q_lower = query.lower()
        scores = {
            agent: sum(1 for kw in kws if kw in q_lower)
            for agent, kws in ROUTE_KEYWORDS.items()
        }
        candidates = sorted(
            [(a, s) for a, s in scores.items() if s > 0],
            key=lambda x: x[1], reverse=True
        )[:max_agents]

        if not candidates:
            return cls.route(query, context)

        if len(candidates) == 1:
            return cls.route(query, context)

        # Multiple agents — combine
        responses = []
        all_sources = []
        for agent_name, _ in candidates:
            res = AgentOrchestrator.dispatch(agent_name, query, context)
            responses.append(f"[{agent_name}]: {res['answer']}")
            all_sources.extend(res.get("sources", []))

        combined_answer = "\n\n".join(responses)
        return {
            "answer": combined_answer,
            "sources": all_sources,
            "agent": "hybrid",
            "data": {"agents_used": [a for a, _ in candidates]},
            "routing": {"agent": "hybrid", "candidates": [a for a, _ in candidates], "method": "hybrid"},
        }

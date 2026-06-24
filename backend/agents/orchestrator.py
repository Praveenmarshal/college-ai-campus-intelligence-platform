"""
agents/orchestrator.py
Central registry and dispatcher for all specialised AI agents.
The Smart Query Router (services/query_router.py) decides WHICH agent to call;
this module is responsible for actually instantiating and invoking them.
"""

import logging
from typing import Optional

from agents.document_agent import DocumentAgent
from agents.analytics_agent import AnalyticsAgent
from agents.placement_agent import PlacementAgent
from agents.academic_agent import AcademicAgent
from agents.prediction_agent import PredictionAgent
from agents.library_agent import LibraryAgent
from agents.hostel_agent import HostelAgent
from agents.event_agent import EventAgent
from agents.resume_agent import ResumeAgent
from agents.general_agent import GeneralAgent
from agents.timetable_agent import TimetableAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Singleton-style registry of all agents.
    Lazily instantiates each agent on first use to avoid unnecessary startup cost
    (e.g. DocumentAgent loads the embedding model).
    """

    _agents: dict = {}

    _AGENT_CLASSES = {
        "document_agent":   DocumentAgent,
        "analytics_agent":  AnalyticsAgent,
        "placement_agent":  PlacementAgent,
        "academic_agent":   AcademicAgent,
        "prediction_agent": PredictionAgent,
        "library_agent":    LibraryAgent,
        "hostel_agent":     HostelAgent,
        "event_agent":      EventAgent,
        "resume_agent":     ResumeAgent,
        "general_agent":    GeneralAgent,
        "timetable_agent":  TimetableAgent,
    }

    @classmethod
    def get_agent(cls, agent_name: str):
        """Lazily instantiate and cache an agent by name."""
        if agent_name not in cls._AGENT_CLASSES:
            raise ValueError(f"Unknown agent: '{agent_name}'. Available: {list(cls._AGENT_CLASSES.keys())}")

        if agent_name not in cls._agents:
            logger.info("Instantiating agent: %s", agent_name)
            cls._agents[agent_name] = cls._AGENT_CLASSES[agent_name]()

        return cls._agents[agent_name]

    @classmethod
    def dispatch(cls, agent_name: str, query: str, context: Optional[dict] = None) -> dict:
        """Route a query to the named agent and return its response."""
        try:
            agent = cls.get_agent(agent_name)
            return agent.handle(query, context)
        except ValueError as exc:
            logger.error("Agent dispatch failed: %s", exc)
            return {
                "answer": f"I couldn't process that request: {exc}",
                "sources": [],
                "agent": "orchestrator",
                "data": None,
                "error": str(exc),
            }
        except Exception as exc:
            logger.exception("Agent '%s' raised an unexpected error", agent_name)
            return {
                "answer": "Something went wrong while processing your request. Please try again.",
                "sources": [],
                "agent": agent_name,
                "data": None,
                "error": str(exc),
            }

    @classmethod
    def list_agents(cls) -> list[dict]:
        """Return metadata about all available agents (for admin/debug UI)."""
        return [
            {"name": name, "description": agent_cls.description}
            for name, agent_cls in cls._AGENT_CLASSES.items()
        ]

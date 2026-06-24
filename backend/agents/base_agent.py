"""
agents/base_agent.py
Abstract base class for all specialised AI agents.
Each agent implements `handle(query, context)` and returns a standard response shape.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    All agents must implement `handle()`.
    Response shape:
        {
          "answer": str,
          "sources": list,
          "agent": str,         # this agent's name
          "data": dict | None,  # optional structured data (charts, tables)
        }
    """

    name: str = "base_agent"
    description: str = "Base agent — should not be used directly"

    @abstractmethod
    def handle(self, query: str, context: Optional[dict] = None) -> dict:
        """Process a query and return a structured response."""
        raise NotImplementedError

    def _response(self, answer: str, sources: list = None, data: dict = None) -> dict:
        return {
            "answer": answer,
            "sources": sources or [],
            "agent": self.name,
            "data": data,
        }

    def _error_response(self, message: str) -> dict:
        return {
            "answer": f"I encountered an issue: {message}",
            "sources": [],
            "agent": self.name,
            "data": None,
            "error": message,
        }

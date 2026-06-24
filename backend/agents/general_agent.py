"""
agents/general_agent.py
Handles general conversation and campus questions using Google Gemini.
"""
import logging
from typing import Optional

from agents.base_agent import BaseAgent
from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class GeneralAgent(BaseAgent):
    name = "general_agent"
    description = "Handles general conversation and campus questions"

    def handle(self, query: str, context: Optional[dict] = None) -> dict:
        try:
            history = (context or {}).get("chat_history", [])

            messages = []
            for msg in history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            messages.append({"role": "user", "content": query})

            system_prompt = (
                "You are an AI assistant for a campus intelligence platform. "
                "Answer the user's question clearly, concisely, and helpfully. "
                "You can help with general questions about college life, academics, placements, "
                "library, hostel, events, and more."
            )

            answer = gemini_service.chat(messages=messages, system_instruction=system_prompt)
            return self._response(answer=answer)
        except Exception as exc:
            logger.exception("GeneralAgent failed")
            return self._error_response(str(exc))

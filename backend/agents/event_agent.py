"""
agents/event_agent.py
Handles campus event questions using Google Gemini.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from agents.base_agent import BaseAgent
from config.database import get_db
from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class EventAgent(BaseAgent):
    name = "event_agent"
    description = "Answers questions about campus events and registrations"

    def handle(self, query: str, context: Optional[dict] = None) -> dict:
        try:
            db = get_db()
            events = list(db.events.find({}))

            if not events:
                return self._response(
                    answer="No campus events data is available yet. Please upload events.xlsx via Admin → Upload Excel."
                )

            events_str = ""
            for e in events:
                title = e.get("title", "")
                event_type = e.get("event_type", "Cultural")
                venue = e.get("venue", "Auditorium")
                dept = e.get("department", "General")
                raw_date = e.get("event_date")
                date_str = raw_date.strftime("%Y-%m-%d") if isinstance(raw_date, datetime) else str(raw_date)
                events_str += f"- {title}, Type: {event_type}, Date: {date_str}, Venue: {venue}, Dept: {dept}\n"

            now = datetime.now(timezone.utc)
            upcoming = []
            for e in events:
                raw_date = e.get("event_date")
                if raw_date and hasattr(raw_date, "tzinfo") and raw_date.tzinfo is None:
                    raw_date = raw_date.replace(tzinfo=timezone.utc)
                if raw_date and raw_date >= now:
                    e_copy = dict(e)
                    e_copy["_id"] = str(e_copy["_id"])
                    e_copy["event_date"] = raw_date.isoformat()
                    upcoming.append(e_copy)
            upcoming.sort(key=lambda x: x["event_date"])
            upcoming = upcoming[:10]

            prompt = (
                "You are a campus event coordinator assistant.\n\n"
                f"EVENTS DATABASE:\n{events_str}\n\n"
                f"QUESTION: {query}\n\n"
                "Provide a polite and concise response. List upcoming events clearly if requested."
            )

            answer = gemini_service.generate(
                prompt=prompt,
                system_instruction="You are a campus event coordinator assistant.",
            )
            return self._response(answer=answer, data={"upcoming_events": upcoming})
        except Exception as exc:
            logger.exception("EventAgent failed")
            return self._error_response(str(exc))

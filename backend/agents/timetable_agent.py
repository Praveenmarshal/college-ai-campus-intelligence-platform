"""
agents/timetable_agent.py
Handles timetable and scheduling queries using Google Gemini.
"""
import logging
from datetime import datetime
from typing import Optional

from agents.base_agent import BaseAgent
from config.database import get_db
from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class TimetableAgent(BaseAgent):
    name = "timetable_agent"
    description = "Answers timetable and class scheduling questions"

    def handle(self, query: str, context: Optional[dict] = None) -> dict:
        try:
            db = get_db()
            timetable = list(db.timetable.find({}))

            if not timetable:
                return self._response(
                    answer="No timetable data has been uploaded yet. Please ask an administrator to upload timetable.xlsx via Admin → Upload Excel."
                )

            slots_str = ""
            for entry in timetable:
                day = entry.get("day", "")
                period = entry.get("period", "")
                subject = entry.get("subject", "")
                time_val = entry.get("time", "")
                dept = entry.get("department", "")
                faculty = entry.get("faculty_name", "")

                slots_str += f"- {day}, Period {period}: {subject}"
                if time_val:
                    slots_str += f" ({time_val})"
                if dept:
                    slots_str += f", Dept: {dept}"
                if faculty:
                    slots_str += f", Teacher: {faculty}"
                slots_str += "\n"

            days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            today_day = days_of_week[datetime.today().weekday()]

            prompt = (
                f"Today is {today_day}.\n\n"
                f"TIMETABLE:\n{slots_str}\n\n"
                f"QUESTION: {query}\n\n"
                "Provide a clear, helpful, and concise response. Format the schedule neatly."
            )

            answer = gemini_service.generate(
                prompt=prompt,
                system_instruction="You are a helpful university timetable assistant.",
            )
            return self._response(answer=answer, data={"timetable_slots_count": len(timetable)})
        except Exception as exc:
            logger.exception("TimetableAgent failed")
            return self._error_response(str(exc))

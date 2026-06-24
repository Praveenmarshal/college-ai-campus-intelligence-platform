"""
agents/hostel_agent.py
Handles hostel questions: room allocation, vacancy — using Google Gemini.
"""
import logging
from typing import Optional

from agents.base_agent import BaseAgent
from config.database import get_db
from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class HostelAgent(BaseAgent):
    name = "hostel_agent"
    description = "Answers hostel room allocation and vacancy questions"

    def handle(self, query: str, context: Optional[dict] = None) -> dict:
        try:
            db = get_db()
            rooms = list(db.hostel.find({}))

            if not rooms:
                return self._response(
                    answer="No hostel room data is available yet. Please upload hostel.xlsx via Admin → Upload Excel."
                )

            rooms_str = ""
            for r in rooms:
                room_number = r.get("room_number", "")
                block = r.get("block", "")
                room_type = r.get("room_type", "Double")
                student_id = r.get("student_id", "")
                status = "Occupied" if student_id else "Vacant"
                payment = r.get("payment_status", "")

                rooms_str += f"- Room {room_number}, Block {block}, Type: {room_type}, Status: {status}"
                if student_id:
                    rooms_str += f" (Occupant: {student_id}, Payment: {payment})"
                rooms_str += "\n"

            pipeline = [
                {"$group": {
                    "_id": "$block",
                    "total": {"$sum": 1},
                    "occupied": {"$sum": {"$cond": [{"$ne": ["$student_id", ""]}, 1, 0]}}
                }}
            ]
            block_stats = list(db.hostel.aggregate(pipeline))
            stats_str = "\nSummary stats by block:\n"
            for b in block_stats:
                vacancies = b["total"] - b["occupied"]
                stats_str += f"- Block {b['_id']}: Total: {b['total']}, Occupied: {b['occupied']}, Vacant: {vacancies}\n"

            prompt = (
                f"You are a university hostel administrator assistant.\n\n"
                f"HOSTEL DATABASE:\n{rooms_str}{stats_str}\n\n"
                f"QUESTION: {query}\n\n"
                "Provide a polite, professional, and concise answer. "
                "Calculate occupancy percentages or vacant counts if requested."
            )

            answer = gemini_service.generate(
                prompt=prompt,
                system_instruction="You are a university hostel administrator assistant.",
            )

            formatted_stats = [
                {"block": b["_id"], "total": b["total"], "occupied": b["occupied"]}
                for b in block_stats
            ]
            return self._response(answer=answer, data={"block_stats": formatted_stats})
        except Exception as exc:
            logger.exception("HostelAgent failed")
            return self._error_response(str(exc))

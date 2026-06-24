"""
agents/academic_agent.py
Handles academic questions: CGPA, results — using Google Gemini.
"""
import logging
from typing import Optional

from agents.base_agent import BaseAgent
from config.database import get_db
from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class AcademicAgent(BaseAgent):
    name = "academic_agent"
    description = "Answers academic performance, CGPA, and results questions"

    def handle(self, query: str, context: Optional[dict] = None) -> dict:
        try:
            db = get_db()
            pipeline = [
                {"$group": {
                    "_id": "$department",
                    "avg_cgpa": {"$avg": "$cgpa"},
                    "count": {"$sum": 1},
                }},
                {"$sort": {"avg_cgpa": -1}},
            ]
            dept_stats = list(db.students.aggregate(pipeline))

            top_performers = list(
                db.students.find({}, {"name": 1, "student_id": 1, "cgpa": 1, "department": 1})
                .sort("cgpa", -1).limit(5)
            )
            for s in top_performers:
                s["_id"] = str(s["_id"])

            stats_str = "Department-wise average CGPA:\n"
            for d in dept_stats:
                stats_str += f"- {d['_id']}: {round(d.get('avg_cgpa') or 0, 2)} (n={d['count']})\n"

            top_str = "Top 5 performers:\n"
            for s in top_performers:
                top_str += f"- {s.get('name', 'Unknown')} ({s.get('department', '')}): CGPA {s.get('cgpa', 'N/A')}\n"

            prompt = (
                f"Academic performance data:\n{stats_str}\n{top_str}\n\n"
                f"Question: {query}\n\nAnswer concisely using this data."
            )

            try:
                answer = gemini_service.generate(prompt=prompt)
            except Exception:
                answer = stats_str

            return self._response(answer=answer, data={"department_stats": dept_stats, "top_performers": top_performers})
        except Exception as exc:
            logger.exception("AcademicAgent failed")
            return self._error_response(str(exc))

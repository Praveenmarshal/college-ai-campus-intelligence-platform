"""
agents/placement_agent.py
Handles placement questions: trends, packages, recruiters — using Google Gemini.
"""
import logging
from typing import Optional

from agents.base_agent import BaseAgent
from config.database import get_db
from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class PlacementAgent(BaseAgent):
    name = "placement_agent"
    description = "Answers placement statistics, package, and recruiter questions"

    def handle(self, query: str, context: Optional[dict] = None) -> dict:
        try:
            db = get_db()
            pipeline = [
                {"$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "placed": {"$sum": {"$cond": [{"$eq": ["$status", "placed"]}, 1, 0]}},
                    "avg_package": {"$avg": "$package_lpa"},
                    "max_package": {"$max": "$package_lpa"},
                }}
            ]
            stats = list(db.placements.aggregate(pipeline))
            stats = stats[0] if stats else {"total": 0, "placed": 0, "avg_package": 0, "max_package": 0}
            stats.pop("_id", None)

            top_recruiters = list(db.placements.aggregate([
                {"$group": {"_id": "$company_name", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}, {"$limit": 5},
            ]))

            context_str = (
                f"Total students: {stats.get('total', 0)}, "
                f"Placed: {stats.get('placed', 0)}, "
                f"Avg package: {round(stats.get('avg_package') or 0, 2)} LPA, "
                f"Highest package: {round(stats.get('max_package') or 0, 2)} LPA. "
                f"Top recruiters: {[r['_id'] for r in top_recruiters]}"
            )

            prompt = f"Placement data: {context_str}\n\nQuestion: {query}\n\nAnswer concisely using this data."
            try:
                answer = gemini_service.generate(prompt=prompt)
            except Exception:
                answer = context_str

            return self._response(answer=answer, data={"stats": stats, "top_recruiters": top_recruiters})
        except Exception as exc:
            logger.exception("PlacementAgent failed")
            return self._error_response(str(exc))

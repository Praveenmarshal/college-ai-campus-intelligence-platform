"""
agents/analytics_agent.py
Handles general analytics questions via MongoDB NL query engine + Gemini summarization.
"""
import logging
from typing import Optional

from agents.base_agent import BaseAgent
from services.mongo_query_service import MongoQueryEngine
from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

COLLECTION_KEYWORDS = {
    "attendance": ["attendance", "absent", "present", "class"],
    "students":   ["student", "cgpa", "department", "batch", "semester"],
    "fees":       ["fee", "payment", "due", "paid"],
    "events":     ["event", "fest", "seminar", "workshop"],
    "library":    ["library", "book", "borrow"],
    "hostel":     ["hostel", "room", "block"],
}


class AnalyticsAgent(BaseAgent):
    name = "analytics_agent"
    description = "Answers general analytics questions using MongoDB data"

    def _guess_collection(self, query: str) -> str:
        q_lower = query.lower()
        scores = {
            coll: sum(1 for kw in kws if kw in q_lower)
            for coll, kws in COLLECTION_KEYWORDS.items()
        }
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "students"

    def handle(self, query: str, context: Optional[dict] = None) -> dict:
        collection = (context or {}).get("collection") or self._guess_collection(query)

        try:
            result = MongoQueryEngine.query(query, collection)

            summary_prompt = (
                f"Question: {query}\n"
                f"Query results ({result['result_count']} records): {result['results'][:10]}\n\n"
                "Summarise these results in 2-3 clear sentences for the user."
            )
            try:
                answer = gemini_service.generate(prompt=summary_prompt)
            except Exception:
                answer = f"Found {result['result_count']} matching record(s) in {collection}."

            return self._response(
                answer=answer,
                data={
                    "collection": result["collection"],
                    "results": result["results"],
                    "result_count": result["result_count"],
                },
            )
        except (ValueError, RuntimeError) as exc:
            logger.warning("AnalyticsAgent query failed: %s", exc)
            return self._error_response(str(exc))

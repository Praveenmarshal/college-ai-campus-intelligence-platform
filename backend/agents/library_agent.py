"""
agents/library_agent.py
Handles library questions using Google Gemini.
"""
import logging
from typing import Optional

from agents.base_agent import BaseAgent
from config.database import get_db
from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class LibraryAgent(BaseAgent):
    name = "library_agent"
    description = "Answers library book search, availability, and fine questions"

    def handle(self, query: str, context: Optional[dict] = None) -> dict:
        try:
            db = get_db()
            books = list(db.library.find({}))

            if not books:
                return self._response(
                    answer="No library catalog data is available yet. Please upload library.xlsx via Admin → Upload Excel."
                )

            catalog_str = ""
            for b in books:
                avail = b.get("available_copies", 1)
                total = b.get("total_copies", 1)
                catalog_str += (
                    f"- \"{b.get('title', '')}\", Author: {b.get('author', '')}, "
                    f"ISBN: {b.get('isbn', '')}, Category: {b.get('category', '')}, "
                    f"Copies: {avail}/{total}, Status: {b.get('status', 'available')}"
                )
                if b.get("due_date"):
                    catalog_str += f", Due: {b['due_date']}"
                catalog_str += "\n"

            prompt = (
                "You are a helpful university library assistant.\n\n"
                f"LIBRARY CATALOG:\n{catalog_str}\n\n"
                f"QUESTION: {query}\n\n"
                "Provide a polite, accurate, and concise answer. "
                "If a book is available, say so. If borrowed, mention the due date if available."
            )

            answer = gemini_service.generate(
                prompt=prompt,
                system_instruction="You are a helpful university library assistant.",
            )

            q_lower = query.lower()
            matching_books = []
            for b in books:
                if q_lower in b.get("title", "").lower() or q_lower in b.get("author", "").lower():
                    b_copy = dict(b)
                    b_copy["_id"] = str(b_copy["_id"])
                    matching_books.append(b_copy)

            return self._response(answer=answer, data={"books": matching_books})
        except Exception as exc:
            logger.exception("LibraryAgent failed")
            return self._error_response(str(exc))

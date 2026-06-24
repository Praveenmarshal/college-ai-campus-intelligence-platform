"""
agents/document_agent.py
Handles questions about uploaded documents (PDFs) via the RAG pipeline.
"""

import logging
from typing import Optional

from agents.base_agent import BaseAgent
from rag.rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)


class DocumentAgent(BaseAgent):
    name = "document_agent"
    description = "Answers questions about uploaded PDFs and documents using RAG"

    def __init__(self):
        self.pipeline = RAGPipeline(collection_name="campus_docs", top_k=5)

    def handle(self, query: str, context: Optional[dict] = None) -> dict:
        try:
            history = (context or {}).get("chat_history", [])
            result = self.pipeline.answer(query, chat_history=history)
            return self._response(
                answer=result["answer"],
                sources=result.get("sources", []),
                data={"context_used": result.get("context_used", False)},
            )
        except Exception as exc:
            logger.exception("DocumentAgent failed")
            return self._error_response(str(exc))

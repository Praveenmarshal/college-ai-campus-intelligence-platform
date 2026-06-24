"""
rag/rag_pipeline.py
Orchestrates the full RAG flow: query → embed → retrieve → prompt → Gemini → cited answer.
"""

import logging
from typing import Optional

from rag.embedder import embed_text
from rag.vector_store import VectorStore
from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """You are an AI assistant for a college campus platform. \
Answer the user's question using ONLY the provided context excerpts below. \
If the context doesn't contain enough information to answer, say so honestly — \
do not make up information. Always cite which source(s) you used by referencing \
the filename in brackets, e.g. [syllabus.pdf]. Keep answers clear and concise."""


class RAGPipeline:
    """End-to-end Retrieval-Augmented Generation pipeline."""

    def __init__(self, collection_name: str = "campus_docs", top_k: int = 5):
        self.store = VectorStore(collection_name)
        self.top_k = top_k

    def retrieve(self, query: str, top_k: Optional[int] = None, where: Optional[dict] = None) -> list[dict]:
        """Embed the query and retrieve the most relevant chunks."""
        query_vec = embed_text(query)
        hits = self.store.query(query_vec, top_k=top_k or self.top_k, where=where)
        return hits

    def build_context(self, hits: list[dict]) -> str:
        """Format retrieved chunks into a context block for the LLM prompt."""
        if not hits:
            return "No relevant documents found."

        blocks = []
        for h in hits:
            filename = h["metadata"].get("filename", "unknown")
            blocks.append(f"[Source: {filename}]\n{h['text']}")
        return "\n\n---\n\n".join(blocks)

    def answer(
        self,
        query: str,
        chat_history: Optional[list[dict]] = None,
        top_k: Optional[int] = None,
        where: Optional[dict] = None,
    ) -> dict:
        """
        Full RAG answer generation.

        Returns:
            {
              answer: str,
              sources: [{ filename, chunk_index, score }],
              context_used: bool
            }
        """
        hits = self.retrieve(query, top_k=top_k, where=where)
        context = self.build_context(hits)

        # Build the full prompt including chat history context
        history_text = ""
        if chat_history:
            for msg in chat_history[-4:]:  # last 4 messages for context
                role = msg.get("role", "user").capitalize()
                history_text += f"{role}: {msg.get('content', '')}\n"

        full_prompt = (
            f"{history_text}\n" if history_text else ""
        ) + (
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Answer based on the context above. Cite sources in [brackets]."
        )

        try:
            response_text = gemini_service.generate(
                prompt=full_prompt,
                system_instruction=RAG_SYSTEM_PROMPT,
            )
        except RuntimeError as exc:
            logger.error("RAG generation failed: %s", exc)
            return {
                "answer": (
                    "I'm unable to reach the AI model right now. "
                    "Please ensure GEMINI_API_KEY is set correctly and try again."
                ),
                "sources": [],
                "context_used": False,
                "error": str(exc),
            }

        sources = [
            {
                "filename":    h["metadata"].get("filename", "unknown"),
                "chunk_index": h["metadata"].get("chunk_index", 0),
                "score":       h["score"],
            }
            for h in hits
        ]

        return {
            "answer": response_text,
            "sources": sources,
            "context_used": len(hits) > 0,
        }

    def stream_answer(self, query: str, chat_history: Optional[list[dict]] = None, top_k: Optional[int] = None):
        """Streaming variant — yields text chunks, then a final sources event.
        Since Gemini REST doesn't support true streaming, returns the full answer as one chunk."""
        result = self.answer(query, chat_history=chat_history, top_k=top_k)
        yield {"type": "token", "content": result["answer"]}
        yield {"type": "done", "sources": result.get("sources", [])}

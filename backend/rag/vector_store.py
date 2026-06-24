"""
rag/vector_store.py
Wraps ChromaDB operations: add, query (retrieve), delete.
Used by the PDF RAG pipeline and other agents that need semantic search.
"""

import logging
from typing import Optional

from config.chromadb_config import get_collection

logger = logging.getLogger(__name__)


class VectorStore:
    """High-level interface over a ChromaDB collection."""

    def __init__(self, collection_name: str = "campus_docs"):
        self.collection_name = collection_name

    @property
    def collection(self):
        return get_collection(self.collection_name)

    # ── Add ─────────────────────────────────────────────────
    def add_chunks(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> int:
        """
        Add embedded chunks to the vector store.
        Returns the number of chunks added.
        """
        if not ids:
            return 0

        # ChromaDB metadata values must be str/int/float/bool — sanitise
        clean_meta = [
            {k: (v if isinstance(v, (str, int, float, bool)) else str(v)) for k, v in m.items()}
            for m in metadatas
        ]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=clean_meta,
        )
        logger.info("Added %d chunks to collection '%s'", len(ids), self.collection_name)
        return len(ids)

    # ── Query ───────────────────────────────────────────────
    def query(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        where: Optional[dict] = None,
    ) -> list[dict]:
        """
        Retrieve the top_k most similar chunks.

        Returns list of:
            { id, text, metadata, distance, score }
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
        )

        if not results["ids"] or not results["ids"][0]:
            return []

        hits = []
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            hits.append({
                "id":       results["ids"][0][i],
                "text":     results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": distance,
                "score":    round(1 - distance, 4),  # cosine similarity approx
            })
        return hits

    # ── Delete ──────────────────────────────────────────────
    def delete_by_doc_id(self, doc_id: str) -> None:
        """Delete all chunks belonging to a specific document."""
        try:
            self.collection.delete(where={"doc_id": doc_id})
            logger.info("Deleted chunks for doc_id=%s from '%s'", doc_id, self.collection_name)
        except Exception as exc:
            logger.warning("Delete failed for doc_id=%s: %s", doc_id, exc)

    def delete_ids(self, ids: list[str]) -> None:
        if ids:
            self.collection.delete(ids=ids)

    # ── Stats ───────────────────────────────────────────────
    def count(self) -> int:
        return self.collection.count()

    def get_by_doc_id(self, doc_id: str, limit: int = 1000) -> list[dict]:
        """Fetch all chunks for a given document (for re-display / debugging)."""
        results = self.collection.get(where={"doc_id": doc_id}, limit=limit)
        chunks = []
        for i in range(len(results["ids"])):
            chunks.append({
                "id": results["ids"][i],
                "text": results["documents"][i],
                "metadata": results["metadatas"][i],
            })
        return chunks

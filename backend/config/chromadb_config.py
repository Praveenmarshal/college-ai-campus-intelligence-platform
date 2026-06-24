"""
config/chromadb_config.py
ChromaDB vector store manager.
Handles initialisation, collection management, and health checks.
"""

import logging
from typing import Optional

import chromadb
from chromadb import Collection
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class ChromaManager:
    """Singleton ChromaDB connection and collection manager."""

    _client: Optional[chromadb.PersistentClient] = None
    _collections: dict[str, Collection] = {}

    # All named collections used across the platform
    COLLECTION_NAMES = [
        "campus_docs",        # PDF RAG documents
        "ocr_chunks",         # OCR-processed text
        "question_papers",    # Question paper analysis
        "resumes",            # Resume embeddings
        "knowledge_base",     # General campus knowledge
    ]

    @classmethod
    def init_app(cls, app) -> None:
        """
        Initialise ChromaDB from Flask app config.
        Uses persistent storage at CHROMA_PERSIST_DIR.
        """
        persist_dir = app.config.get("CHROMA_PERSIST_DIR", "./chroma_db")

        try:
            cls._client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )

            # Pre-load all collections
            for name in cls.COLLECTION_NAMES:
                cls._collections[name] = cls._client.get_or_create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info("[OK] ChromaDB collection ready: %s", name)

            logger.info("[OK] ChromaDB initialised at: %s", persist_dir)

        except Exception as exc:
            logger.error("[ERROR] ChromaDB initialisation failed: %s", exc)
            raise

    @classmethod
    def get_collection(cls, name: str = "campus_docs") -> Collection:
        """Return a named collection."""
        if name not in cls._collections:
            raise KeyError(
                f"Collection '{name}' not found. "
                f"Available: {list(cls._collections.keys())}"
            )
        return cls._collections[name]

    @classmethod
    def get_client(cls) -> chromadb.PersistentClient:
        """Return the raw ChromaDB client."""
        if cls._client is None:
            raise RuntimeError("ChromaDB not initialised. Call ChromaManager.init_app(app) first.")
        return cls._client

    @classmethod
    def reset_collection(cls, name: str) -> None:
        """Delete and recreate a collection (admin use only)."""
        if cls._client and name in cls.COLLECTION_NAMES:
            cls._client.delete_collection(name)
            cls._collections[name] = cls._client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("[RESET] ChromaDB collection reset: %s", name)

    @classmethod
    def health_check(cls) -> dict:
        """Return health status of ChromaDB."""
        try:
            total_docs = sum(
                col.count() for col in cls._collections.values()
            )
            return {
                "status": "healthy",
                "collections": {
                    name: col.count()
                    for name, col in cls._collections.items()
                },
                "total_documents": total_docs,
            }
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}


def get_collection(name: str = "campus_docs") -> Collection:
    """Convenience accessor for a ChromaDB collection."""
    return ChromaManager.get_collection(name)

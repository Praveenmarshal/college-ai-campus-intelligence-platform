"""
rag/embedder.py
Singleton embedding service using all-MiniLM-L6-v2.
Produces 384-dimensional vectors for semantic search.
"""

import logging
from typing import Union

logger = logging.getLogger(__name__)

_model = None
_model_name = "all-MiniLM-L6-v2"


def _get_model():
    """Lazy-load the embedding model (only once per process)."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model: %s …", _model_name)
            _model = SentenceTransformer(_model_name)
            logger.info("✅ Embedding model loaded")
        except Exception as exc:
            logger.error("Failed to load embedding model: %s", exc)
            raise
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a single string. Returns a list of 384 floats."""
    model = _get_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()


def embed_batch(texts: list[str], batch_size: int = 64, show_progress: bool = False) -> list[list[float]]:
    """
    Embed a list of strings in batches.
    Returns list of embedding vectors.
    """
    if not texts:
        return []
    model = _get_model()
    vecs = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=show_progress,
    )
    return [v.tolist() for v in vecs]


def embed_chunks(chunks: list[dict]) -> tuple[list[str], list[list[float]], list[dict]]:
    """
    Embed a list of chunk dicts (from PDFProcessor).

    Returns:
        ids        — list of chunk IDs for ChromaDB
        embeddings — list of embedding vectors
        metadatas  — list of metadata dicts
    """
    texts     = [c["text"] for c in chunks]
    ids       = [c["id"]   for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    logger.info("Embedding %d chunks …", len(texts))
    embeddings = embed_batch(texts)
    logger.info("✅ Embedded %d chunks", len(embeddings))

    return ids, embeddings, metadatas

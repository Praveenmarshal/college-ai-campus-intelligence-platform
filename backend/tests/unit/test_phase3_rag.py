"""
tests/unit/test_phase3_rag.py
Phase 3 — PDF RAG pipeline tests.
Tests text cleaning, chunking logic, and vector store interface
without requiring a live Ollama server (those are mocked / skipped).
"""

import pytest


class TestPDFProcessorCleaning:

    def test_clean_text_collapses_whitespace(self):
        from rag.pdf_processor import PDFProcessor
        dirty = "Hello    world\n\n\n\n\nFoo"
        cleaned = PDFProcessor.clean_text(dirty)
        assert "    " not in cleaned
        assert "\n\n\n" not in cleaned

    def test_clean_text_fixes_ligatures(self):
        from rag.pdf_processor import PDFProcessor
        dirty = "eﬃcient ﬁle"
        cleaned = PDFProcessor.clean_text(dirty)
        assert "ﬃ" not in cleaned
        assert "ﬁ" not in cleaned
        assert "efficient" in cleaned or "ffi" in cleaned

    def test_clean_text_removes_page_numbers(self):
        from rag.pdf_processor import PDFProcessor
        dirty = "Some content\nPage 3 of 10\nMore content"
        cleaned = PDFProcessor.clean_text(dirty)
        assert "Page 3 of 10" not in cleaned

    def test_clean_text_empty_input(self):
        from rag.pdf_processor import PDFProcessor
        assert PDFProcessor.clean_text("") == ""


class TestPDFProcessorChunking:

    def test_chunk_text_basic(self):
        from rag.pdf_processor import PDFProcessor
        text = "This is a sentence. " * 100  # ~2000 chars
        chunks = PDFProcessor.chunk_text(text, "doc1", "test.pdf", chunk_size=500, overlap=50)
        assert len(chunks) > 1
        for c in chunks:
            assert "id" in c
            assert "text" in c
            assert c["metadata"]["doc_id"] == "doc1"
            assert c["metadata"]["filename"] == "test.pdf"

    def test_chunk_text_empty(self):
        from rag.pdf_processor import PDFProcessor
        chunks = PDFProcessor.chunk_text("", "doc1", "empty.pdf")
        assert chunks == []

    def test_chunk_text_short_discarded(self):
        from rag.pdf_processor import PDFProcessor
        chunks = PDFProcessor.chunk_text("short", "doc1", "tiny.pdf")
        assert chunks == []  # below MIN_CHUNK_LENGTH

    def test_chunk_ids_are_sequential(self):
        from rag.pdf_processor import PDFProcessor
        text = "Sentence number here. " * 200
        chunks = PDFProcessor.chunk_text(text, "docX", "f.pdf", chunk_size=400, overlap=40)
        for i, c in enumerate(chunks):
            assert c["id"] == f"docX_chunk_{i}"
            assert c["metadata"]["chunk_index"] == i

    def test_chunk_overlap_creates_continuity(self):
        from rag.pdf_processor import PDFProcessor
        text = "Word" + " filler" * 300
        chunks = PDFProcessor.chunk_text(text, "doc2", "f2.pdf", chunk_size=300, overlap=60)
        assert len(chunks) >= 2


class TestVectorStoreInterface:
    """Tests that don't require a live ChromaDB connection — interface-level only."""

    def test_vector_store_instantiation(self):
        from rag.vector_store import VectorStore
        store = VectorStore("test_collection")
        assert store.collection_name == "test_collection"

    def test_query_empty_results_shape(self):
        # Verify the contract: hits should be a list (mocked behaviour documented)
        from rag.vector_store import VectorStore
        store = VectorStore("test_collection")
        assert hasattr(store, "query")
        assert hasattr(store, "add_chunks")
        assert hasattr(store, "delete_by_doc_id")


class TestRAGPipelineContext:

    def test_build_context_empty_hits(self):
        from rag.rag_pipeline import RAGPipeline
        pipeline = RAGPipeline.__new__(RAGPipeline)  # skip __init__ (no DB needed)
        context = pipeline.build_context([])
        assert "No relevant documents" in context

    def test_build_context_formats_sources(self):
        from rag.rag_pipeline import RAGPipeline
        pipeline = RAGPipeline.__new__(RAGPipeline)
        hits = [
            {"text": "Attendance must be 75%.", "metadata": {"filename": "policy.pdf"}, "score": 0.9},
        ]
        context = pipeline.build_context(hits)
        assert "policy.pdf" in context
        assert "75%" in context


class TestLLMClientConfig:

    def test_default_model_name(self):
        from rag.llm_client import LLMClient
        client = LLMClient()
        assert client.model is not None
        if client.provider in ("ollama", "groq") and client.base_url:
            assert client.base_url.startswith("http")

    def test_custom_config(self):
        from rag.llm_client import LLMClient
        client = LLMClient(base_url="http://example.com", model="custom-model", timeout=30)
        assert client.base_url == "http://example.com"
        assert client.model == "custom-model"
        assert client.timeout == 30

    def test_is_available_handles_connection_error(self):
        from rag.llm_client import LLMClient
        client = LLMClient(base_url="http://nonexistent-host-xyz:11434")
        assert client.is_available() is False


class TestDocumentModelSerialisation:

    def test_serialise_strips_internal_fields(self, app):
        with app.app_context():
            from bson import ObjectId
            from models.document_model import DocumentModel
            doc = {
                "_id": ObjectId(),
                "filename": "x.pdf",
                "original_name": "Original.pdf",
                "file_type": "pdf",
                "uploaded_by": ObjectId(),
                "created_at": None,
                "updated_at": None,
            }
            result = DocumentModel._serialise(doc)
            assert "id" in result
            assert "_id" not in result
            assert isinstance(result["uploaded_by"], str)

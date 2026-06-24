"""
rag/pdf_processor.py
PDF text extraction, cleaning, and chunking pipeline.
Supports text-based PDFs and triggers OCR fallback for scanned pages.
"""

import logging
import re
import uuid
from pathlib import Path
from typing import Generator

import pdfplumber
from pypdf import PdfReader

logger = logging.getLogger(__name__)

# Chunking parameters
DEFAULT_CHUNK_SIZE    = 800   # characters
DEFAULT_CHUNK_OVERLAP = 150   # characters overlap between chunks
MIN_CHUNK_LENGTH      = 50    # discard chunks shorter than this


class PDFProcessor:
    """Extract, clean, and chunk text from PDF files."""

    # ── Extraction ──────────────────────────────────────────
    @staticmethod
    def extract_text(file_path: str | Path) -> tuple[str, int]:
        """
        Extract full text from a PDF using pdfplumber (primary)
        with pypdf as fallback.

        Returns:
            (full_text, page_count)
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        text_pages = []
        page_count = 0

        # ── Primary: pdfplumber ──────────────────────────
        try:
            with pdfplumber.open(path) as pdf:
                page_count = len(pdf.pages)
                for i, page in enumerate(pdf.pages):
                    raw = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
                    if raw.strip():
                        text_pages.append(f"[Page {i + 1}]\n{raw}")
                    else:
                        logger.debug("Page %d: no text extracted (may be scanned)", i + 1)
        except Exception as exc:
            logger.warning("pdfplumber failed (%s); falling back to pypdf", exc)
            text_pages = []

        # ── Fallback: pypdf ──────────────────────────────
        if not any(t.strip() for t in text_pages):
            try:
                reader = PdfReader(str(path))
                page_count = len(reader.pages)
                for i, page in enumerate(reader.pages):
                    raw = page.extract_text() or ""
                    if raw.strip():
                        text_pages.append(f"[Page {i + 1}]\n{raw}")
            except Exception as exc:
                logger.error("pypdf also failed: %s", exc)
                raise RuntimeError(f"Could not extract text from PDF: {exc}") from exc

        full_text = "\n\n".join(text_pages)
        logger.info("Extracted %d chars from %d pages (%s)", len(full_text), page_count, path.name)
        return full_text, page_count

    # ── Cleaning ────────────────────────────────────────────
    @staticmethod
    def clean_text(raw: str) -> str:
        """Remove noise: headers, footers, excessive whitespace, ligatures."""
        text = raw

        # Fix common ligature artifacts
        ligatures = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}
        for lig, rep in ligatures.items():
            text = text.replace(lig, rep)

        # Collapse multiple spaces
        text = re.sub(r"[ \t]+", " ", text)

        # Collapse 3+ newlines to 2
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove standalone page numbers like "- 3 -" or "Page 3 of 10"
        text = re.sub(r"(?i)\bpage\s+\d+\s+(of\s+\d+)?\b", "", text)
        text = re.sub(r"^\s*[-–]\s*\d+\s*[-–]\s*$", "", text, flags=re.MULTILINE)

        # Strip lines that are just punctuation/whitespace
        lines = [ln for ln in text.splitlines() if ln.strip() and not re.match(r"^[\s\W]+$", ln)]
        return "\n".join(lines).strip()

    # ── Chunking ────────────────────────────────────────────
    @classmethod
    def chunk_text(
        cls,
        text: str,
        doc_id: str,
        filename: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> list[dict]:
        """
        Split text into overlapping chunks suitable for embedding.

        Returns list of chunk dicts:
            { id, text, metadata: { doc_id, filename, chunk_index, char_start } }
        """
        chunks = []
        text = cls.clean_text(text)
        length = len(text)

        if length == 0:
            logger.warning("Empty text — no chunks produced for %s", filename)
            return []

        # Prefer sentence boundaries for splits
        start = 0
        chunk_index = 0

        while start < length:
            end = min(start + chunk_size, length)

            # Try to end on a sentence boundary if not at EOF
            if end < length:
                # Look for ". " or "\n" within last 20% of chunk
                search_from = end - chunk_size // 5
                boundary = -1
                for pattern in [". ", ".\n", "\n\n", "\n"]:
                    pos = text.rfind(pattern, search_from, end)
                    if pos != -1:
                        boundary = pos + len(pattern)
                        break
                if boundary > start + MIN_CHUNK_LENGTH:
                    end = boundary

            chunk_text = text[start:end].strip()

            if len(chunk_text) >= MIN_CHUNK_LENGTH:
                chunks.append({
                    "id": f"{doc_id}_chunk_{chunk_index}",
                    "text": chunk_text,
                    "metadata": {
                        "doc_id":      doc_id,
                        "filename":    filename,
                        "chunk_index": chunk_index,
                        "char_start":  start,
                        "char_end":    end,
                    },
                })
                chunk_index += 1

            if end >= length:
                break
            start = end - overlap  # overlap for context continuity

        logger.info("Chunked '%s' → %d chunks", filename, len(chunks))
        return chunks

    # ── Combined pipeline ────────────────────────────────────
    @classmethod
    def process_pdf(
        cls,
        file_path: str | Path,
        doc_id: str = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap:    int = DEFAULT_CHUNK_OVERLAP,
    ) -> dict:
        """
        Full pipeline: extract → clean → chunk.

        Returns:
            {
              doc_id, filename, page_count,
              full_text, chunks: [{ id, text, metadata }]
            }
        """
        path = Path(file_path)
        doc_id = doc_id or str(uuid.uuid4())

        raw_text, page_count = cls.extract_text(path)
        chunks = cls.chunk_text(raw_text, doc_id, path.name, chunk_size, overlap)

        return {
            "doc_id":     doc_id,
            "filename":   path.name,
            "page_count": page_count,
            "full_text":  raw_text[:500],  # preview only; don't store full text
            "char_count": len(raw_text),
            "chunks":     chunks,
        }

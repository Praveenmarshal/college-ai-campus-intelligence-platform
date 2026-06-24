"""
services/ocr/ocr_processor.py
Phase 12 — OCR engine for scanned documents and images.
Primary: EasyOCR (better accuracy, GPU-capable).
Fallback: Tesseract (lighter weight, CPU-only).
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

_easyocr_reader = None


def _get_easyocr_reader():
    """Lazily load the EasyOCR reader (expensive to initialise)."""
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            logger.info("Loading EasyOCR reader (English)…")
            _easyocr_reader = easyocr.Reader(["en"], gpu=False)
            logger.info("✅ EasyOCR reader loaded")
        except Exception as exc:
            logger.warning("EasyOCR unavailable: %s", exc)
            _easyocr_reader = False  # sentinel: tried and failed
    return _easyocr_reader if _easyocr_reader is not False else None


class OCRProcessor:
    """Extract text from images and scanned PDFs."""

    # ── Image preprocessing ──────────────────────────────────
    @staticmethod
    def preprocess_image(image_path: str | Path) -> np.ndarray:
        """Basic preprocessing: grayscale + contrast enhancement for better OCR accuracy."""
        import cv2

        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Adaptive thresholding for uneven lighting (common in scanned docs)
        processed = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
        )

        # Denoise
        processed = cv2.fastNlMeansDenoising(processed, h=10)

        return processed

    # ── EasyOCR extraction ────────────────────────────────────
    @classmethod
    def extract_with_easyocr(cls, image_path: str | Path) -> dict:
        """Extract text using EasyOCR. Returns text + per-line confidence."""
        reader = _get_easyocr_reader()
        if reader is None:
            raise RuntimeError("EasyOCR is not available in this environment")

        results = reader.readtext(str(image_path))

        lines = []
        confidences = []
        for (_bbox, text, confidence) in results:
            lines.append(text)
            confidences.append(confidence)

        full_text = "\n".join(lines)
        avg_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0

        return {
            "text": full_text,
            "line_count": len(lines),
            "avg_confidence": avg_confidence,
            "engine": "easyocr",
        }

    # ── Tesseract fallback ────────────────────────────────────
    @classmethod
    def extract_with_tesseract(cls, image_path: str | Path) -> dict:
        """Extract text using pytesseract (Tesseract OCR)."""
        import pytesseract

        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)

        # Get confidence data
        try:
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            confidences = [int(c) for c in data["conf"] if c not in ("-1", -1)]
            avg_confidence = round(sum(confidences) / len(confidences) / 100, 3) if confidences else 0
        except Exception:
            avg_confidence = None

        return {
            "text": text.strip(),
            "line_count": len(text.strip().splitlines()),
            "avg_confidence": avg_confidence,
            "engine": "tesseract",
        }

    # ── Combined pipeline with automatic fallback ─────────────
    @classmethod
    def extract_text(cls, image_path: str | Path, prefer: str = None) -> dict:
        """
        Extract text from an image, trying the preferred engine first
        and falling back to the other on failure.

        If `prefer` is not given, reads OCR_ENGINE env var (defaults to
        "easyocr"). Set OCR_ENGINE=tesseract on lean deployments (e.g.
        Render free tier via requirements-render.txt) where easyocr/torch
        aren't installed, to skip the doomed-to-fail import attempt.
        """
        import os
        prefer = prefer or os.getenv("OCR_ENGINE", "easyocr")

        engines = (
            [cls.extract_with_easyocr, cls.extract_with_tesseract]
            if prefer == "easyocr"
            else [cls.extract_with_tesseract, cls.extract_with_easyocr]
        )

        last_error = None
        for engine_fn in engines:
            try:
                result = engine_fn(image_path)
                if result["text"].strip():
                    return result
            except Exception as exc:
                last_error = exc
                logger.warning("%s failed: %s", engine_fn.__name__, exc)
                continue

        raise RuntimeError(f"All OCR engines failed. Last error: {last_error}")

    # ── Scanned PDF support ───────────────────────────────────
    @classmethod
    def extract_from_scanned_pdf(cls, pdf_path: str | Path, max_pages: int = 20) -> dict:
        """
        Convert PDF pages to images and run OCR on each.
        Used when PDFProcessor.extract_text() returns empty (scanned/image-only PDF).
        """
        try:
            from pdf2image import convert_from_path
        except ImportError as exc:
            raise RuntimeError(
                "pdf2image is required for scanned PDF OCR. Install poppler-utils + pdf2image."
            ) from exc

        images = convert_from_path(str(pdf_path), dpi=200, last_page=max_pages)

        all_text = []
        total_confidence = []

        for i, image in enumerate(images):
            tmp_path = Path(f"/tmp/ocr_page_{i}.png")
            image.save(tmp_path, "PNG")
            try:
                result = cls.extract_text(tmp_path)
                all_text.append(f"[Page {i + 1}]\n{result['text']}")
                if result.get("avg_confidence"):
                    total_confidence.append(result["avg_confidence"])
            finally:
                tmp_path.unlink(missing_ok=True)

        return {
            "text": "\n\n".join(all_text),
            "page_count": len(images),
            "avg_confidence": round(sum(total_confidence) / len(total_confidence), 3) if total_confidence else None,
            "engine": "ocr_pdf_pipeline",
        }

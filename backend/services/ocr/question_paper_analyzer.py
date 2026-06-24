"""
services/ocr/question_paper_analyzer.py
Phase 12 — Question paper analysis: topic extraction, frequency analysis, trends.
Combines OCR (for scanned papers) with Qwen 3 for topic understanding.
"""

import json
import logging
import re
from collections import Counter
from pathlib import Path

from rag.pdf_processor import PDFProcessor
from services.ocr.ocr_processor import OCRProcessor
from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

TOPIC_EXTRACTION_PROMPT = """You are analysing a university question paper. Extract the key \
topics/concepts being tested. Respond with ONLY a JSON object — no markdown, no explanation.

Format:
{
  "topics": [<list of 5-15 specific topic strings, e.g. "Binary Search Trees", "Newton's Laws">],
  "question_count": <integer>,
  "subject_area": "<inferred subject, e.g. Data Structures>",
  "difficulty_level": "easy" | "medium" | "hard",
  "question_types": [<e.g. "MCQ", "Short Answer", "Long Answer", "Numerical">]
}"""


class QuestionPaperAnalyzer:
    """Analyse question papers for topic frequency and trends."""

    @staticmethod
    def extract_text(file_path: str | Path) -> str:
        """Extract text — tries direct PDF extraction first, falls back to OCR if empty."""
        path = Path(file_path)

        if path.suffix.lower() == ".pdf":
            text, _ = PDFProcessor.extract_text(path)
            text = PDFProcessor.clean_text(text)
            if text.strip():
                return text
            # Likely a scanned PDF — fall back to OCR
            logger.info("PDF appears scanned, falling back to OCR for %s", path.name)
            result = OCRProcessor.extract_from_scanned_pdf(path)
            return result["text"]
        else:
            # Image file
            result = OCRProcessor.extract_text(path)
            return result["text"]

    @classmethod
    def extract_topics(cls, text: str) -> dict:
        """Use the LLM to extract topics and metadata from question paper text."""
        prompt = f"Question paper text:\n{text[:4000]}\n\nRespond with ONLY the JSON object."

        try:
            response = gemini_service.generate(
                prompt=prompt,
                system_instruction=TOPIC_EXTRACTION_PROMPT,
                json_mode=True,
            )
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (RuntimeError, json.JSONDecodeError) as exc:
            logger.warning("LLM topic extraction failed, using fallback: %s", exc)

        # Fallback: simple heuristic — count capitalised noun phrases
        question_count = len(re.findall(r"(?im)^\s*(?:q\.?\s*\d+|question\s*\d+|\d+[\.\)])", text))
        return {
            "topics": [],
            "question_count": question_count or text.count("?"),
            "subject_area": "unknown",
            "difficulty_level": "medium",
            "question_types": [],
        }

    @classmethod
    def analyze_frequency(cls, papers_topics: list[list[str]]) -> dict:
        """
        Given topics extracted from multiple papers (e.g. last 5 years),
        compute frequency analysis to identify consistently important topics.
        """
        all_topics = [t for paper in papers_topics for t in paper]
        counter = Counter(all_topics)
        total_papers = len(papers_topics)

        frequency_analysis = [
            {
                "topic": topic,
                "frequency": count,
                "appears_in_pct": round((count / total_papers) * 100, 1) if total_papers else 0,
            }
            for topic, count in counter.most_common(20)
        ]

        important_topics = [t for t in frequency_analysis if t["appears_in_pct"] >= 50]

        return {
            "frequency_analysis": frequency_analysis,
            "important_topics": important_topics,
            "total_papers_analyzed": total_papers,
            "unique_topics_found": len(counter),
        }

    @classmethod
    def process_paper(cls, file_path: str | Path) -> dict:
        """Full pipeline for a single question paper: extract text → extract topics."""
        text = cls.extract_text(file_path)
        if not text.strip():
            raise ValueError("Could not extract any readable text from this file.")

        topics_data = cls.extract_topics(text)
        topics_data["text_preview"] = text[:500]
        topics_data["char_count"] = len(text)
        return topics_data

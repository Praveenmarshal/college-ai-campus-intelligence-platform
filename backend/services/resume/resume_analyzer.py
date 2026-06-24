"""
services/resume/resume_analyzer.py
Resume parsing, ATS scoring, and skill gap analysis using Google Gemini.
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional

from rag.pdf_processor import PDFProcessor
from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

# Simple in-memory cache: resume_id -> analysis dict
_analysis_cache: dict[str, dict] = {}

# Common technical skills for keyword-based gap detection (fallback when Gemini unavailable)
COMMON_SKILLS = [
    "python", "java", "javascript", "react", "node.js", "sql", "mongodb",
    "aws", "docker", "kubernetes", "git", "machine learning", "data analysis",
    "communication", "leadership", "html", "css", "c++", "tensorflow", "pytorch",
    "flask", "django", "rest api", "agile", "scrum", "excel", "tableau",
]


class ResumeAnalyzer:
    """Extract, parse, and analyse resumes for ATS compatibility and skill gaps."""

    @staticmethod
    def extract_text(file_path: str | Path) -> str:
        """Extract raw text from a resume PDF."""
        text, _ = PDFProcessor.extract_text(file_path)
        return PDFProcessor.clean_text(text)

    @staticmethod
    def _fallback_skill_extraction(text: str) -> list[str]:
        """Keyword-based skill extraction when Gemini is unavailable."""
        text_lower = text.lower()
        return [skill for skill in COMMON_SKILLS if skill in text_lower]

    @classmethod
    def analyze(cls, resume_text: str, target_role: Optional[str] = None) -> dict:
        """
        Run full resume analysis via Gemini: ATS score, skill extraction, gap analysis.
        Falls back to basic heuristics if Gemini is unavailable.
        """
        try:
            analysis = gemini_service.analyze_resume(
                resume_text=resume_text[:5000],
                target_role=target_role or "Software Engineer",
            )
            # Normalize ats_score
            if "ats_score" in analysis:
                analysis["ats_score"] = max(0, min(100, int(analysis["ats_score"])))
            return analysis

        except Exception as exc:
            logger.warning("Gemini resume analysis failed, using fallback: %s", exc)

        # ── Fallback heuristic analysis ──────────────────────
        extracted_skills = cls._fallback_skill_extraction(resume_text)
        word_count = len(resume_text.split())
        has_email = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", resume_text))
        has_phone = bool(re.search(r"[\+\(]?\d[\d\-\(\) ]{8,}\d", resume_text))

        score = 40
        score += min(len(extracted_skills) * 4, 30)
        score += 10 if has_email else 0
        score += 10 if has_phone else 0
        score += 10 if 300 < word_count < 1200 else 0

        return {
            "ats_score": min(score, 100),
            "strengths": [f"Found {len(extracted_skills)} recognisable skills"] if extracted_skills else [],
            "weaknesses": ["Could not run full AI analysis — Gemini API key may be missing or invalid"],
            "extracted_skills": extracted_skills,
            "missing_skills": [s for s in COMMON_SKILLS if s not in extracted_skills][:8],
            "suggested_job_roles": [],
            "recommendations": [
                "Ensure your resume includes a clear contact email and phone number",
                "List specific technical skills clearly in a dedicated section",
                "Keep resume length between 1-2 pages (300-1200 words)",
            ],
            "summary": (
                "Automated heuristic analysis (Gemini API unavailable). "
                "Please set GEMINI_API_KEY and re-analyze for a full AI-powered assessment."
            ),
        }

    @classmethod
    def cache_analysis(cls, resume_id: str, analysis: dict) -> None:
        _analysis_cache[resume_id] = analysis

    @classmethod
    def get_cached_analysis(cls, resume_id: str) -> Optional[dict]:
        return _analysis_cache.get(resume_id)

    @classmethod
    def process_resume(cls, file_path: str | Path, resume_id: str, target_role: Optional[str] = None) -> dict:
        """Full pipeline: extract → analyze → cache."""
        text = cls.extract_text(file_path)
        if not text.strip():
            raise ValueError(
                "Could not extract any text from this resume. "
                "Ensure it's a text-based PDF, not a scanned image."
            )

        analysis = cls.analyze(text, target_role)
        analysis["word_count"] = len(text.split())
        cls.cache_analysis(resume_id, analysis)
        return analysis

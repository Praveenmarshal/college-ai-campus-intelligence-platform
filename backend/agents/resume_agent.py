"""
agents/resume_agent.py
Wraps the resume analysis service for conversational queries about resumes.
"""
import logging
from typing import Optional

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ResumeAgent(BaseAgent):
    name = "resume_agent"
    description = "Answers questions about resume analysis, ATS scores, and skill gaps"

    def handle(self, query: str, context: Optional[dict] = None) -> dict:
        resume_id = (context or {}).get("resume_id")
        if not resume_id:
            return self._response(
                answer="Please upload a resume first using the Resume Analyzer page, then ask me about it.",
            )
        try:
            from services.resume.resume_analyzer import ResumeAnalyzer
            analysis = ResumeAnalyzer.get_cached_analysis(resume_id)
            if not analysis:
                return self._response(answer="I couldn't find that resume's analysis. Please re-upload it.")

            answer = (
                f"This resume has an ATS score of {analysis.get('ats_score')}/100. "
                f"Missing skills: {', '.join(analysis.get('missing_skills', [])[:5]) or 'none detected'}."
            )
            return self._response(answer=answer, data=analysis)
        except Exception as exc:
            logger.exception("ResumeAgent failed")
            return self._error_response(str(exc))

"""
services/gemini_service.py
Google Gemini API integration service.
Uses standard REST API calls (no external SDK dependency) to avoid version mismatch issues on Render.
Supports chat, RAG, resume analysis (JSON), and data analysis.
"""

import json
import logging
import os
import time
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Load config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")  # gemini-1.5-flash is stable and fast

class GeminiService:
    """Service to interact with the Google Gemini API using REST."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or GEMINI_MODEL
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def _get_url(self) -> str:
        return f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"

    def _call_api(self, payload: Dict[str, Any], retries: int = 3, backoff: float = 2.0) -> Dict[str, Any]:
        """Make a POST request to Gemini API with retries."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set. Please set it in your environment variables.")

        url = self._get_url()
        headers = {"Content-Type": "application/json"}

        for attempt in range(retries):
            try:
                logger.debug(f"Calling Gemini API (attempt {attempt + 1})")
                resp = requests.post(url, headers=headers, json=payload, timeout=60)
                if resp.status_code == 429:
                    logger.warning("Gemini API rate limit hit (429). Retrying after delay...")
                    time.sleep(backoff * (attempt + 1))
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else "?"
                logger.error(f"Gemini API HTTP error (status {status_code}): {exc}")
                if status_code in [500, 502, 503, 504] and attempt < retries - 1:
                    time.sleep(backoff * (attempt + 1))
                    continue
                raise RuntimeError(f"Gemini API request failed: {exc}") from exc
            except Exception as exc:
                logger.error(f"Gemini API connection error: {exc}")
                if attempt < retries - 1:
                    time.sleep(backoff * (attempt + 1))
                    continue
                raise RuntimeError(f"Gemini API call failed: {exc}") from exc

        raise RuntimeError("Gemini API call failed after multiple retries.")

    def generate(self, prompt: str, system_instruction: Optional[str] = None, json_mode: bool = False) -> str:
        """Generate content from a single prompt."""
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        if json_mode:
            payload["generationConfig"] = {
                "responseMimeType": "application/json"
            }

        response_data = self._call_api(payload)
        try:
            candidates = response_data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            raise ValueError(f"Empty or malformed response from Gemini: {response_data}")
        except Exception as exc:
            logger.error(f"Error parsing Gemini response: {exc}")
            raise RuntimeError(f"Failed to parse Gemini response: {exc}") from exc

    def chat(self, messages: List[Dict[str, str]], system_instruction: Optional[str] = None) -> str:
        """
        Execute multi-turn chat.
        messages format: [{"role": "user"|"model"|"assistant", "content": "..."}]
        """
        gemini_contents = []
        for msg in messages:
            role = msg.get("role", "user")
            # map 'assistant' role to 'model' for Gemini
            if role == "assistant":
                role = "model"
            elif role == "system":
                # system instructions should be set in systemInstruction field
                continue

            gemini_contents.append({
                "role": role,
                "parts": [{"text": msg.get("content", "")}]
            })

        payload = {
            "contents": gemini_contents
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        response_data = self._call_api(payload)
        try:
            candidates = response_data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            raise ValueError(f"Empty response in candidates: {response_data}")
        except Exception as exc:
            logger.error(f"Error parsing Gemini chat response: {exc}")
            raise RuntimeError(f"Failed to parse Gemini chat response: {exc}") from exc

    def chat_with_context(self, query: str, context_docs: List[str], sources: List[Dict[str, Any]] = None) -> str:
        """RAG response generation."""
        context_str = "\n\n".join([f"Document chunk:\n{doc}" for doc in context_docs])
        prompt = f"""Use the following pieces of context to answer the user's question. 
If you don't know the answer or if the context doesn't contain the answer, say that you don't know and try to guide them based on general knowledge, but clearly state what is from context and what is general knowledge.
Always cite the source documents (like filenames, page numbers) in your response if provided in context.

CONTEXT:
{context_str}

QUESTION: {query}
"""
        system_instruction = "You are a helpful campus assistant. Your goal is to answer questions about campus regulations, policies, and files accurately using context."
        return self.generate(prompt, system_instruction=system_instruction)

    def analyze_resume(self, resume_text: str, target_role: str = "Software Engineer") -> Dict[str, Any]:
        """Analyze resume text and return structured analysis."""
        prompt = f"""Analyze the following resume text for the target role: "{target_role}".
You must return a JSON object with the following fields:
{{
  "ats_score": <number between 0 and 100 representing match level>,
  "summary": "<a concise 2-3 sentence summary of the candidate>",
  "strengths": ["list of 3-5 main strengths"],
  "weaknesses": ["list of 3-5 weaknesses or areas for improvement"],
  "extracted_skills": ["list of skills found in the resume"],
  "missing_skills": ["list of important skills for the target role that are missing"],
  "suggested_job_roles": ["list of 2-3 suggested job roles for this candidate"],
  "recommendations": ["list of 3-5 actionable improvement suggestions"]
}}

RESUME TEXT:
{resume_text}
"""
        system_instruction = "You are an expert recruitment ATS (Applicant Tracking System) and career coach. Respond ONLY in valid JSON matching the requested schema."
        response_text = self.generate(prompt, system_instruction=system_instruction, json_mode=True)
        try:
            return json.loads(response_text)
        except Exception as exc:
            logger.error(f"Failed to parse resume JSON response: {exc}. Response text: {response_text}")
            # Try to extract JSON if markdown wrapped
            import re
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except Exception:
                    pass
            raise RuntimeError("Failed to parse resume analysis response from Gemini as JSON")

    def analyze_data(self, data_summary: str, question: str) -> str:
        """Analyze Excel/CSV data summaries and answer natural language queries."""
        prompt = f"""You are a data analyst. Below is the summary of a dataset.
Dataset Summary:
{data_summary}

User Question: {question}

Explain the answer to the user's question clearly, citing values from the dataset summary.
If calculations are needed, explain them. Keep the tone helpful, professional and concise.
"""
        return self.generate(prompt)

    def generate_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dashboard insights from aggregated campus stats."""
        prompt = f"""Generate 3-5 key analytics insights from the following campus statistics:
{json.dumps(data, indent=2)}

Return a JSON object containing:
{{
  "insights": [
    {{
      "title": "Short title of the insight",
      "description": "Detailed description of the insight and what it means.",
      "type": "info" | "warning" | "success" | "danger"
    }}
  ]
}}
"""
        response_text = self.generate(prompt, system_instruction="You are a senior academic director and analyst. Respond only in JSON.", json_mode=True)
        try:
            return json.loads(response_text)
        except Exception:
            return {"insights": []}

# Singleton instance
gemini_service = GeminiService()

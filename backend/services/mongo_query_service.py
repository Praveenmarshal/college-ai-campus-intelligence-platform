"""
services/mongo_query_engine.py
Translates natural language questions into MongoDB aggregation pipelines
using Qwen 3, validates them for safety, and executes against allowed collections.
"""

import json
import logging
import re
from typing import Optional

from bson import ObjectId, json_util

from config.database import get_db
from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

# Collections the NL query engine is allowed to touch — never users/audit_logs directly
ALLOWED_COLLECTIONS = {
    "students":   ["student_id", "name", "department", "batch_year", "semester", "cgpa", "section"],
    "faculty":    ["faculty_id", "name", "department", "designation", "subjects"],
    "attendance": ["student_id", "course_id", "course_name", "date", "status", "department"],
    "placements": ["student_id", "student_name", "company_name", "package_lpa", "status", "year", "department"],
    "fees":       ["student_id", "academic_year", "semester", "fee_type", "amount_due", "amount_paid", "payment_status"],
    "events":     ["title", "event_type", "event_date", "venue", "department"],
    "library":    ["title", "author", "category", "available_copies", "total_copies"],
    "hostel":     ["student_id", "room_number", "block", "room_type", "payment_status"],
}

# Operators allowed inside aggregation stages — blocks $where, $function, $accumulator (code execution)
FORBIDDEN_OPERATORS = {"$where", "$function", "$accumulator", "$expr.$function"}

NL_MONGO_SYSTEM_PROMPT = """You are a MongoDB query assistant. Given a collection name, its \
available fields, and a natural language question, respond with ONLY a JSON object containing \
a MongoDB aggregation pipeline. Do not include explanation or markdown — JSON only.

Format:
{
  "collection": "<collection name>",
  "pipeline": [ <aggregation stages as JSON> ]
}

Rules:
- Only use fields that exist in the provided schema.
- Use $match, $group, $sort, $limit, $project, $count — never $where, $function, or $accumulator.
- Always include a $limit stage (max 100) unless the question asks for a count/aggregate.
- For "average", "total", "count" questions, use $group with appropriate accumulators ($avg, $sum, $count)."""


class MongoQueryEngine:
    """Natural language → MongoDB aggregation pipeline → safe execution."""

    @staticmethod
    def _validate_pipeline(pipeline: list) -> tuple[bool, str]:
        """Recursively check a pipeline for forbidden operators."""
        serialised = json.dumps(pipeline)
        for op in FORBIDDEN_OPERATORS:
            if op in serialised:
                return False, f"Forbidden operator detected: {op}"
        if len(pipeline) > 15:
            return False, "Pipeline too complex (max 15 stages)"
        return True, ""

    @classmethod
    def parse_query(cls, question: str, collection: str) -> dict:
        """Use the LLM to convert NL question into a MongoDB aggregation pipeline."""
        if collection not in ALLOWED_COLLECTIONS:
            raise ValueError(
                f"Collection '{collection}' is not queryable. "
                f"Allowed: {list(ALLOWED_COLLECTIONS.keys())}"
            )

        fields = ALLOWED_COLLECTIONS[collection]
        prompt = (
            f"Collection: {collection}\n"
            f"Available fields: {', '.join(fields)}\n\n"
            f"Question: {question}\n\n"
            "Respond with ONLY the JSON object."
        )

        try:
            response = gemini_service.generate(
                prompt=prompt,
                system_instruction=NL_MONGO_SYSTEM_PROMPT,
                json_mode=True,
            )
        except RuntimeError as exc:
            raise RuntimeError(f"Gemini unavailable: {exc}") from exc

        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if not json_match:
            raise ValueError(f"Could not parse LLM response: {response[:200]}")

        try:
            spec = json.loads(json_match.group())
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON from LLM: {exc}") from exc

        if "pipeline" not in spec:
            raise ValueError("LLM response missing 'pipeline' field")

        return spec

    @classmethod
    def execute(cls, collection: str, pipeline: list, max_results: int = 100) -> list[dict]:
        """Safely execute a validated aggregation pipeline."""
        is_valid, error_msg = cls._validate_pipeline(pipeline)
        if not is_valid:
            raise ValueError(f"Unsafe pipeline rejected: {error_msg}")

        # Ensure a limit stage exists to prevent runaway queries
        has_limit = any("$limit" in stage for stage in pipeline)
        has_group_or_count = any("$group" in stage or "$count" in stage for stage in pipeline)
        if not has_limit and not has_group_or_count:
            pipeline.append({"$limit": max_results})

        db = get_db()
        try:
            results = list(db[collection].aggregate(pipeline, maxTimeMS=10000))
        except Exception as exc:
            logger.error("Pipeline execution failed: %s | pipeline=%s", exc, pipeline)
            raise RuntimeError(f"Query execution failed: {exc}") from exc

        # Convert ObjectId/datetime to JSON-safe types
        clean_results = json.loads(json_util.dumps(results))
        for doc in clean_results:
            if "_id" in doc and isinstance(doc["_id"], dict):
                doc["_id"] = str(doc["_id"].get("$oid", doc["_id"]))

        return clean_results

    @classmethod
    def query(cls, question: str, collection: str) -> dict:
        """Full pipeline: NL question → spec → validated execution → result."""
        spec = cls.parse_query(question, collection)
        target_collection = spec.get("collection", collection)

        if target_collection not in ALLOWED_COLLECTIONS:
            target_collection = collection  # fall back to requested collection

        results = cls.execute(target_collection, spec["pipeline"])

        return {
            "collection": target_collection,
            "pipeline": spec["pipeline"],
            "results": results,
            "result_count": len(results),
        }

    @staticmethod
    def list_collections() -> dict:
        """Return the allowed collections and their queryable fields."""
        return ALLOWED_COLLECTIONS

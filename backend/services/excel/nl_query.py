"""
services/excel/nl_query.py
Translates natural language questions into pandas operations
using Google Gemini, then executes them safely against a DataFrame.
"""

import json
import logging
import re

import pandas as pd

from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

NL_QUERY_SYSTEM_PROMPT = """You are a data analyst assistant. Given a pandas DataFrame's \
column names and a natural language question, respond with ONLY a JSON object describing \
the operation to perform. Do not include any explanation, markdown, or extra text.

Schema:
{
  "operation": "filter" | "groupby_agg" | "sort" | "describe" | "value_counts" | "top_n",
  "column": "<column name or null>",
  "group_by": "<column name or null>",
  "agg_column": "<column name or null>",
  "agg_func": "mean" | "sum" | "count" | "max" | "min" | null,
  "filter_column": "<column or null>",
  "filter_op": "==" | "!=" | ">" | "<" | ">=" | "<=" | "contains" | null,
  "filter_value": "<value or null>",
  "sort_column": "<column or null>",
  "sort_ascending": true | false,
  "limit": <integer or null>
}

Only use column names that actually exist in the provided schema."""


class NLQueryEngine:
    """Convert natural language → structured query → pandas execution."""

    @staticmethod
    def _build_schema_description(df: pd.DataFrame) -> str:
        lines = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            sample = df[col].dropna().head(2).tolist()
            lines.append(f"- {col} ({dtype}): e.g. {sample}")
        return "\n".join(lines)

    @classmethod
    def parse_query(cls, question: str, df: pd.DataFrame) -> dict:
        """Use Gemini to convert a natural language question into a structured query spec."""
        schema = cls._build_schema_description(df)
        prompt = (
            f"DataFrame columns:\n{schema}\n\n"
            f"Question: {question}\n\n"
            "Respond with ONLY the JSON object."
        )

        try:
            response = gemini_service.generate(
                prompt=prompt,
                system_instruction=NL_QUERY_SYSTEM_PROMPT,
                json_mode=True,
            )
        except Exception as exc:
            raise RuntimeError(f"Gemini unavailable for query parsing: {exc}") from exc

        # Extract JSON from response
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if not json_match:
            raise ValueError(f"Could not parse Gemini response as JSON: {response[:200]}")

        try:
            spec = json.loads(json_match.group())
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON from Gemini: {exc}") from exc

        return spec

    @staticmethod
    def execute_query(df: pd.DataFrame, spec: dict) -> dict:
        """
        Safely execute a structured query spec against a DataFrame.
        Never uses eval() — only whitelisted pandas operations.
        """
        result_df = df.copy()
        operation = spec.get("operation")

        # ── Filter ──────────────────────────────────────
        if spec.get("filter_column") and spec["filter_column"] in result_df.columns:
            col = spec["filter_column"]
            op = spec.get("filter_op", "==")
            val = spec.get("filter_value")

            try:
                if op == "==":
                    result_df = result_df[result_df[col].astype(str) == str(val)]
                elif op == "!=":
                    result_df = result_df[result_df[col].astype(str) != str(val)]
                elif op == "contains":
                    result_df = result_df[result_df[col].astype(str).str.contains(str(val), case=False, na=False)]
                elif op in (">", "<", ">=", "<="):
                    numeric_col = pd.to_numeric(result_df[col], errors="coerce")
                    numeric_val = float(val)
                    if op == ">":   result_df = result_df[numeric_col > numeric_val]
                    elif op == "<":  result_df = result_df[numeric_col < numeric_val]
                    elif op == ">=": result_df = result_df[numeric_col >= numeric_val]
                    elif op == "<=": result_df = result_df[numeric_col <= numeric_val]
            except Exception as exc:
                logger.warning("Filter execution failed: %s", exc)

        # ── Group by + aggregate ──────────────────────────
        if operation == "groupby_agg" and spec.get("group_by") in result_df.columns:
            group_col = spec["group_by"]
            agg_col = spec.get("agg_column")
            agg_func = spec.get("agg_func", "count")

            if agg_col and agg_col in result_df.columns and agg_func != "count":
                numeric = pd.to_numeric(result_df[agg_col], errors="coerce")
                result_df["_agg_val"] = numeric
                grouped = result_df.groupby(group_col)["_agg_val"].agg(agg_func)
            else:
                grouped = result_df.groupby(group_col).size()

            grouped = grouped.sort_values(ascending=spec.get("sort_ascending", False))
            if spec.get("limit"):
                grouped = grouped.head(int(spec["limit"]))

            return {
                "operation": "groupby_agg",
                "result": grouped.round(2).to_dict() if grouped.dtype != "object" else grouped.to_dict(),
                "row_count": len(grouped),
            }

        # ── Value counts ──────────────────────────────────
        if operation == "value_counts" and spec.get("column") in result_df.columns:
            counts = result_df[spec["column"]].value_counts()
            if spec.get("limit"):
                counts = counts.head(int(spec["limit"]))
            return {"operation": "value_counts", "result": counts.to_dict(), "row_count": len(counts)}

        # ── Sort + top N ────────────────────────────────────
        if operation in ("sort", "top_n") and spec.get("sort_column") in result_df.columns:
            sort_col = spec["sort_column"]
            ascending = spec.get("sort_ascending", False)
            numeric = pd.to_numeric(result_df[sort_col], errors="coerce")
            result_df["_sort_val"] = numeric
            result_df = result_df.sort_values("_sort_val", ascending=ascending).drop(columns=["_sort_val"])

            limit = int(spec.get("limit") or 10)
            result_df = result_df.head(limit)
            return {
                "operation": operation,
                "result": result_df.fillna("").to_dict("records"),
                "row_count": len(result_df),
            }

        # ── Describe (statistical summary) ─────────────────
        if operation == "describe":
            numeric_df = result_df.select_dtypes(include="number")
            if not numeric_df.empty:
                desc = numeric_df.describe().round(2).to_dict()
                return {"operation": "describe", "result": desc, "row_count": len(result_df)}

        # ── Default: return filtered rows ──────────────────
        limit = int(spec.get("limit") or 20)
        return {
            "operation": operation or "filter",
            "result": result_df.head(limit).fillna("").to_dict("records"),
            "row_count": len(result_df),
        }

    @classmethod
    def query(cls, question: str, df: pd.DataFrame) -> dict:
        """Full pipeline: NL question → spec → execution → result."""
        spec = cls.parse_query(question, df)
        result = cls.execute_query(df, spec)
        result["query_spec"] = spec
        return result

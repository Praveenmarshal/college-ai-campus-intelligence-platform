"""
services/csv_engine/csv_processor.py
CSV parsing, type inference, profiling, and statistical analysis.
Reuses ExcelProcessor's analysis logic where applicable since both work on DataFrames.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from services.excel.excel_processor import ExcelProcessor

logger = logging.getLogger(__name__)


class CSVProcessor:
    """Parse and profile CSV files for the analytics engine."""

    # ── Loading ─────────────────────────────────────────────
    @staticmethod
    def load_csv(file_path: str | Path) -> pd.DataFrame:
        """
        Load a CSV with automatic delimiter and encoding detection.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        # Try common encodings
        for encoding in ("utf-8", "latin-1", "cp1252"):
            try:
                df = pd.read_csv(path, encoding=encoding, sep=None, engine="python")
                break
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        else:
            raise RuntimeError(f"Could not parse CSV with any known encoding: {path.name}")

        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        df = df.dropna(how="all")

        logger.info("Loaded CSV '%s' — %d rows, %d cols", path.name, len(df), len(df.columns))
        return df

    # ── Type inference ──────────────────────────────────────
    @staticmethod
    def infer_column_types(df: pd.DataFrame) -> dict:
        """Infer a friendlier type label for each column than raw pandas dtype."""
        types = {}
        for col in df.columns:
            series = df[col].dropna()
            if series.empty:
                types[col] = "empty"
                continue

            if pd.api.types.is_numeric_dtype(series):
                types[col] = "integer" if (series % 1 == 0).all() else "float"
            elif pd.api.types.is_bool_dtype(series):
                types[col] = "boolean"
            else:
                # Try datetime
                try:
                    pd.to_datetime(series.head(20), errors="raise")
                    types[col] = "datetime"
                except (ValueError, TypeError):
                    unique_ratio = series.nunique() / len(series)
                    types[col] = "categorical" if unique_ratio < 0.5 else "text"
        return types

    # ── Profiling ───────────────────────────────────────────
    @classmethod
    def profile(cls, df: pd.DataFrame) -> dict:
        """Generate a full data-quality profile of the CSV."""
        col_types = cls.infer_column_types(df)
        summary = ExcelProcessor.summarise(df)  # reuse general stats

        duplicate_rows = int(df.duplicated().sum())
        completeness = round((1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100, 2) if len(df) else 0

        return {
            **summary,
            "column_types": col_types,
            "duplicate_rows": duplicate_rows,
            "completeness_pct": completeness,
            "memory_usage_kb": round(df.memory_usage(deep=True).sum() / 1024, 2),
        }

    # ── Combined pipeline ─────────────────────────────────
    @classmethod
    def process_file(cls, file_path: str | Path) -> dict:
        df = cls.load_csv(file_path)
        sheet_type = ExcelProcessor.detect_sheet_type(df)
        profile = cls.profile(df)

        analysis = {}
        if sheet_type == "attendance":
            analysis = ExcelProcessor.analyse_attendance(df)
        elif sheet_type == "placements":
            analysis = ExcelProcessor.analyse_placements(df)
        elif sheet_type == "results":
            analysis = ExcelProcessor.analyse_results(df)

        return {
            "detected_type": sheet_type,
            "profile": profile,
            "analysis": analysis,
            "preview": df.head(10).fillna("").to_dict("records"),
        }

"""
services/excel/excel_processor.py
Excel parsing, sheet-type auto-detection, and statistical analysis.
Supports: attendance.xlsx, placements.xlsx, fees.xlsx, results.xlsx,
          students.xlsx, faculty.xlsx, timetable.xlsx
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Column signatures used to auto-detect sheet type
SHEET_SIGNATURES = {
    "attendance": {"student_id", "date", "status", "course"},
    "placements": {"company", "package", "student", "placement"},
    "fees":       {"fee", "amount", "due", "payment"},
    "results":    {"cgpa", "grade", "marks", "semester", "subject"},
    "students":   {"student_id", "name", "department", "batch"},
    "faculty":    {"faculty_id", "designation", "qualification"},
    "timetable":  {"day", "period", "subject", "time", "slot"},
    "library":    {"title", "author", "isbn", "book"},
    "hostel":     {"room_number", "block", "room_type", "hostel"},
    "events":     {"title", "event_date", "event_type", "venue"},
}


class ExcelProcessor:
    """Parse and analyse Excel workbooks for the analytics engine."""

    # ── Loading ─────────────────────────────────────────────
    @staticmethod
    def load_workbook(file_path: str | Path) -> dict[str, pd.DataFrame]:
        """
        Load all sheets from an Excel file into DataFrames.
        Returns { sheet_name: DataFrame }.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        try:
            sheets = pd.read_excel(path, sheet_name=None, engine="openpyxl")
        except Exception as exc:
            logger.error("Failed to read Excel file %s: %s", path, exc)
            raise RuntimeError(f"Could not read Excel file: {exc}") from exc

        # Clean column names on every sheet
        for name, df in sheets.items():
            df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
            sheets[name] = df.dropna(how="all")

        logger.info("Loaded workbook '%s' — sheets: %s", path.name, list(sheets.keys()))
        return sheets

    # ── Sheet type detection ───────────────────────────────
    @staticmethod
    def detect_sheet_type(df: pd.DataFrame) -> str:
        """
        Auto-detect the dataset type based on column name signatures.
        Returns one of: attendance, placements, fees, results, students,
                        faculty, timetable, unknown
        """
        cols = {c.lower() for c in df.columns}
        best_match, best_score = "unknown", 0

        for sheet_type, signature in SHEET_SIGNATURES.items():
            score = sum(1 for sig in signature if any(sig in c for c in cols))
            if score > best_score:
                best_score = score
                best_match = sheet_type

        return best_match if best_score >= 2 else "unknown"

    # ── Statistical summary ─────────────────────────────────
    @staticmethod
    def summarise(df: pd.DataFrame) -> dict:
        """Generate a general statistical summary of a DataFrame."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

        summary = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "missing_values": df.isnull().sum().to_dict(),
            "numeric_stats": {},
            "categorical_stats": {},
        }

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) > 0:
                summary["numeric_stats"][col] = {
                    "mean":   round(float(series.mean()), 2),
                    "median": round(float(series.median()), 2),
                    "min":    round(float(series.min()), 2),
                    "max":    round(float(series.max()), 2),
                    "std":    round(float(series.std()), 2) if len(series) > 1 else 0,
                }

        for col in categorical_cols[:10]:  # limit to avoid huge payloads
            counts = df[col].value_counts().head(10)
            summary["categorical_stats"][col] = counts.to_dict()

        return summary

    # ── Type-specific analytics ─────────────────────────────
    @staticmethod
    def analyse_attendance(df: pd.DataFrame) -> dict:
        """Compute attendance-specific analytics."""
        col_map = ExcelProcessor._find_columns(df, {
            "student_id": ["student_id", "studentid", "roll_no", "roll_number"],
            "status":     ["status", "attendance_status", "present"],
            "date":       ["date", "attendance_date"],
            "course":     ["course", "course_name", "subject"],
        })

        result = {"detected_columns": col_map}

        if col_map.get("status"):
            status_col = col_map["status"]
            present_vals = {"present", "p", "1", "yes", "true"}
            df["_is_present"] = df[status_col].astype(str).str.lower().isin(present_vals)

            overall_pct = round(df["_is_present"].mean() * 100, 2)
            result["overall_attendance_pct"] = overall_pct

            if col_map.get("student_id"):
                per_student = df.groupby(col_map["student_id"])["_is_present"].mean() * 100
                result["per_student_pct"] = per_student.round(2).to_dict()
                result["at_risk_students"] = per_student[per_student < 75].round(2).to_dict()

            if col_map.get("course"):
                per_course = df.groupby(col_map["course"])["_is_present"].mean() * 100
                result["per_course_pct"] = per_course.round(2).to_dict()

        return result

    @staticmethod
    def analyse_placements(df: pd.DataFrame) -> dict:
        """Compute placement-specific analytics."""
        col_map = ExcelProcessor._find_columns(df, {
            "company": ["company", "company_name", "recruiter"],
            "package": ["package", "package_lpa", "salary", "ctc"],
            "student": ["student", "student_name", "student_id"],
            "status":  ["status", "placement_status"],
        })

        result = {"detected_columns": col_map}

        if col_map.get("package"):
            pkg_col = col_map["package"]
            pkg_series = pd.to_numeric(df[pkg_col], errors="coerce").dropna()
            if len(pkg_series) > 0:
                result["highest_package"] = round(float(pkg_series.max()), 2)
                result["average_package"] = round(float(pkg_series.mean()), 2)
                result["lowest_package"]  = round(float(pkg_series.min()), 2)

        if col_map.get("company"):
            result["companies_visited"] = int(df[col_map["company"]].nunique())
            result["top_recruiters"] = df[col_map["company"]].value_counts().head(10).to_dict()

        if col_map.get("status"):
            placed = df[col_map["status"]].astype(str).str.lower().str.contains("placed", na=False)
            result["total_students"] = len(df)
            result["placed_count"] = int(placed.sum())
            result["placement_rate_pct"] = round(placed.mean() * 100, 2)

        return result

    @staticmethod
    def analyse_results(df: pd.DataFrame) -> dict:
        """Compute academic results analytics (CGPA, grades, top performers)."""
        col_map = ExcelProcessor._find_columns(df, {
            "cgpa":    ["cgpa", "gpa"],
            "student": ["student", "student_name", "student_id", "name"],
            "subject": ["subject", "course"],
            "marks":   ["marks", "score"],
        })

        result = {"detected_columns": col_map}

        if col_map.get("cgpa"):
            cgpa_series = pd.to_numeric(df[col_map["cgpa"]], errors="coerce").dropna()
            if len(cgpa_series) > 0:
                result["average_cgpa"] = round(float(cgpa_series.mean()), 2)
                result["highest_cgpa"] = round(float(cgpa_series.max()), 2)
                result["lowest_cgpa"]  = round(float(cgpa_series.min()), 2)

                if col_map.get("student"):
                    top = df.nlargest(10, col_map["cgpa"])[[col_map["student"], col_map["cgpa"]]]
                    result["top_performers"] = top.to_dict("records")

        return result

    # ── Helper ──────────────────────────────────────────────
    @staticmethod
    def _find_columns(df: pd.DataFrame, candidates: dict[str, list[str]]) -> dict[str, Optional[str]]:
        """Match actual column names against candidate keyword lists."""
        cols_lower = {c.lower(): c for c in df.columns}
        result = {}
        for key, options in candidates.items():
            match = None
            for opt in options:
                for col_lower, original in cols_lower.items():
                    if opt in col_lower:
                        match = original
                        break
                if match:
                    break
            result[key] = match
        return result

    # ── Combined pipeline ─────────────────────────────────
    @classmethod
    def process_file(cls, file_path: str | Path) -> dict:
        """
        Full pipeline: load → detect type per sheet → summarise → type-specific analysis.
        Returns a dict keyed by sheet name.
        """
        sheets = cls.load_workbook(file_path)
        output = {}

        for sheet_name, df in sheets.items():
            if df.empty:
                continue

            sheet_type = cls.detect_sheet_type(df)
            summary = cls.summarise(df)

            analysis = {}
            if sheet_type == "attendance":
                analysis = cls.analyse_attendance(df)
            elif sheet_type == "placements":
                analysis = cls.analyse_placements(df)
            elif sheet_type == "results":
                analysis = cls.analyse_results(df)

            output[sheet_name] = {
                "detected_type": sheet_type,
                "summary": summary,
                "analysis": analysis,
                "preview": df.head(5).fillna("").to_dict("records"),
            }

        return output

    @classmethod
    def save_to_mongodb(cls, sheets: dict[str, pd.DataFrame]) -> dict:
        """
        Save the processed sheets into the respective MongoDB collections.
        """
        from config.database import get_db
        from datetime import datetime, timezone
        db = get_db()
        stats = {}

        for sheet_name, df in sheets.items():
            if df.empty:
                continue

            sheet_type = cls.detect_sheet_type(df)
            if sheet_type == "unknown":
                continue

            # Convert NaN to None for Mongo insertion
            df_clean = df.replace({np.nan: None})

            if sheet_type == "students":
                col_map = cls._find_columns(df, {
                    "student_id": ["student_id", "studentid", "roll", "roll_number", "roll_no"],
                    "name": ["name", "student_name", "full_name"],
                    "email": ["email", "e_mail", "mail"],
                    "department": ["department", "dept", "branch"],
                    "batch_year": ["batch", "batch_year", "year"],
                    "semester": ["semester", "sem"],
                    "cgpa": ["cgpa", "gpa"],
                    "is_hostel": ["hostel", "is_hostel", "hosteler"]
                })
                now = datetime.now(timezone.utc)
                count = 0
                for _, row in df_clean.iterrows():
                    s_id = str(row.get(col_map.get("student_id") or "student_id") or "").strip()
                    if not s_id:
                        continue
                    email = str(row.get(col_map.get("email") or "email") or "").strip().lower()
                    name = str(row.get(col_map.get("name") or "name") or "").strip()
                    if not name:
                        name = s_id
                    
                    student_doc = {
                        "student_id": s_id,
                        "name": name,
                        "email": email or f"{s_id}@college.edu",
                        "phone": str(row.get("phone") or ""),
                        "department": str(row.get(col_map.get("department") or "department") or "General"),
                        "batch_year": int(row.get(col_map.get("batch_year") or "batch_year") or 2026),
                        "semester": int(row.get(col_map.get("semester") or "semester") or 1),
                        "section": str(row.get("section") or "A"),
                        "cgpa": float(row.get(col_map.get("cgpa") or "cgpa") or 0.0),
                        "is_hostel": bool(row.get(col_map.get("is_hostel") or "is_hostel") or False),
                        "updated_at": now
                    }
                    db.students.update_one({"student_id": s_id}, {"$set": student_doc, "$setOnInsert": {"created_at": now}}, upsert=True)
                    count += 1
                stats[sheet_name] = f"Upserted {count} students"

            elif sheet_type == "faculty":
                col_map = cls._find_columns(df, {
                    "faculty_id": ["faculty_id", "facultyid", "employee_id", "emp_id"],
                    "name": ["name", "faculty_name", "full_name"],
                    "email": ["email", "e_mail", "mail"],
                    "department": ["department", "dept", "branch"],
                    "designation": ["designation", "role", "post"],
                    "qualification": ["qualification", "degree"],
                    "experience_years": ["experience", "exp", "years"]
                })
                now = datetime.now(timezone.utc)
                count = 0
                for _, row in df_clean.iterrows():
                    f_id = str(row.get(col_map.get("faculty_id") or "faculty_id") or "").strip()
                    if not f_id:
                        continue
                    name = str(row.get(col_map.get("name") or "name") or "").strip()
                    email = str(row.get(col_map.get("email") or "email") or "").strip().lower()
                    
                    fac_doc = {
                        "faculty_id": f_id,
                        "name": name or f_id,
                        "email": email or f"{f_id}@college.edu",
                        "phone": str(row.get("phone") or ""),
                        "department": str(row.get(col_map.get("department") or "department") or "General"),
                        "designation": str(row.get(col_map.get("designation") or "designation") or "Lecturer"),
                        "qualification": str(row.get(col_map.get("qualification") or "qualification") or "PhD"),
                        "experience_years": int(row.get(col_map.get("experience_years") or "experience_years") or 0),
                        "subjects": str(row.get("subjects") or "").split(",") if row.get("subjects") else [],
                        "updated_at": now
                    }
                    db.faculty.update_one({"faculty_id": f_id}, {"$set": fac_doc, "$setOnInsert": {"created_at": now}}, upsert=True)
                    count += 1
                stats[sheet_name] = f"Upserted {count} faculty members"

            elif sheet_type == "attendance":
                col_map = cls._find_columns(df, {
                    "student_id": ["student_id", "studentid", "roll", "roll_number", "roll_no"],
                    "status": ["status", "attendance_status", "present"],
                    "date": ["date", "attendance_date"],
                    "course": ["course", "course_name", "subject"]
                })
                db.attendance.delete_many({})
                count = 0
                for _, row in df_clean.iterrows():
                    s_id = str(row.get(col_map.get("student_id") or "student_id") or "").strip()
                    if not s_id:
                        continue
                    status = str(row.get(col_map.get("status") or "status") or "absent").strip().lower()
                    present_vals = {"present", "p", "1", "yes", "true"}
                    normalized_status = "present" if status in present_vals else "absent"
                    
                    raw_date = row.get(col_map.get("date") or "date")
                    if isinstance(raw_date, str):
                        try:
                            date_obj = pd.to_datetime(raw_date).to_pydatetime()
                        except Exception:
                            date_obj = datetime.now(timezone.utc)
                    elif hasattr(raw_date, "to_pydatetime"):
                        date_obj = raw_date.to_pydatetime()
                    else:
                        date_obj = datetime.now(timezone.utc)

                    att_doc = {
                        "student_id": s_id,
                        "status": normalized_status,
                        "date": date_obj,
                        "course_name": str(row.get(col_map.get("course") or "course") or "General"),
                        "course_id": str(row.get("course_id") or "GEN-01"),
                        "department": str(row.get("department") or "General")
                    }
                    db.attendance.insert_one(att_doc)
                    count += 1
                stats[sheet_name] = f"Loaded {count} attendance records"

            elif sheet_type == "placements":
                col_map = cls._find_columns(df, {
                    "company": ["company", "company_name", "recruiter"],
                    "package": ["package", "package_lpa", "salary", "ctc"],
                    "student": ["student", "student_name", "student_id", "roll_no"],
                    "status": ["status", "placement_status"]
                })
                db.placements.delete_many({})
                count = 0
                for _, row in df_clean.iterrows():
                    student = str(row.get(col_map.get("student") or "student") or "").strip()
                    if not student:
                        continue
                    pkg_val = row.get(col_map.get("package") or "package")
                    try:
                        pkg = float(pkg_val) if pkg_val is not None else 0.0
                    except Exception:
                        pkg = 0.0

                    status = str(row.get(col_map.get("status") or "status") or "placed").strip().lower()
                    
                    placement_doc = {
                        "student_id": student,
                        "student_name": str(row.get("name") or student),
                        "company_name": str(row.get(col_map.get("company") or "company") or "Unknown"),
                        "package_lpa": pkg,
                        "status": "placed" if "placed" in status or status == "yes" else "unplaced",
                        "year": int(row.get("year") or datetime.now().year),
                        "department": str(row.get("department") or "General")
                    }
                    db.placements.insert_one(placement_doc)
                    count += 1
                stats[sheet_name] = f"Loaded {count} placement records"

            elif sheet_type == "results":
                col_map = cls._find_columns(df, {
                    "cgpa": ["cgpa", "gpa"],
                    "student_id": ["student_id", "roll_no", "studentid"],
                    "subject": ["subject", "course", "subject_name"],
                    "marks": ["marks", "score", "grade"]
                })
                db.results.delete_many({})
                count = 0
                for _, row in df_clean.iterrows():
                    s_id = str(row.get(col_map.get("student_id") or "student_id") or "").strip()
                    if not s_id:
                        continue
                    cgpa_val = row.get(col_map.get("cgpa") or "cgpa")
                    try:
                        cgpa = float(cgpa_val) if cgpa_val is not None else None
                    except Exception:
                        cgpa = None

                    if cgpa is not None:
                        db.students.update_one({"student_id": s_id}, {"$set": {"cgpa": cgpa}})
                    
                    res_doc = {
                        "student_id": s_id,
                        "subject": str(row.get(col_map.get("subject") or "subject") or "General"),
                        "marks": str(row.get(col_map.get("marks") or "marks") or ""),
                        "cgpa": cgpa or 0.0,
                        "semester": int(row.get("semester") or 1)
                    }
                    db.results.insert_one(res_doc)
                    count += 1
                stats[sheet_name] = f"Processed {count} student results"

            elif sheet_type == "fees":
                col_map = cls._find_columns(df, {
                    "fee": ["fee", "amount", "total"],
                    "due": ["due", "amount_due", "pending"],
                    "payment": ["payment", "status", "payment_status"],
                    "student_id": ["student_id", "roll_no"]
                })
                db.fees.delete_many({})
                count = 0
                for _, row in df_clean.iterrows():
                    s_id = str(row.get(col_map.get("student_id") or "student_id") or "").strip()
                    if not s_id:
                        continue
                    try:
                        amt = float(row.get("amount") or row.get(col_map.get("fee") or "amount") or 0.0)
                        due = float(row.get(col_map.get("due") or "due") or 0.0)
                    except Exception:
                        amt = 0.0
                        due = 0.0

                    pay_status = str(row.get(col_map.get("payment") or "payment") or "pending").strip().lower()

                    fee_doc = {
                        "student_id": s_id,
                        "amount_due": due,
                        "amount_paid": amt - due if amt >= due else 0.0,
                        "payment_status": pay_status,
                        "semester": int(row.get("semester") or 1),
                        "academic_year": str(row.get("academic_year") or "2025-2026")
                    }
                    db.fees.insert_one(fee_doc)
                    count += 1
                stats[sheet_name] = f"Loaded {count} fee records"

            elif sheet_type == "timetable":
                db.timetable.delete_many({})
                count = 0
                for _, row in df_clean.iterrows():
                    tt_doc = {
                        "day": str(row.get("day") or ""),
                        "period": str(row.get("period") or ""),
                        "subject": str(row.get("subject") or ""),
                        "time": str(row.get("time") or ""),
                        "slot": str(row.get("slot") or ""),
                        "department": str(row.get("department") or "General"),
                        "faculty_name": str(row.get("faculty") or row.get("teacher") or "")
                    }
                    db.timetable.insert_one(tt_doc)
                    count += 1
                stats[sheet_name] = f"Loaded {count} timetable slots"

            elif sheet_type == "library":
                db.library.delete_many({})
                count = 0
                for _, row in df_clean.iterrows():
                    lib_doc = {
                        "title": str(row.get("title") or ""),
                        "author": str(row.get("author") or ""),
                        "isbn": str(row.get("isbn") or ""),
                        "category": str(row.get("category") or "General"),
                        "available_copies": int(row.get("available") or row.get("copies") or 1),
                        "total_copies": int(row.get("total") or row.get("copies") or 1)
                    }
                    db.library.insert_one(lib_doc)
                    count += 1
                stats[sheet_name] = f"Loaded {count} books"

            elif sheet_type == "hostel":
                db.hostel.delete_many({})
                count = 0
                for _, row in df_clean.iterrows():
                    hostel_doc = {
                        "student_id": str(row.get("student_id") or ""),
                        "room_number": str(row.get("room") or row.get("room_number") or ""),
                        "block": str(row.get("block") or ""),
                        "room_type": str(row.get("type") or "Double"),
                        "payment_status": str(row.get("payment") or "paid")
                    }
                    db.hostel.insert_one(hostel_doc)
                    count += 1
                stats[sheet_name] = f"Loaded {count} hostel rooms"

            elif sheet_type == "events":
                db.events.delete_many({})
                count = 0
                for _, row in df_clean.iterrows():
                    raw_date = row.get("event_date") or row.get("date")
                    if isinstance(raw_date, str):
                        try:
                            date_obj = pd.to_datetime(raw_date).to_pydatetime()
                        except Exception:
                            date_obj = datetime.now(timezone.utc)
                    elif hasattr(raw_date, "to_pydatetime"):
                        date_obj = raw_date.to_pydatetime()
                    else:
                        date_obj = datetime.now(timezone.utc)

                    evt_doc = {
                        "title": str(row.get("title") or ""),
                        "event_type": str(row.get("type") or row.get("event_type") or "Cultural"),
                        "event_date": date_obj,
                        "venue": str(row.get("venue") or "Auditorium"),
                        "department": str(row.get("department") or "General"),
                        "is_active": True
                    }
                    db.events.insert_one(evt_doc)
                    count += 1
                stats[sheet_name] = f"Loaded {count} events"

        return stats

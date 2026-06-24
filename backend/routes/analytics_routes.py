"""
routes/analytics_routes.py
Dashboard and analytics aggregation endpoints.
Falls back to sample data when MongoDB collections are empty.
"""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required

from models.response import success
from services.auth_service import active_user_required, faculty_or_admin_required
from config.database import get_db

logger = logging.getLogger(__name__)
analytics_bp = Blueprint("analytics", __name__)

SAMPLE_DATA_DIR = Path(__file__).parent.parent / "sample_data"


def _load_excel_stats(filename: str) -> dict:
    """Load stats from a sample/uploaded Excel file as a fallback."""
    try:
        import pandas as pd
        # Check uploads first, then sample_data
        upload_paths = [
            Path(current_app.config.get("UPLOAD_FOLDER", "./uploads")) / "excels" / filename,
            SAMPLE_DATA_DIR / filename,
        ]
        for p in upload_paths:
            if p.exists():
                return {"path": str(p), "df": pd.read_excel(p, engine="openpyxl")}
    except Exception as exc:
        logger.warning("Could not load Excel fallback %s: %s", filename, exc)
    return {}


@analytics_bp.get("/dashboard")
@jwt_required()
@active_user_required
def dashboard():
    """High-level dashboard stats — with Excel fallback when MongoDB is empty."""
    db = get_db()

    total_students = db.students.count_documents({})
    total_faculty = db.faculty.count_documents({})
    total_documents = db.documents.count_documents({})
    total_placed = db.placements.count_documents({"status": "placed"})
    recent_chats = db.chats.count_documents({
        "updated_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=7)}
    })

    avg_attendance = None
    avg_cgpa = None
    highest_package = None

    # ── Excel fallbacks ─────────────────────────────────────
    if total_students == 0:
        try:
            import pandas as pd
            res = _load_excel_stats("students.xlsx")
            if res.get("df") is not None:
                df = res["df"]
                df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
                total_students = len(df)
                if "cgpa" in df.columns:
                    avg_cgpa = round(float(df["cgpa"].dropna().mean()), 2)
        except Exception as exc:
            logger.warning("students.xlsx fallback failed: %s", exc)

    if total_students > 0 and avg_cgpa is None:
        try:
            pipeline = [{"$group": {"_id": None, "avg": {"$avg": "$cgpa"}}}]
            res = list(db.students.aggregate(pipeline))
            if res and res[0].get("avg"):
                avg_cgpa = round(res[0]["avg"], 2)
        except Exception:
            pass

    if total_faculty == 0:
        try:
            res = _load_excel_stats("faculty.xlsx")
            if res.get("df") is not None:
                total_faculty = len(res["df"])
        except Exception:
            pass

    if total_placed == 0:
        try:
            import pandas as pd
            res = _load_excel_stats("placements.xlsx")
            if res.get("df") is not None:
                df = res["df"]
                df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
                placed_col = next((c for c in df.columns if "status" in c), None)
                pkg_col = next((c for c in df.columns if "package" in c or "lpa" in c or "ctc" in c), None)
                if placed_col:
                    total_placed = int(df[placed_col].str.lower().eq("placed").sum())
                elif pkg_col:
                    total_placed = int(df[pkg_col].notna().sum())
                if pkg_col:
                    highest_package = round(float(pd.to_numeric(df[pkg_col], errors="coerce").max()), 2)
        except Exception as exc:
            logger.warning("placements.xlsx fallback failed: %s", exc)

    if highest_package is None:
        try:
            res = list(db.placements.aggregate([{"$group": {"_id": None, "max_pkg": {"$max": "$package_lpa"}}}]))
            if res and res[0].get("max_pkg"):
                highest_package = round(res[0]["max_pkg"], 2)
        except Exception:
            pass

    if avg_attendance is None:
        try:
            import pandas as pd
            res = _load_excel_stats("attendance.xlsx")
            if res.get("df") is not None:
                df = res["df"]
                df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
                status_col = next((c for c in df.columns if "status" in c or "attendance" in c), None)
                if status_col:
                    present_count = df[status_col].str.lower().isin(["present", "p", "1"]).sum()
                    avg_attendance = round(float(present_count / len(df) * 100), 1)
                elif "attendance_percentage" in df.columns or "attendance_pct" in df.columns:
                    col = "attendance_percentage" if "attendance_percentage" in df.columns else "attendance_pct"
                    avg_attendance = round(float(pd.to_numeric(df[col], errors="coerce").mean()), 1)
        except Exception as exc:
            logger.warning("attendance.xlsx fallback failed: %s", exc)

    if avg_attendance is None:
        try:
            pipeline = [
                {"$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "present": {"$sum": {"$cond": [{"$eq": ["$status", "present"]}, 1, 0]}},
                }}
            ]
            res = list(db.attendance.aggregate(pipeline))
            if res and res[0]["total"] > 0:
                avg_attendance = round(res[0]["present"] / res[0]["total"] * 100, 1)
        except Exception:
            pass

    return success({
        "total_students": total_students,
        "total_faculty": total_faculty,
        "total_documents": total_documents,
        "total_placed": total_placed,
        "recent_chat_sessions": recent_chats,
        "avg_attendance": avg_attendance,
        "avg_cgpa": avg_cgpa,
        "highest_package": highest_package,
    })


@analytics_bp.get("/attendance")
@jwt_required()
@active_user_required
def attendance_analytics():
    db = get_db()
    department = request.args.get("department")

    match_stage = {"$match": {"department": department}} if department else {"$match": {}}

    pipeline = [
        match_stage,
        {"$group": {
            "_id": "$department",
            "total": {"$sum": 1},
            "present": {"$sum": {"$cond": [{"$eq": ["$status", "present"]}, 1, 0]}},
        }},
    ]
    by_dept = list(db.attendance.aggregate(pipeline))
    for d in by_dept:
        d["department"] = d.pop("_id")
        d["attendance_pct"] = round((d["present"] / d["total"]) * 100, 2) if d["total"] else 0

    # ── Excel fallback ─────────────────────────────────
    if not by_dept:
        try:
            import pandas as pd
            res = _load_excel_stats("attendance.xlsx")
            if res.get("df") is not None:
                df = res["df"]
                df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
                dept_col = next((c for c in df.columns if "dept" in c or "department" in c), None)
                status_col = next((c for c in df.columns if "status" in c), None)
                if dept_col and status_col:
                    grouped = df.groupby(dept_col)
                    for dept_name, grp in grouped:
                        total = len(grp)
                        present = grp[status_col].str.lower().isin(["present", "p"]).sum()
                        by_dept.append({
                            "department": str(dept_name),
                            "total": int(total),
                            "present": int(present),
                            "attendance_pct": round(float(present / total * 100), 2) if total else 0,
                        })
        except Exception as exc:
            logger.warning("attendance.xlsx fallback failed: %s", exc)

    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    trend_pipeline = [
        {"$match": {"date": {"$gte": thirty_days_ago}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
            "total": {"$sum": 1},
            "present": {"$sum": {"$cond": [{"$eq": ["$status", "present"]}, 1, 0]}},
        }},
        {"$sort": {"_id": 1}},
    ]
    trend = list(db.attendance.aggregate(trend_pipeline))
    for t in trend:
        t["date"] = t.pop("_id")
        t["attendance_pct"] = round((t["present"] / t["total"]) * 100, 2) if t["total"] else 0

    return success({"by_department": by_dept, "trend_30_days": trend})


@analytics_bp.get("/placements")
@jwt_required()
@active_user_required
def placement_analytics():
    db = get_db()

    pipeline = [
        {"$group": {
            "_id": None,
            "total": {"$sum": 1},
            "placed": {"$sum": {"$cond": [{"$eq": ["$status", "placed"]}, 1, 0]}},
            "avg_package": {"$avg": "$package_lpa"},
            "max_package": {"$max": "$package_lpa"},
        }}
    ]
    overall = list(db.placements.aggregate(pipeline))
    overall = overall[0] if overall else {}
    overall.pop("_id", None)

    by_year = list(db.placements.aggregate([
        {"$group": {"_id": "$year", "placed_count": {"$sum": 1}, "avg_package": {"$avg": "$package_lpa"}}},
        {"$sort": {"_id": 1}},
    ]))
    for y in by_year:
        y["year"] = y.pop("_id")
        y["avg_package"] = round(y.get("avg_package") or 0, 2)

    top_recruiters = list(db.placements.aggregate([
        {"$group": {"_id": "$company_name", "hires": {"$sum": 1}}},
        {"$sort": {"hires": -1}}, {"$limit": 10},
    ]))
    for r in top_recruiters:
        r["company"] = r.pop("_id")

    # ── Excel fallback ─────────────────────────────────
    if not overall:
        try:
            import pandas as pd
            res = _load_excel_stats("placements.xlsx")
            if res.get("df") is not None:
                df = res["df"]
                df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
                pkg_col = next((c for c in df.columns if "package" in c or "lpa" in c or "ctc" in c), None)
                status_col = next((c for c in df.columns if "status" in c), None)
                company_col = next((c for c in df.columns if "company" in c), None)
                total = len(df)
                placed = int(df[status_col].str.lower().eq("placed").sum()) if status_col else total
                avg_pkg = round(float(pd.to_numeric(df[pkg_col], errors="coerce").mean()), 2) if pkg_col else 0
                max_pkg = round(float(pd.to_numeric(df[pkg_col], errors="coerce").max()), 2) if pkg_col else 0
                overall = {"total": total, "placed": placed, "avg_package": avg_pkg, "max_package": max_pkg}
                if company_col and not top_recruiters:
                    co_counts = df[company_col].value_counts().head(10)
                    top_recruiters = [{"company": str(k), "hires": int(v)} for k, v in co_counts.items()]
                year_col = next((c for c in df.columns if "year" in c or "batch" in c), None)
                if year_col and not by_year:
                    for yr, grp in df.groupby(year_col):
                        pkg_vals = pd.to_numeric(grp[pkg_col], errors="coerce") if pkg_col else None
                        by_year.append({
                            "year": str(yr),
                            "placed_count": len(grp),
                            "avg_package": round(float(pkg_vals.mean()), 2) if pkg_vals is not None else 0,
                        })
        except Exception as exc:
            logger.warning("placements.xlsx fallback failed: %s", exc)

    return success({
        "overall": {k: (round(v, 2) if isinstance(v, float) else v) for k, v in overall.items()},
        "by_year": by_year,
        "top_recruiters": top_recruiters,
    })


@analytics_bp.get("/academic")
@jwt_required()
@active_user_required
def academic_analytics():
    db = get_db()

    pipeline = [
        {"$group": {
            "_id": "$department",
            "avg_cgpa": {"$avg": "$cgpa"},
            "student_count": {"$sum": 1},
        }},
        {"$sort": {"avg_cgpa": -1}},
    ]
    by_dept = list(db.students.aggregate(pipeline))
    for d in by_dept:
        d["department"] = d.pop("_id")
        d["avg_cgpa"] = round(d.get("avg_cgpa") or 0, 2)

    top_performers = list(
        db.students.find({}, {"name": 1, "student_id": 1, "cgpa": 1, "department": 1})
        .sort("cgpa", -1).limit(10)
    )
    for s in top_performers:
        s["id"] = str(s.pop("_id"))

    # ── Excel fallback ─────────────────────────────────
    if not by_dept:
        try:
            import pandas as pd
            for fname in ["results.xlsx", "students.xlsx"]:
                res = _load_excel_stats(fname)
                if res.get("df") is not None:
                    df = res["df"]
                    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
                    dept_col = next((c for c in df.columns if "dept" in c or "department" in c), None)
                    cgpa_col = next((c for c in df.columns if "cgpa" in c or "gpa" in c), None)
                    if dept_col and cgpa_col:
                        df[cgpa_col] = pd.to_numeric(df[cgpa_col], errors="coerce")
                        for dept_name, grp in df.groupby(dept_col):
                            by_dept.append({
                                "department": str(dept_name),
                                "avg_cgpa": round(float(grp[cgpa_col].mean()), 2),
                                "student_count": len(grp),
                            })
                        if not top_performers and "name" in df.columns:
                            top_df = df.nlargest(10, cgpa_col)
                            for _, row in top_df.iterrows():
                                top_performers.append({
                                    "id": str(row.get("student_id", "")),
                                    "name": str(row.get("name", "")),
                                    "cgpa": float(row.get(cgpa_col, 0)),
                                    "department": str(row.get(dept_col, "")),
                                })
                        break
        except Exception as exc:
            logger.warning("results/students.xlsx fallback failed: %s", exc)

    return success({"by_department": by_dept, "top_performers": top_performers})


@analytics_bp.get("/system")
@jwt_required()
@faculty_or_admin_required
def system_stats():
    """Document/upload type breakdown and storage stats."""
    db = get_db()
    by_type = list(db.documents.aggregate([
        {"$group": {"_id": "$file_type", "count": {"$sum": 1}, "total_size": {"$sum": "$file_size"}}}
    ]))
    for t in by_type:
        t["file_type"] = t.pop("_id")

    return success({"documents_by_type": by_type})

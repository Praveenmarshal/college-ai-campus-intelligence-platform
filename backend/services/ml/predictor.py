"""
services/ml/predictor.py
Phase 11 — Machine Learning prediction service.

Trains and serves Random Forest / XGBoost models for:
  - Attendance risk prediction
  - CGPA trend prediction
  - Placement probability
  - Fee default risk

Models are persisted to disk (joblib) and lazily loaded.
Falls back to rule-based heuristics if no trained model exists yet
(cold-start friendly for a freshly deployed platform).
"""

import logging
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error

from config.database import get_db

logger = logging.getLogger(__name__)

# XGBoost is omitted from requirements-render.txt (lean free-tier deploys) to
# stay under Render's free-tier build size. Placement prediction falls back to
# RandomForestClassifier (already imported above) when XGBoost isn't installed
# — same training/inference code path, just a different classifier under the hood.
try:
    from xgboost import XGBClassifier
    _XGBOOST_AVAILABLE = True
except ImportError:
    logger.warning(
        "xgboost not installed — placement prediction will use RandomForestClassifier instead. "
        "This is expected on lean deployments using requirements-render.txt."
    )
    _XGBOOST_AVAILABLE = False

MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


class Predictor:
    """Unified interface for all ML prediction tasks."""

    # ── Attendance risk ─────────────────────────────────────
    @staticmethod
    def _attendance_model_path() -> Path:
        return MODEL_DIR / "attendance_risk.joblib"

    @classmethod
    def train_attendance_model(cls) -> dict:
        """Train a Random Forest classifier to predict attendance risk (binary: at-risk or not)."""
        db = get_db()
        pipeline = [
            {"$group": {
                "_id": "$student_id",
                "total_classes": {"$sum": 1},
                "present_count": {"$sum": {"$cond": [{"$eq": ["$status", "present"]}, 1, 0]}},
            }}
        ]
        records = list(db.attendance.aggregate(pipeline))

        if len(records) < 20:
            return {"status": "insufficient_data", "message": "Need at least 20 student attendance records to train"}

        df = pd.DataFrame(records)
        df["attendance_pct"] = (df["present_count"] / df["total_classes"]) * 100
        df["at_risk"] = (df["attendance_pct"] < 75).astype(int)

        X = df[["total_classes", "present_count"]]
        y = df["at_risk"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
        model.fit(X_train, y_train)

        accuracy = accuracy_score(y_test, model.predict(X_test)) if len(X_test) > 0 else 0
        joblib.dump(model, cls._attendance_model_path())

        return {"status": "trained", "accuracy": round(accuracy, 3), "samples": len(df)}

    @classmethod
    def predict_attendance_risk(cls, student_id: str) -> dict:
        db = get_db()
        records = list(db.attendance.find({"student_id": student_id}))
        if not records:
            return {"risk": "unknown", "reason": "No attendance records found", "attendance_pct": None}

        total = len(records)
        present = sum(1 for r in records if r.get("status") == "present")
        pct = round((present / total) * 100, 2) if total else 0

        model_path = cls._attendance_model_path()
        if model_path.exists():
            try:
                model = joblib.load(model_path)
                pred = model.predict([[total, present]])[0]
                proba = model.predict_proba([[total, present]])[0][1]
                risk = "high" if pred == 1 else "low"
                return {"risk": risk, "attendance_pct": pct, "risk_probability": round(float(proba), 3), "method": "ml_model"}
            except Exception as exc:
                logger.warning("Attendance model prediction failed, using heuristic: %s", exc)

        # Heuristic fallback
        risk = "high" if pct < 75 else ("medium" if pct < 85 else "low")
        return {"risk": risk, "attendance_pct": pct, "method": "heuristic"}

    # ── CGPA prediction ──────────────────────────────────────
    @staticmethod
    def _cgpa_model_path() -> Path:
        return MODEL_DIR / "cgpa_predictor.joblib"

    @classmethod
    def train_cgpa_model(cls) -> dict:
        """Train a regressor to predict next-semester CGPA from current CGPA + attendance."""
        db = get_db()
        students = list(db.students.find({}, {"student_id": 1, "cgpa": 1, "semester": 1}))

        if len(students) < 20:
            return {"status": "insufficient_data", "message": "Need at least 20 student records to train"}

        rows = []
        for s in students:
            att_records = list(db.attendance.find({"student_id": s.get("student_id")}))
            if not att_records:
                continue
            present_pct = sum(1 for r in att_records if r.get("status") == "present") / len(att_records) * 100
            rows.append({
                "current_cgpa": s.get("cgpa", 0),
                "semester": s.get("semester", 1),
                "attendance_pct": present_pct,
                "next_cgpa": s.get("cgpa", 0),  # proxy target — in production this would be t+1 actual CGPA
            })

        if len(rows) < 15:
            return {"status": "insufficient_data", "message": "Not enough joined records to train"}

        df = pd.DataFrame(rows)
        X = df[["current_cgpa", "semester", "attendance_pct"]]
        y = df["next_cgpa"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
        model.fit(X_train, y_train)

        mae = mean_absolute_error(y_test, model.predict(X_test)) if len(X_test) > 0 else 0
        joblib.dump(model, cls._cgpa_model_path())

        return {"status": "trained", "mae": round(float(mae), 3), "samples": len(df)}

    @classmethod
    def predict_cgpa(cls, student_id: str) -> dict:
        db = get_db()
        student = db.students.find_one({"student_id": student_id})
        if not student:
            return {"prediction": "unknown", "reason": "Student not found"}

        current_cgpa = student.get("cgpa", 0)
        att_records = list(db.attendance.find({"student_id": student_id}))
        att_pct = (
            sum(1 for r in att_records if r.get("status") == "present") / len(att_records) * 100
            if att_records else 75
        )

        model_path = cls._cgpa_model_path()
        if model_path.exists():
            try:
                model = joblib.load(model_path)
                pred = model.predict([[current_cgpa, student.get("semester", 1), att_pct]])[0]
                trend = "improving" if pred > current_cgpa else ("declining" if pred < current_cgpa else "stable")
                return {"predicted_cgpa": round(float(pred), 2), "current_cgpa": current_cgpa, "trend": trend, "method": "ml_model"}
            except Exception as exc:
                logger.warning("CGPA model prediction failed, using heuristic: %s", exc)

        # Heuristic: attendance strongly correlates with CGPA trend
        trend = "improving" if att_pct > 85 else ("declining" if att_pct < 65 else "stable")
        return {"predicted_cgpa": current_cgpa, "current_cgpa": current_cgpa, "trend": trend, "method": "heuristic"}

    # ── Placement probability ────────────────────────────────
    @staticmethod
    def _placement_model_path() -> Path:
        return MODEL_DIR / "placement_predictor.joblib"

    @classmethod
    def train_placement_model(cls) -> dict:
        """Train an XGBoost classifier to predict placement likelihood from CGPA + attendance."""
        db = get_db()
        placements = list(db.placements.find({}, {"student_id": 1, "status": 1}))

        if len(placements) < 20:
            return {"status": "insufficient_data", "message": "Need at least 20 placement records to train"}

        rows = []
        for p in placements:
            student = db.students.find_one({"student_id": p.get("student_id")})
            if not student:
                continue
            att_records = list(db.attendance.find({"student_id": p.get("student_id")}))
            att_pct = (
                sum(1 for r in att_records if r.get("status") == "present") / len(att_records) * 100
                if att_records else 75
            )
            rows.append({
                "cgpa": student.get("cgpa", 0),
                "attendance_pct": att_pct,
                "placed": 1 if p.get("status") == "placed" else 0,
            })

        if len(rows) < 15:
            return {"status": "insufficient_data", "message": "Not enough joined records to train"}

        df = pd.DataFrame(rows)
        X = df[["cgpa", "attendance_pct"]]
        y = df["placed"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        if _XGBOOST_AVAILABLE:
            model = XGBClassifier(n_estimators=100, max_depth=4, random_state=42, eval_metric="logloss")
        else:
            model = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=42)
        model.fit(X_train, y_train)

        accuracy = accuracy_score(y_test, model.predict(X_test)) if len(X_test) > 0 else 0
        joblib.dump(model, cls._placement_model_path())

        return {"status": "trained", "accuracy": round(float(accuracy), 3), "samples": len(df)}

    @classmethod
    def predict_placement_probability(cls, student_id: str) -> dict:
        db = get_db()
        student = db.students.find_one({"student_id": student_id})
        if not student:
            return {"probability": None, "reason": "Student not found"}

        cgpa = student.get("cgpa", 0)
        att_records = list(db.attendance.find({"student_id": student_id}))
        att_pct = (
            sum(1 for r in att_records if r.get("status") == "present") / len(att_records) * 100
            if att_records else 75
        )

        model_path = cls._placement_model_path()
        if model_path.exists():
            try:
                model = joblib.load(model_path)
                proba = model.predict_proba([[cgpa, att_pct]])[0][1]
                return {"probability": round(float(proba), 3), "cgpa": cgpa, "attendance_pct": round(att_pct, 1), "method": "ml_model"}
            except Exception as exc:
                logger.warning("Placement model prediction failed, using heuristic: %s", exc)

        # Heuristic fallback
        score = min(1.0, max(0.0, (cgpa / 10) * 0.6 + (att_pct / 100) * 0.4))
        return {"probability": round(score, 3), "cgpa": cgpa, "attendance_pct": round(att_pct, 1), "method": "heuristic"}

    # ── Fee default risk ──────────────────────────────────────
    @classmethod
    def predict_fee_default_risk(cls, student_id: str) -> dict:
        """Heuristic-based fee default risk (rule-based — no historical default labels yet)."""
        db = get_db()
        fee_records = list(db.fees.find({"student_id": student_id}))
        if not fee_records:
            return {"risk": "unknown", "reason": "No fee records found"}

        overdue_count = sum(1 for f in fee_records if f.get("payment_status") == "overdue")
        total_due = sum(f.get("amount_due", 0) - f.get("amount_paid", 0) for f in fee_records)

        if overdue_count >= 2 or total_due > 50000:
            risk = "high"
        elif overdue_count == 1 or total_due > 10000:
            risk = "medium"
        else:
            risk = "low"

        return {"risk": risk, "overdue_count": overdue_count, "outstanding_amount": round(total_due, 2), "method": "heuristic"}

    # ── Combined prediction ────────────────────────────────────
    @classmethod
    def predict_all(cls, student_id: str) -> dict:
        """Run all four prediction types for a student in one call."""
        attendance = cls.predict_attendance_risk(student_id)
        cgpa = cls.predict_cgpa(student_id)
        placement = cls.predict_placement_probability(student_id)
        fee = cls.predict_fee_default_risk(student_id)

        return {
            "student_id": student_id,
            "attendance_risk": attendance.get("risk"),
            "attendance_pct": attendance.get("attendance_pct"),
            "cgpa_prediction": cgpa.get("trend"),
            "predicted_cgpa": cgpa.get("predicted_cgpa"),
            "placement_probability": placement.get("probability"),
            "fee_default_risk": fee.get("risk"),
        }

    @classmethod
    def train_all_models(cls) -> dict:
        """Retrain all models — typically run as an admin/scheduled task."""
        return {
            "attendance_model": cls.train_attendance_model(),
            "cgpa_model": cls.train_cgpa_model(),
            "placement_model": cls.train_placement_model(),
        }

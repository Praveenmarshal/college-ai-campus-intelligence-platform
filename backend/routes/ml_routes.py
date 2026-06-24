"""
routes/ml_routes.py
Phase 11 — Machine Learning prediction endpoints.

Endpoints:
  GET  /api/ml/predict/:student_id        — all predictions for a student
  GET  /api/ml/predict/attendance/:id     — attendance risk only
  GET  /api/ml/predict/cgpa/:id           — CGPA trend only
  GET  /api/ml/predict/placement/:id      — placement probability only
  GET  /api/ml/predict/fee-default/:id    — fee default risk only
  POST /api/ml/train                      — retrain all models (admin)
  GET  /api/ml/at-risk-students           — list all at-risk students (admin/faculty)
"""

import logging

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.response import success, error
from models.audit_model import AuditModel
from services.auth_service import AuthService, active_user_required, admin_required, faculty_or_admin_required
from services.ml.predictor import Predictor
from config.database import get_db

logger = logging.getLogger(__name__)
ml_bp = Blueprint("ml", __name__)


@ml_bp.get("/predict/<string:student_id>")
@jwt_required()
@active_user_required
def predict_all(student_id):
    result = Predictor.predict_all(student_id)
    return success(result)


@ml_bp.get("/predict/attendance/<string:student_id>")
@jwt_required()
@active_user_required
def predict_attendance(student_id):
    return success(Predictor.predict_attendance_risk(student_id))


@ml_bp.get("/predict/cgpa/<string:student_id>")
@jwt_required()
@active_user_required
def predict_cgpa(student_id):
    return success(Predictor.predict_cgpa(student_id))


@ml_bp.get("/predict/placement/<string:student_id>")
@jwt_required()
@active_user_required
def predict_placement(student_id):
    return success(Predictor.predict_placement_probability(student_id))


@ml_bp.get("/predict/fee-default/<string:student_id>")
@jwt_required()
@active_user_required
def predict_fee_default(student_id):
    return success(Predictor.predict_fee_default_risk(student_id))


@ml_bp.post("/train")
@jwt_required()
@admin_required
def train_models():
    """Retrain all ML models from current MongoDB data."""
    results = Predictor.train_all_models()
    AuditModel.log(
        user_id=get_jwt_identity(), action="train_ml_models", resource="ml",
        ip_address=AuthService.get_ip(), details=results,
    )
    return success(results, "Model training complete")


@ml_bp.get("/at-risk-students")
@jwt_required()
@faculty_or_admin_required
def at_risk_students():
    """List students flagged as at-risk for attendance (heuristic scan)."""
    db = get_db()
    pipeline = [
        {"$group": {
            "_id": "$student_id",
            "total": {"$sum": 1},
            "present": {"$sum": {"$cond": [{"$eq": ["$status", "present"]}, 1, 0]}},
        }},
        {"$project": {
            "student_id": "$_id",
            "attendance_pct": {"$multiply": [{"$divide": ["$present", "$total"]}, 100]},
        }},
        {"$match": {"attendance_pct": {"$lt": 75}}},
        {"$sort": {"attendance_pct": 1}},
        {"$limit": 50},
    ]
    at_risk = list(db.attendance.aggregate(pipeline))
    for r in at_risk:
        r.pop("_id", None)
        r["attendance_pct"] = round(r["attendance_pct"], 2)

    return success({"at_risk_students": at_risk, "count": len(at_risk)})

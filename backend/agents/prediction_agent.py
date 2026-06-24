"""
agents/prediction_agent.py
Routes prediction questions (attendance/CGPA/placement/fee-default risk) to ML models.
"""
import logging
from typing import Optional

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class PredictionAgent(BaseAgent):
    name = "prediction_agent"
    description = "Provides ML-based predictions: attendance, CGPA, placement, fee default risk"

    def handle(self, query: str, context: Optional[dict] = None) -> dict:
        try:
            from services.ml.predictor import Predictor
            student_id = (context or {}).get("student_id")

            if not student_id:
                return self._response(
                    answer="To generate a prediction, please specify a student ID.",
                    data=None,
                )

            predictions = Predictor.predict_all(student_id)
            answer = (
                f"Based on historical data for student {student_id}: "
                f"attendance risk is {predictions.get('attendance_risk', 'unknown')}, "
                f"predicted CGPA trend is {predictions.get('cgpa_prediction', 'unknown')}, "
                f"placement likelihood is {predictions.get('placement_probability', 'unknown')}."
            )
            return self._response(answer=answer, data=predictions)
        except Exception as exc:
            logger.exception("PredictionAgent failed")
            return self._error_response(str(exc))

"""
tests/unit/test_phase11_13_ml_ocr_notify.py
Phase 11 (ML), Phase 12 (OCR), Phase 13 (Notifications) — unit tests.
"""

import pytest


class TestPredictorHeuristics:
    """Tests for ML predictor fallback heuristics (no trained model required)."""

    def test_predict_attendance_risk_no_records(self, app):
        with app.app_context():
            from services.ml.predictor import Predictor
            result = Predictor.predict_attendance_risk("NONEXISTENT_STUDENT_999")
            assert result["risk"] == "unknown"

    def test_predict_fee_default_no_records(self, app):
        with app.app_context():
            from services.ml.predictor import Predictor
            result = Predictor.predict_fee_default_risk("NONEXISTENT_STUDENT_999")
            assert result["risk"] == "unknown"

    def test_predict_cgpa_unknown_student(self, app):
        with app.app_context():
            from services.ml.predictor import Predictor
            result = Predictor.predict_cgpa("NONEXISTENT_STUDENT_999")
            assert result["prediction"] == "unknown"

    def test_predict_placement_unknown_student(self, app):
        with app.app_context():
            from services.ml.predictor import Predictor
            result = Predictor.predict_placement_probability("NONEXISTENT_STUDENT_999")
            assert result["probability"] is None


class TestOCRProcessorInterface:

    def test_ocr_processor_has_required_methods(self):
        from services.ocr.ocr_processor import OCRProcessor
        assert hasattr(OCRProcessor, "extract_text")
        assert hasattr(OCRProcessor, "extract_with_easyocr")
        assert hasattr(OCRProcessor, "extract_with_tesseract")
        assert hasattr(OCRProcessor, "extract_from_scanned_pdf")

    def test_extract_text_invalid_path_raises(self):
        from services.ocr.ocr_processor import OCRProcessor
        with pytest.raises(Exception):
            OCRProcessor.extract_text("/nonexistent/path/image.png")


class TestQuestionPaperAnalyzer:

    def test_extract_topics_fallback_question_count(self, monkeypatch):
        from services.ocr.question_paper_analyzer import QuestionPaperAnalyzer
        from rag.llm_client import llm_client

        def mock_chat(*args, **kwargs):
            raise RuntimeError("LLM unavailable")

        monkeypatch.setattr(llm_client, "chat", mock_chat)

        text = "Q1. What is OOP?\nQ2. Define polymorphism.\nQ3. Explain inheritance."
        result = QuestionPaperAnalyzer.extract_topics(text)
        assert result["question_count"] >= 3

    def test_analyze_frequency_basic(self):
        from services.ocr.question_paper_analyzer import QuestionPaperAnalyzer
        papers_topics = [
            ["Binary Trees", "Sorting", "Graphs"],
            ["Binary Trees", "Sorting"],
            ["Binary Trees", "Hashing"],
        ]
        result = QuestionPaperAnalyzer.analyze_frequency(papers_topics)
        assert result["total_papers_analyzed"] == 3
        top_topic = result["frequency_analysis"][0]
        assert top_topic["topic"] == "Binary Trees"
        assert top_topic["frequency"] == 3
        assert top_topic["appears_in_pct"] == 100.0

    def test_analyze_frequency_important_topics_threshold(self):
        from services.ocr.question_paper_analyzer import QuestionPaperAnalyzer
        papers_topics = [["A", "B"], ["A"], ["A"], ["B"]]
        result = QuestionPaperAnalyzer.analyze_frequency(papers_topics)
        important_names = [t["topic"] for t in result["important_topics"]]
        assert "A" in important_names  # appears in 3/4 = 75%


class TestNotificationModel:

    def test_serialise_converts_objectid(self, app):
        with app.app_context():
            from bson import ObjectId
            from models.notification_model import NotificationModel
            doc = {
                "_id": ObjectId(),
                "user_id": ObjectId(),
                "title": "Test",
                "message": "Test message",
                "notification_type": "system",
                "channel": "in-app",
                "is_read": False,
                "is_sent": True,
                "sent_at": None,
                "created_at": None,
            }
            result = NotificationModel._serialise(doc)
            assert isinstance(result["id"], str)
            assert isinstance(result["user_id"], str)
            assert "_id" not in result


class TestEmailServiceTemplates:
    """Test email template generation without actually sending (mocked send)."""

    def test_send_attendance_alert_calls_send(self, monkeypatch):
        from services.notification.email_service import EmailService

        captured = {}
        def mock_send(to, subject, body, html_body=None):
            captured["to"] = to
            captured["subject"] = subject
            captured["body"] = body
            return True

        monkeypatch.setattr(EmailService, "send", staticmethod(mock_send))
        result = EmailService.send_attendance_alert("test@test.com", "John Doe", 68.5)
        assert result is True
        assert captured["to"] == "test@test.com"
        assert "Attendance Alert" in captured["subject"]

    def test_send_fee_due_alert_calls_send(self, monkeypatch):
        from services.notification.email_service import EmailService

        captured = {}
        def mock_send(to, subject, body, html_body=None):
            captured["body"] = body
            return True

        monkeypatch.setattr(EmailService, "send", staticmethod(mock_send))
        EmailService.send_fee_due_alert("test@test.com", "Jane", 15000.0, "2024-12-31")
        assert "15,000" in captured["body"]


class TestSMSServiceGracefulFailure:

    def test_send_without_credentials_returns_false(self, monkeypatch):
        from services.notification.sms_service import SMSService
        monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
        monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
        SMSService._client = None
        result = SMSService.send("+1234567890", "Test message")
        assert result is False

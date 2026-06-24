"""
services/notification/sms_service.py
Phase 13 — SMS notification service using Twilio.
"""

import logging
import os

logger = logging.getLogger(__name__)


class SMSService:
    """Send SMS alerts via Twilio for critical, time-sensitive notifications."""

    _client = None

    @classmethod
    def _get_client(cls):
        if cls._client is None:
            try:
                from twilio.rest import Client
                sid = os.getenv("TWILIO_ACCOUNT_SID")
                token = os.getenv("TWILIO_AUTH_TOKEN")
                if not sid or not token:
                    logger.warning("Twilio credentials not configured")
                    return None
                cls._client = Client(sid, token)
            except Exception as exc:
                logger.error("Failed to initialise Twilio client: %s", exc)
                return None
        return cls._client

    @classmethod
    def send(cls, to: str, body: str) -> bool:
        """Send a single SMS. Returns True on success, False on failure (never raises)."""
        client = cls._get_client()
        if client is None:
            logger.warning("SMS not sent (Twilio unavailable): %s", to)
            return False

        from_number = os.getenv("TWILIO_PHONE_NUMBER")
        if not from_number:
            logger.error("TWILIO_PHONE_NUMBER not configured")
            return False

        try:
            client.messages.create(body=body, from_=from_number, to=to)
            logger.info("SMS sent to %s", to)
            return True
        except Exception as exc:
            logger.error("Failed to send SMS to %s: %s", to, exc)
            return False

    @classmethod
    def send_attendance_alert(cls, to: str, student_name: str, attendance_pct: float) -> bool:
        body = (
            f"Campus AI Alert: Hi {student_name}, your attendance is {attendance_pct}%, "
            f"below the 75% requirement. Please attend classes regularly."
        )
        return cls.send(to, body)

    @classmethod
    def send_fee_alert(cls, to: str, student_name: str, amount: float, due_date: str) -> bool:
        body = f"Campus AI: Hi {student_name}, fee of Rs.{amount:,.0f} is due on {due_date}. Please pay promptly."
        return cls.send(to, body)

    @classmethod
    def send_otp(cls, to: str, otp: str) -> bool:
        body = f"Your Campus AI verification code is: {otp}. Valid for 10 minutes. Do not share this code."
        return cls.send(to, body)

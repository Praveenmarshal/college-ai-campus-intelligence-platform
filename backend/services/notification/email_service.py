"""
services/notification/email_service.py
Phase 13 — SMTP email notification service using Flask-Mail.
"""

import logging
from typing import Optional

from flask_mail import Message

logger = logging.getLogger(__name__)


class EmailService:
    """Send transactional emails for campus alerts."""

    @staticmethod
    def send(to: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """
        Send a single email. Returns True on success, False on failure (never raises).
        """
        try:
            from app import mail
            msg = Message(subject=subject, recipients=[to], body=body, html=html_body)
            mail.send(msg)
            logger.info("Email sent to %s: %s", to, subject)
            return True
        except Exception as exc:
            logger.error("Failed to send email to %s: %s", to, exc)
            return False

    @staticmethod
    def send_bulk(recipients: list[str], subject: str, body: str, html_body: Optional[str] = None) -> dict:
        """Send the same email to multiple recipients. Returns success/failure counts."""
        sent, failed = 0, 0
        for recipient in recipients:
            if EmailService.send(recipient, subject, body, html_body):
                sent += 1
            else:
                failed += 1
        return {"sent": sent, "failed": failed, "total": len(recipients)}

    # ── Templated notifications ────────────────────────────

    @staticmethod
    def send_attendance_alert(to: str, student_name: str, attendance_pct: float) -> bool:
        subject = "⚠️ Attendance Alert — Action Required"
        body = (
            f"Dear {student_name},\n\n"
            f"Your current attendance is {attendance_pct}%, which is below the required 75% threshold.\n"
            f"Please ensure regular attendance to avoid academic penalties.\n\n"
            f"— Campus AI Intelligence Platform"
        )
        html = f"""
        <div style="font-family: sans-serif; max-width: 500px;">
          <h2 style="color: #ef4444;">⚠️ Attendance Alert</h2>
          <p>Dear {student_name},</p>
          <p>Your current attendance is <strong>{attendance_pct}%</strong>, which is below the
          required <strong>75%</strong> threshold.</p>
          <p>Please ensure regular attendance to avoid academic penalties.</p>
          <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 16px 0;">
          <p style="color: #6b7280; font-size: 12px;">Campus AI Intelligence Platform</p>
        </div>
        """
        return EmailService.send(to, subject, body, html)

    @staticmethod
    def send_fee_due_alert(to: str, student_name: str, amount_due: float, due_date: str) -> bool:
        subject = "💰 Fee Payment Reminder"
        body = (
            f"Dear {student_name},\n\n"
            f"This is a reminder that you have an outstanding fee of ₹{amount_due:,.2f}, "
            f"due on {due_date}.\n\nPlease complete the payment to avoid late fees.\n\n"
            f"— Campus AI Intelligence Platform"
        )
        return EmailService.send(to, subject, body)

    @staticmethod
    def send_placement_notification(to: str, student_name: str, company: str, role: str) -> bool:
        subject = f"🎉 New Placement Opportunity — {company}"
        body = (
            f"Dear {student_name},\n\n"
            f"{company} is hiring for the role of {role}. Check the placement portal for details "
            f"and apply before the deadline.\n\n— Campus AI Intelligence Platform"
        )
        return EmailService.send(to, subject, body)

    @staticmethod
    def send_event_reminder(to: str, student_name: str, event_title: str, event_date: str, venue: str) -> bool:
        subject = f"📅 Event Reminder — {event_title}"
        body = (
            f"Dear {student_name},\n\n"
            f"Reminder: '{event_title}' is happening on {event_date} at {venue}.\n\n"
            f"— Campus AI Intelligence Platform"
        )
        return EmailService.send(to, subject, body)

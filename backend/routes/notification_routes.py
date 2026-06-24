"""
routes/notification_routes.py
Phase 13 — Notification management endpoints.
"""

import logging

from flask import Blueprint, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.notification_model import NotificationModel
from models.response import success, error, not_found, paginated
from services.auth_service import active_user_required, admin_required, AuthService
from services.notification.email_service import EmailService
from services.notification.sms_service import SMSService
from config.database import get_db

logger = logging.getLogger(__name__)
notification_bp = Blueprint("notification", __name__)


@notification_bp.get("")
@jwt_required()
@active_user_required
def list_notifications():
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(50, max(1, int(request.args.get("per_page", 20))))
    unread_only = request.args.get("unread_only", "false").lower() == "true"

    notifs, total = NotificationModel.find_by_user(g.current_user["id"], page, per_page, unread_only)
    return paginated(notifs, total, page, per_page)


@notification_bp.get("/unread-count")
@jwt_required()
@active_user_required
def unread_count():
    count = NotificationModel.count_unread(g.current_user["id"])
    return success({"unread_count": count})


@notification_bp.put("/<string:notification_id>/read")
@jwt_required()
@active_user_required
def mark_read(notification_id):
    ok = NotificationModel.mark_read(notification_id, g.current_user["id"])
    if not ok:
        return not_found("Notification")
    return success(message="Marked as read")


@notification_bp.put("/read-all")
@jwt_required()
@active_user_required
def mark_all_read():
    count = NotificationModel.mark_all_read(g.current_user["id"])
    return success({"updated_count": count}, "All notifications marked as read")


@notification_bp.delete("/<string:notification_id>")
@jwt_required()
@active_user_required
def delete_notification(notification_id):
    ok = NotificationModel.delete(notification_id, g.current_user["id"])
    if not ok:
        return not_found("Notification")
    return success(message="Notification deleted")


@notification_bp.post("/send/attendance-alert")
@jwt_required()
@admin_required
def send_attendance_alerts():
    """
    Bulk send attendance alerts to all students below the threshold.
    Body: { threshold?: number (default 75) }
    """
    threshold = float((request.get_json(silent=True) or {}).get("threshold", 75))
    db = get_db()

    pipeline = [
        {"$group": {
            "_id": "$student_id",
            "total": {"$sum": 1},
            "present": {"$sum": {"$cond": [{"$eq": ["$status", "present"]}, 1, 0]}},
        }},
    ]
    records = list(db.attendance.aggregate(pipeline))

    sent_count = 0
    for r in records:
        pct = round((r["present"] / r["total"]) * 100, 2) if r["total"] else 0
        if pct < threshold:
            student = db.students.find_one({"student_id": r["_id"]})
            if not student:
                continue
            user = db.users.find_one({"email": student.get("email")})
            if not user:
                continue

            EmailService.send_attendance_alert(student["email"], student["name"], pct)
            NotificationModel.create(
                str(user["_id"]), "Attendance Alert",
                f"Your attendance is {pct}%, below the {threshold}% requirement.",
                notification_type="attendance", channel="email",
            )
            sent_count += 1

    AuditModel_log_safe(get_jwt_identity(), sent_count)
    return success({"alerts_sent": sent_count}, f"Sent {sent_count} attendance alert(s)")


def AuditModel_log_safe(user_id, count):
    try:
        from models.audit_model import AuditModel
        AuditModel.log(
            user_id=user_id, action="bulk_attendance_alerts", resource="notifications",
            details={"sent_count": count},
        )
    except Exception:
        pass

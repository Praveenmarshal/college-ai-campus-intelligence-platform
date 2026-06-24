"""
models/schemas.py
MongoDB document schema definitions.
These are plain Python dicts used as templates and for validation.
Full Marshmallow validators are co-located here for each collection.
"""

from datetime import datetime, timezone
from bson import ObjectId


def utcnow():
    return datetime.now(timezone.utc)


# ── User ──────────────────────────────────────────────────────
USER_SCHEMA = {
    "_id": ObjectId,
    "name": str,
    "email": str,                    # unique
    "password_hash": str,
    "role": str,                     # admin | faculty | student
    "is_active": bool,
    "profile_picture": str,          # URL or file path
    "phone": str,
    "department": str,
    "created_at": datetime,
    "updated_at": datetime,
    "last_login": datetime,
    "refresh_tokens": list,          # list of valid refresh token JTIs
}

# ── Student ───────────────────────────────────────────────────
STUDENT_SCHEMA = {
    "_id": ObjectId,
    "student_id": str,               # e.g. "2024CS001"
    "user_id": ObjectId,             # ref → users
    "name": str,
    "email": str,
    "phone": str,
    "department": str,               # CSE | ECE | ME | CE | ...
    "batch_year": int,               # 2022
    "semester": int,                 # 1–8
    "section": str,                  # A | B | C
    "cgpa": float,
    "address": str,
    "guardian_name": str,
    "guardian_phone": str,
    "is_hostel": bool,
    "created_at": datetime,
    "updated_at": datetime,
}

# ── Faculty ───────────────────────────────────────────────────
FACULTY_SCHEMA = {
    "_id": ObjectId,
    "faculty_id": str,               # e.g. "FAC001"
    "user_id": ObjectId,
    "name": str,
    "email": str,
    "phone": str,
    "department": str,
    "designation": str,              # Professor | Asst Prof | HOD
    "subjects": list,                # ["CS3001", "CS3002"]
    "qualification": str,
    "experience_years": int,
    "created_at": datetime,
    "updated_at": datetime,
}

# ── Attendance ────────────────────────────────────────────────
ATTENDANCE_SCHEMA = {
    "_id": ObjectId,
    "student_id": str,
    "course_id": str,
    "course_name": str,
    "faculty_id": str,
    "date": datetime,
    "status": str,                   # present | absent | late
    "semester": int,
    "department": str,
    "recorded_by": ObjectId,         # ref → users (faculty)
    "created_at": datetime,
}

# ── Placement ─────────────────────────────────────────────────
PLACEMENT_SCHEMA = {
    "_id": ObjectId,
    "student_id": str,
    "student_name": str,
    "department": str,
    "batch_year": int,
    "company_name": str,
    "job_role": str,
    "package_lpa": float,            # lakhs per annum
    "offer_date": datetime,
    "joining_date": datetime,
    "placement_type": str,           # campus | off-campus | internship
    "status": str,                   # placed | not_placed | in_process
    "year": int,
    "created_at": datetime,
}

# ── Fee ───────────────────────────────────────────────────────
FEE_SCHEMA = {
    "_id": ObjectId,
    "student_id": str,
    "academic_year": str,            # "2024-25"
    "semester": int,
    "fee_type": str,                 # tuition | hostel | transport | misc
    "amount_due": float,
    "amount_paid": float,
    "due_date": datetime,
    "payment_date": datetime,
    "payment_mode": str,             # online | cash | cheque | dd
    "transaction_id": str,
    "payment_status": str,           # paid | pending | overdue | partial
    "created_at": datetime,
}

# ── Document (uploaded file) ──────────────────────────────────
DOCUMENT_SCHEMA = {
    "_id": ObjectId,
    "filename": str,
    "original_name": str,
    "file_path": str,
    "file_type": str,                # pdf | excel | csv | image
    "file_size": int,                # bytes
    "mime_type": str,
    "uploaded_by": ObjectId,
    "description": str,
    "tags": list,
    "is_processed": bool,            # has it been embedded in ChromaDB?
    "collection_name": str,          # which ChromaDB collection
    "chunk_count": int,
    "created_at": datetime,
    "updated_at": datetime,
}

# ── Chat / Conversation ───────────────────────────────────────
CHAT_SCHEMA = {
    "_id": ObjectId,
    "session_id": str,              # UUID for conversation grouping
    "user_id": ObjectId,
    "title": str,                   # auto-generated from first message
    "messages": [
        {
            "role": str,            # user | assistant
            "content": str,
            "sources": list,        # document sources cited
            "agent_used": str,      # which agent handled this
            "timestamp": datetime,
        }
    ],
    "agent_type": str,              # last agent used
    "created_at": datetime,
    "updated_at": datetime,
}

# ── Event ─────────────────────────────────────────────────────
EVENT_SCHEMA = {
    "_id": ObjectId,
    "title": str,
    "description": str,
    "event_type": str,              # cultural | technical | sports | seminar
    "event_date": datetime,
    "venue": str,
    "organiser": str,
    "department": str,              # "all" or specific dept
    "registrations": list,          # list of student_ids
    "max_participants": int,
    "is_active": bool,
    "created_at": datetime,
}

# ── Library ───────────────────────────────────────────────────
LIBRARY_SCHEMA = {
    "_id": ObjectId,
    "isbn": str,
    "title": str,
    "author": str,
    "publisher": str,
    "year": int,
    "category": str,
    "total_copies": int,
    "available_copies": int,
    "location": str,                # shelf/rack reference
    "borrowed_by": [
        {
            "student_id": str,
            "borrow_date": datetime,
            "due_date": datetime,
            "return_date": datetime,
            "fine_amount": float,
        }
    ],
    "created_at": datetime,
}

# ── Hostel ────────────────────────────────────────────────────
HOSTEL_SCHEMA = {
    "_id": ObjectId,
    "student_id": str,
    "room_number": str,
    "block": str,                   # A | B | C | D
    "floor": int,
    "room_type": str,               # single | double | triple
    "allocated_date": datetime,
    "vacating_date": datetime,
    "monthly_fee": float,
    "payment_status": str,
    "warden_name": str,
    "is_active": bool,
    "created_at": datetime,
}

# ── Notification ──────────────────────────────────────────────
NOTIFICATION_SCHEMA = {
    "_id": ObjectId,
    "user_id": ObjectId,
    "title": str,
    "message": str,
    "notification_type": str,       # attendance | fee | placement | event | system
    "channel": str,                 # email | sms | in-app
    "is_read": bool,
    "is_sent": bool,
    "sent_at": datetime,
    "created_at": datetime,
}

# ── Audit Log ─────────────────────────────────────────────────
AUDIT_LOG_SCHEMA = {
    "_id": ObjectId,
    "user_id": ObjectId,
    "action": str,                  # login | logout | upload | delete | ...
    "resource": str,                # which API endpoint / resource
    "resource_id": str,
    "ip_address": str,
    "user_agent": str,
    "status": str,                  # success | failure
    "details": dict,
    "timestamp": datetime,
}

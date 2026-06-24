# Admin Manual

## Admin Panel Overview

Log in with an `admin`-role account to see the **Admin** section in the sidebar:
Admin Panel, Upload PDF/Excel/CSV, Documents, Users, Analytics, Reports, System Health.

## Uploading Institutional Data

### PDFs (policies, circulars, syllabi, brochures)
**Admin → Upload PDF.** The file is text-extracted, cleaned, chunked (~800 chars,
150 overlap), embedded with `all-MiniLM-L6-v2`, and stored in ChromaDB. Once
processed, any user can ask about it in **AI Chat** and get cited answers.

> If a PDF is a scanned image (no extractable text), the Question Paper Analyzer
> pipeline's OCR fallback can still pull text out — but for general document RAG,
> prefer text-based PDFs for best chunk quality.

### Excel / CSV (attendance, placements, fees, results, students, faculty, timetable)
**Admin → Upload Excel/CSV.** The platform auto-detects sheet type from column
names and runs type-specific analysis immediately (attendance %, top performers,
package stats, etc.) Use the natural-language query box on the CSV page, or the
**Analytics** page's MongoDB query tool, to ask follow-up questions.

### Bulk Student Import
`POST /api/students/bulk-upload` (or build a UI flow around it) accepts an Excel/CSV
with a `student_id` and `email` column at minimum — duplicates are skipped, not
overwritten.

## User Management

**Admin → Users**: search, filter by role, activate/deactivate, delete, and change
roles. You cannot delete your own account (safety guard). Every role change and
deactivation is recorded in the audit log.

## Documents Management

**Admin → Documents**: see every uploaded file, its processing status, chunk
count, and re-process or delete it. Deleting a document also removes its vectors
from ChromaDB — it's not just a soft delete.

## Training ML Models

`POST /api/ml/train` (admin only) retrains all three trainable models
(attendance risk, CGPA trend, placement probability) from current MongoDB data.
Run this periodically (e.g. monthly, or after a bulk data import) — each model
needs at least ~20 records to train; below that it reports `insufficient_data`
and the platform keeps using heuristic fallbacks.

## Notifications

`POST /api/notifications/send/attendance-alert` bulk-emails every student below
a configurable threshold (default 75%). Requires `MAIL_*` environment variables
to be configured. SMS alerts additionally require `TWILIO_*` variables.

## System Health & Audit

- **Admin → System Health**: live status of MongoDB, ChromaDB, and Ollama, plus
  collection record counts.
- **Admin → Reports**: filterable audit log of every sensitive action (logins,
  uploads, deletes, role changes) with actor, IP, and timestamp.

## Common Operational Tasks

| Task | How |
|---|---|
| Reset a user's password | No self-service reset flow yet — have them use Change Password after you reactivate/recreate, or extend `PUT /api/users/<id>/role`-style endpoint with a password-reset variant |
| Re-index a document after editing the source PDF | Re-upload, or use `POST /api/documents/<id>/reprocess` if the file on disk was replaced directly |
| Check why Ollama answers are generic/wrong | Verify `ollama list` shows `qwen3:8b`; check `/api/health` for `ollama.status` |
| Free up disk space | Delete unused documents via Admin → Documents (removes both file and vectors) |

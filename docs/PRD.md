# Product Requirements Document (PRD)
## AI Campus Intelligence Platform

**Version:** 1.0.0 | **Status:** Implemented (Phases 1–17 complete)

---

## 1. Overview

The AI Campus Intelligence Platform is a unified, AI-powered educational operating
system for colleges and universities. It consolidates document intelligence, data
analytics, predictive modelling, and conversational AI into a single web application,
using **only local, self-hosted LLMs** (Qwen 3 via Ollama) — no third-party AI API
dependency, no per-token billing, and full data sovereignty for sensitive student records.

## 2. Problem Statement

Colleges run dozens of disconnected systems: attendance registers, placement
spreadsheets, library software, hostel logs, and PDF circulars buried in email
threads. Students and staff waste time hunting for information that already exists
somewhere in institutional data. There is no single place to *ask a question* and
get a grounded, cited answer.

## 3. Goals

| Goal | Success Metric |
|---|---|
| Unify data access behind one chat interface | >80% of common queries answered without manual lookup |
| Keep all AI inference local/private | Zero calls to paid external LLM APIs |
| Make analytics self-service | Non-technical staff can ask NL questions of Excel/CSV/MongoDB data |
| Predict at-risk students early | Attendance/CGPA/placement risk flagged before mid-semester |
| Maintain auditability | Every sensitive action logged with actor, timestamp, IP |

## 4. Target Users

- **Students** — check attendance, CGPA, placements, library, hostel, events; ask the AI assistant anything.
- **Faculty** — view class-level attendance/academic analytics, flag at-risk students.
- **Admins** — upload institutional documents/datasets, manage users, view audit logs, monitor system health.

## 5. Core Feature Set

See the [README](../README.md#features) for the full list. In summary: PDF RAG QA,
Excel/CSV analytics with NL query, MongoDB NL query, OCR + question paper analysis,
resume ATS scoring, a 9-agent multi-agent router, ML-based risk prediction, and
email/SMS notifications.

## 6. Non-Functional Requirements

- **Privacy**: All LLM inference runs locally via Ollama; no student data leaves the institution's infrastructure.
- **Security**: JWT auth, bcrypt password hashing, RBAC (admin/faculty/student), rate limiting, audit logging, input validation on every endpoint.
- **Performance**: API responses <2s for non-LLM endpoints; LLM-backed endpoints stream where possible.
- **Test coverage**: >80% backend coverage enforced in CI.
- **Deployability**: Single `docker compose up` brings up the full stack including the LLM runtime.

## 7. Out of Scope (v1.0)

- Mobile native apps (web is responsive but no iOS/Android build)
- Multi-tenant SaaS (this is a single-institution deployment model)
- Payment gateway integration for fees (fee *tracking* only, not *collection*)
- Real-time video proctoring / exam features

## 8. Success Criteria for Launch

- All 17 build phases complete with passing tests (✅ done — see [Testing Report](./TESTING_REPORT.md))
- Docker Compose stack starts cleanly with `docker compose up --build`
- Seed data + dev credentials work end-to-end (login → chat → upload → query)

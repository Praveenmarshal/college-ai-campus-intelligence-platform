# API Documentation

Base URL (dev): `http://localhost:5000`
All endpoints are prefixed `/api`. Authenticated endpoints require
`Authorization: Bearer <access_token>`.

**Response envelope** (all endpoints):
```json
{ "success": true, "message": "...", "data": { ... } }
{ "success": false, "error": "...", "details": { ... } }
```

---

## Auth — `/api/auth`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/register` | — | Create account, returns tokens |
| POST | `/login` | — | `{email, password}` → tokens |
| POST | `/refresh` | refresh token | New access token |
| POST | `/logout` | ✅ | Revoke refresh token |
| GET | `/me` | ✅ | Current user profile |
| PUT | `/change-password` | ✅ | `{current_password, new_password}` |
| POST | `/seed` | — (dev only) | Seeds 3 demo accounts |

## Users — `/api/users`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `` | admin | List users, paginated, `?role=&search=` |
| GET | `/stats` | admin | Counts by role |
| GET | `/<id>` | admin | Get one user |
| PUT | `/profile` | ✅ | Update own name/phone/department |
| PUT | `/<id>/role` | admin | Change role |
| PUT | `/<id>/status` | admin | `{is_active: bool}` |
| DELETE | `/<id>` | admin | Delete user |

## Documents (PDF RAG) — `/api/documents`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/upload/pdf` | admin | Upload + chunk + embed a PDF |
| GET | `` | ✅ | List documents, `?file_type=&search=` |
| GET | `/<id>` | ✅ | Document detail |
| DELETE | `/<id>` | admin | Delete doc + its vectors |
| POST | `/<id>/reprocess` | admin | Re-run RAG pipeline |

## Chat — `/api/chat`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/message` | ✅ | `{message, session_id?}` → RAG answer |
| GET | `/sessions` | ✅ | List my chat sessions |
| GET | `/sessions/<id>` | ✅ | Full session with messages |
| DELETE | `/sessions/<id>` | ✅ | Delete one session |
| DELETE | `/sessions` | ✅ | Clear all sessions |

## Excel — `/api/excel`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/upload` | admin | Upload + auto-analyse workbook |
| GET | `` | ✅ | List Excel uploads |
| GET | `/<id>` | ✅ | Re-run analysis on stored file |
| POST | `/<id>/query` | ✅ | `{question, sheet_name?}` NL query |

## CSV — `/api/csv`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/upload` | admin | Upload + profile a CSV |
| GET | `` | ✅ | List CSV uploads |
| GET | `/<id>` | ✅ | Re-run profiling |
| POST | `/<id>/query` | ✅ | `{question}` NL query |

## MongoDB NL Query — `/api/mongo-query`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/collections` | ✅ | Allowed collections + fields |
| POST | `/ask` | ✅ | `{question, collection}` → aggregation result |

## Smart Router / Multi-Agent — `/api/router`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/ask` | ✅ | `{query, session_id?, context?}` — classify + dispatch |
| POST | `/ask-hybrid` | ✅ | `{query, max_agents?}` — combine multiple agents |
| GET | `/agents` | ✅ | List all 9 agents |
| POST | `/classify` | ✅ | Debug: classify only, no execution |

## Resume — `/api/resume`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/analyze` | ✅ | Upload PDF resume `+target_role?` → ATS analysis |
| GET | `/<id>` | ✅ | Retrieve cached analysis |

## OCR — `/api/ocr`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/extract` | ✅ | Image/scanned PDF → raw text |
| POST | `/question-paper/analyze` | ✅ | Single paper → topics/difficulty |
| POST | `/question-paper/trends` | admin | Multiple papers (`files[]`) → frequency analysis |

## Machine Learning — `/api/ml`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/predict/<student_id>` | ✅ | All 4 predictions combined |
| GET | `/predict/attendance/<id>` | ✅ | Attendance risk |
| GET | `/predict/cgpa/<id>` | ✅ | CGPA trend |
| GET | `/predict/placement/<id>` | ✅ | Placement probability |
| GET | `/predict/fee-default/<id>` | ✅ | Fee default risk |
| POST | `/train` | admin | Retrain all models |
| GET | `/at-risk-students` | faculty/admin | List students below 75% attendance |

## Analytics — `/api/analytics`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/dashboard` | ✅ | High-level counts |
| GET | `/attendance` | ✅ | By-department + 30-day trend |
| GET | `/placements` | ✅ | Overall + by-year + top recruiters |
| GET | `/academic` | ✅ | By-department CGPA + top performers |
| GET | `/system` | faculty/admin | Document storage breakdown |

## Students — `/api/students`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `` | ✅ | List, paginated, filterable |
| GET | `/me` | ✅ | My own student profile |
| GET | `/<id>` | ✅ | Get one |
| POST | `` | admin | Create |
| PUT | `/<id>` | faculty/admin | Update |
| DELETE | `/<id>` | admin | Delete |
| POST | `/bulk-upload` | admin | Bulk create from Excel/CSV |

## Faculty — `/api/faculty`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `` | ✅ | List |
| GET | `/me` | ✅ | My own faculty profile |
| GET | `/<id>` | ✅ | Get one |
| POST | `` | admin | Create |
| PUT | `/<id>` | admin | Update |
| DELETE | `/<id>` | admin | Delete |

## Notifications — `/api/notifications`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `` | ✅ | List, `?unread_only=true` |
| GET | `/unread-count` | ✅ | Badge count |
| PUT | `/<id>/read` | ✅ | Mark one read |
| PUT | `/read-all` | ✅ | Mark all read |
| DELETE | `/<id>` | ✅ | Delete |
| POST | `/send/attendance-alert` | admin | Bulk attendance alert blast |

## Admin — `/api/admin`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/audit-logs` | admin | `?limit=&action=` |
| GET | `/system-overview` | admin | Collection counts + ChromaDB health |

## Health — `/api`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | — | MongoDB + ChromaDB + Ollama status |
| GET | `/health/ping` | — | Liveness probe |

---

## Error Codes

| HTTP | Meaning |
|---|---|
| 400 | Bad request / business rule violation |
| 401 | Missing/invalid/expired token |
| 403 | Authenticated but insufficient role |
| 404 | Resource not found |
| 409 | Conflict (e.g. duplicate email) |
| 413 | File too large (>50MB) |
| 422 | Validation failed (see `details`) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 503 | Dependent service unavailable (e.g. Ollama down) |

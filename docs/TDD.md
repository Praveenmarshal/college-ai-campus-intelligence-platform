# Technical Design Document (TDD)
## AI Campus Intelligence Platform

---

## 1. Architecture Overview

The platform follows a **layered, agent-oriented architecture**:

```
React SPA (Vite) → Flask REST API → Service Layer → {MongoDB, ChromaDB, Ollama}
```

- **Presentation**: React 18 + Tailwind, talking to the backend exclusively over `/api/*` JSON REST endpoints, authenticated with JWT.
- **API**: Flask blueprints, one per domain (auth, documents, chat, analytics, students, faculty, admin, notifications, excel, csv, mongo-query, router, resume, ml, ocr, health).
- **Service layer**: Pure Python modules under `services/`, `rag/`, and `agents/` — framework-agnostic, independently testable.
- **Data layer**: MongoDB Atlas (operational data), ChromaDB (vector embeddings), local filesystem (uploaded files), joblib (trained ML models).
- **AI layer**: Ollama running Qwen 3 8B/14B locally; all prompts are crafted server-side with explicit system prompts per use case (RAG, NL→pandas, NL→Mongo, resume analysis, topic extraction, intent classification).

## 2. Backend Design

### 2.1 Clean Architecture Layering

```
routes/      → HTTP concerns only (parsing requests, calling services, shaping responses)
models/      → MongoDB document schemas + Marshmallow validators + response helpers
services/    → Business logic, framework-agnostic
rag/         → PDF processing, embeddings, vector store, LLM client, RAG orchestration
agents/      → 9 specialised agents + orchestrator (Phase 8)
config/      → Settings, DB connections, logging — environment-driven
```

Each route handler is intentionally thin: validate → call service → return standard
JSON envelope (`models/response.py`). This keeps business logic unit-testable without
spinning up Flask.

### 2.2 Authentication & RBAC

- Passwords hashed with **bcrypt** (12 rounds).
- **JWT** access tokens (1hr) + refresh tokens (30 days), with refresh-token JTI
  tracked per-user in MongoDB so logout/password-change can revoke sessions server-side.
- `@roles_required("admin")` / `@admin_required` / `@faculty_or_admin_required` /
  `@active_user_required` decorators in `services/auth_service.py` enforce RBAC
  declaratively on each route.

### 2.3 PDF RAG Pipeline (Phase 3)

```
Upload → PDFProcessor.extract_text() (pdfplumber, pypdf fallback)
       → clean_text() (ligature fix, whitespace, page-number stripping)
       → chunk_text() (800 chars, 150 overlap, sentence-boundary aware)
       → embed_chunks() (all-MiniLM-L6-v2, 384-dim, normalised)
       → VectorStore.add_chunks() (ChromaDB, cosine similarity)

Query  → embed_text(query) → VectorStore.query(top_k=5)
       → build_context() → Qwen 3 chat completion with citation-aware system prompt
       → { answer, sources[], context_used }
```

### 2.4 Smart Query Router & Multi-Agent System (Phases 7–8)

`QueryRouter.classify()` first tries **fast keyword matching** against per-agent
keyword signatures (near-zero latency, no LLM call). If confidence is below
threshold (0.4), it falls back to an **LLM classification call** (Qwen, temperature
0, 20 max tokens) that returns just the agent name. `AgentOrchestrator.dispatch()`
then lazily instantiates and invokes the chosen agent. `route_hybrid()` supports
combining 2+ agents for cross-domain questions.

Each of the 9 agents implements `BaseAgent.handle(query, context) -> dict` with a
uniform response contract, making it trivial to add a 10th agent later.

### 2.5 Natural Language → Structured Query (Phases 4–6)

Both `NLQueryEngine` (pandas, Excel/CSV) and `MongoQueryEngine` (MongoDB
aggregation) follow the same pattern: **the LLM only ever outputs a constrained
JSON spec**, never executable code. The spec is then validated and executed by
hand-written, whitelisted Python — `MongoQueryEngine` explicitly rejects
`$where`/`$function`/`$accumulator` to prevent server-side JS injection via prompt
injection.

### 2.6 ML Prediction Service (Phase 11)

`Predictor` trains/serves four models (Random Forest for attendance & CGPA, XGBoost
for placement, rule-based heuristic for fee default — insufficient historical
default labels to train a classifier yet). Every predictor has a **heuristic
fallback** so the platform is useful from day one before enough data accumulates
to train (cold-start friendly), and gracefully degrades if `joblib` model files
are absent.

### 2.7 OCR Pipeline (Phase 12)

EasyOCR is primary (better accuracy), Tesseract is the fallback (lighter, no GPU).
Scanned PDFs are detected when `PDFProcessor.extract_text()` returns empty text,
then routed through `pdf2image` → per-page OCR → reassembled text.

## 3. Frontend Design

- **State**: React Context (Auth, Theme, Chat) — no Redux; app is not complex enough to need it.
- **Routing**: React Router v6 with `<ProtectedRoute>` (auth gate) and `<RoleRoute>` (RBAC gate) wrapping role-specific routes.
- **API layer**: single Axios instance (`api/client.js`) with automatic access-token refresh on 401, request/response interceptors, and a `services.js` barrel exporting one object per domain.
- **Design system**: Tailwind config with custom primary/accent palettes, dark mode via `class` strategy, reusable component classes (`.btn-primary`, `.card`, `.badge-*`) defined once in `assets/index.css`.

## 4. Data Model

See [`backend/models/schemas.py`](../backend/models/schemas.py) for all 15 MongoDB
collection schemas (logical, not enforced by MongoDB itself — validated at the
application layer via Marshmallow where it matters, e.g. auth).

## 5. Security Model

| Concern | Mitigation |
|---|---|
| SQL/NoSQL injection | No raw `eval()`; NL→query engines emit constrained JSON specs, executed via whitelisted operations only |
| Prompt injection → code execution | `$where`/`$function` blocked in MongoDB pipelines; pandas queries never use `eval()`/`exec()` |
| Password storage | bcrypt, 12 rounds |
| Session hijacking | Short-lived access tokens, revocable refresh tokens (JTI tracking) |
| File upload abuse | Extension + MIME allowlist, 50MB cap, safe filename generation (UUID-prefixed) |
| Brute force | Flask-Limiter rate limiting (100 req/hr default) |
| Privilege escalation | Declarative RBAC decorators on every sensitive route; self-deletion/self-demotion blocked |
| Audit trail | Every sensitive action (login, upload, delete, role change) logged with actor/IP/timestamp |

## 6. Deployment Topology

See [docker-compose.yml](../docker-compose.yml): `frontend` (Nginx + static React
build) → `nginx` (reverse proxy, optional TLS termination) → `backend` (Gunicorn +
Flask) → `mongo` / `ollama` / `redis` as backing services. `ollama-init` is a
one-shot container that pulls `qwen3:8b` on first boot.

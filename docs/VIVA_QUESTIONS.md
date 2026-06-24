# Viva Questions & Answers

*Prepared for final-year project defense / technical review.*

---

### General / Architecture

**Q1. What problem does this project solve?**
It unifies fragmented campus information systems (attendance registers, placement
sheets, library logs, PDF circulars) behind a single conversational AI interface,
so students/faculty/admins can ask plain-English questions instead of manually
hunting through spreadsheets and documents.

**Q2. Why a local LLM (Qwen 3 via Ollama) instead of OpenAI/Gemini?**
Three reasons: (1) **data privacy** — student records never leave institutional
infrastructure; (2) **cost** — no per-token billing at scale across an entire
college; (3) **availability** — works without internet access to a third-party
API, important for institutions with restricted connectivity policies.

**Q3. Walk me through the high-level architecture.**
React SPA → Flask REST API (JWT-secured) → service layer (RAG pipeline, NL query
engines, ML predictor, 9 specialised agents) → MongoDB (operational data) +
ChromaDB (vector embeddings) + Ollama (local LLM inference). See
[DIAGRAMS.md](./DIAGRAMS.md) for the full flowchart.

**Q4. Why Clean Architecture / layered design here specifically?**
`routes/` only handle HTTP concerns; all logic lives in `services/`, `rag/`, and
`agents/`, which are plain Python with no Flask dependency. This means the RAG
pipeline, ML predictor, and agents can all be unit-tested without spinning up a
web server, and the business logic could be reused in a CLI tool or batch job
without modification.

---

### RAG / AI

**Q5. Explain the RAG pipeline end to end.**
Upload → `pdfplumber`/`pypdf` extracts raw text → `clean_text()` strips ligatures,
page numbers, excess whitespace → `chunk_text()` splits into ~800-character
chunks with 150-character overlap, preferring sentence boundaries → each chunk is
embedded with `all-MiniLM-L6-v2` (384-dim) → stored in ChromaDB with cosine
similarity. At query time: embed the question → retrieve top-5 chunks → build a
context block → send to Qwen 3 with a citation-aware system prompt → return the
answer plus a `sources[]` list referencing which files were used.

**Q6. Why overlap chunks instead of splitting cleanly?**
Without overlap, a sentence split exactly at a chunk boundary loses context on
both sides — overlap (150 chars here) ensures information near a boundary still
appears whole in at least one chunk, improving retrieval recall.

**Q7. How does the Smart Query Router decide which of the 9 agents to call?**
Two-stage: first, fast keyword matching against per-agent keyword signatures
(`services/query_router.py::ROUTE_KEYWORDS`) — free, instant, no LLM call. If
confidence is below 0.4 (fewer than ~1 keyword hit normalised), it falls back to
an LLM classification call (Qwen, temperature 0, 20 max tokens, constrained to
return only one of the valid agent names).

**Q8. How do you prevent prompt injection from executing arbitrary code via the NL-to-MongoDB feature?**
The LLM is *only* allowed to emit a constrained JSON aggregation pipeline — never
raw JS or Python. `MongoQueryEngine._validate_pipeline()` explicitly scans the
serialised pipeline for `$where`, `$function`, and `$accumulator` (MongoDB's
code-execution operators) and rejects the query if found, regardless of what the
LLM was tricked into generating.

**Q9. What happens if Ollama is down?**
Every LLM-dependent service has a defined failure mode rather than crashing:
`RAGPipeline.answer()` catches `RuntimeError` and returns a friendly "can't reach
the local AI model" message; `ResumeAnalyzer` and `Predictor` fall back to
heuristic (non-LLM) logic; `/api/health` surfaces Ollama's status explicitly so
admins can diagnose it.

---

### Data & ML

**Q10. How does the Excel/CSV "ask in plain English" feature work without using `eval()`?**
The LLM converts the question into a small constrained JSON spec (operation,
column, filter, aggregation function) — never executable code. A hand-written
Python function (`NLQueryEngine.execute_query`) then maps that spec onto
whitelisted pandas operations (`.groupby()`, `.sort_values()`, boolean filtering).
This is safe against prompt injection because the LLM's output is *data*, not
*code*.

**Q11. How are the ML prediction models trained, and what do you do with insufficient data?**
Random Forest for attendance risk and CGPA trend, XGBoost for placement
probability — trained from MongoDB aggregation queries joining students/
attendance/placements. Each training function checks for a minimum sample size
(~15-20 records) and returns `{"status": "insufficient_data"}` rather than
training a garbage model. All four predictors (including fee-default, which is
heuristic-only by design — no historical default labels exist yet) have a
rule-based fallback so predictions are still useful before enough data
accumulates.

**Q12. Why is fee-default prediction heuristic instead of ML-based?**
There's no historical "did this student actually default" label in the schema
yet — fee records track due/paid amounts, not eventual default outcome. Training
a classifier without ground-truth labels would just be reproducing the heuristic
with extra steps, so it's implemented directly as a rule (overdue count + 
outstanding amount thresholds) with a clear TODO for once default-outcome data
exists.

---

### Security

**Q13. How is authentication implemented?**
JWT access tokens (1hr expiry) + refresh tokens (30 days). Passwords are hashed
with bcrypt at 12 rounds. Refresh tokens are tracked server-side by JTI
(JWT ID) per user, so logout or password change can immediately revoke a
session rather than just relying on client-side token deletion.

**Q14. How is RBAC enforced?**
Declaratively, via Python decorators (`@admin_required`,
`@faculty_or_admin_required`, `@roles_required(...)`) applied directly to route
functions. The decorator reads the `role` claim embedded in the JWT and returns
403 before the route body ever executes if the role doesn't match.

**Q15. What's in the audit log, and why?**
Every sensitive action — login, login failure, register, logout, password
change, document upload/delete, role change, user activation/deactivation, bulk
operations — is written to an `audit_logs` collection with actor, IP, user agent,
and timestamp. This supports compliance requirements and incident investigation
without needing to reconstruct events from application logs.

---

### Testing & DevOps

**Q16. What's your test coverage strategy?**
120 backend tests split between pure unit tests (chunking algorithms, validators,
keyword classifiers, heuristic fallbacks — fast, no external dependencies) and
API integration tests (full HTTP request/response cycles via Flask's test
client). CI enforces an 80% coverage floor via `pytest-cov --cov-fail-under=80`.

**Q17. How do tests pass in CI without a running Ollama instance?**
Every AI-dependent service was designed with a non-LLM fallback path from the
start (not bolted on for testing) — the test suite specifically exercises those
fallback paths, proving the system degrades gracefully. This was a deliberate
architectural choice, not a testing workaround.

**Q18. Describe the deployment topology.**
Docker Compose orchestrates: `frontend` (Nginx serving the built React app),
`backend` (Gunicorn + Flask, 4 workers), `mongo`, `ollama` (+ a one-shot
`ollama-init` container that pulls `qwen3:8b` on first boot), `redis` (rate
limiting backend), and an optional top-level `nginx` reverse proxy for TLS
termination.

**Q19. How would you scale this for a larger institution?**
Horizontally scale `backend` replicas behind the Nginx upstream (stateless
Flask app, sessions live in MongoDB/JWT not server memory). Ollama inference is
the most likely bottleneck — would move it to a dedicated GPU host. ChromaDB's
embedded file-based mode would need to move to client/server mode under high
concurrent write load.

**Q20. What would you improve given more time?**
Streaming token-by-token responses in the chat UI (the backend has
`chat_stream()` implemented in `LLMClient` but it isn't wired into the chat
route yet); a proper password-reset-via-email flow; moving the in-memory Excel/
CSV DataFrame cache to Redis so it survives backend restarts and works across
multiple replicas; and real labelled fee-default data to train that predictor
properly instead of the current heuristic.

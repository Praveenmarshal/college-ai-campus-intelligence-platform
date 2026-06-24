# Testing Report

## Summary

| Metric | Value |
|---|---|
| Total backend test functions | 120 |
| Test files | 6 |
| Test types | Unit, API/integration |
| Target coverage | >80% (enforced in CI via `pytest-cov --cov-fail-under=80`) |
| Frontend test runner | Vitest + Testing Library (configured, scaffolded in `vite.config.js`) |
| E2E runner | Playwright (configured in CI pipeline) |

## Test Breakdown by Phase

| File | Phase(s) covered | Test count | Focus |
|---|---|---|---|
| `tests/unit/test_phase1_setup.py` | 1 | 21 | App factory, config classes, health endpoints, file utils, response helpers |
| `tests/api/test_auth.py` | 2 | 29 | Register/login/refresh/logout/me/change-password, RBAC, validators, password hashing |
| `tests/unit/test_phase3_rag.py` | 3 | 17 | PDF text cleaning, chunking, vector store interface, RAG context building, LLM client config |
| `tests/unit/test_phase4_6_analytics.py` | 4, 5, 6 | 24 | Excel sheet detection/analysis, CSV profiling/type inference, NL→pandas execution, MongoDB pipeline safety validation |
| `tests/unit/test_phase7_9_agents.py` | 7, 8, 9 | 16 | Query router keyword classification, agent orchestrator dispatch, base agent contract, resume analyzer fallback |
| `tests/unit/test_phase11_13_ml_ocr_notify.py` | 11, 12, 13 | 13 | ML predictor heuristic fallbacks, OCR interface, question paper frequency analysis, notification templates |

## Testing Strategy

### Unit tests
Pure-function and class-level tests that don't require a live MongoDB/ChromaDB/Ollama
connection — these test business logic (chunking algorithms, validation schemas,
keyword classifiers, heuristic fallbacks) in isolation. The majority of the 120
tests fall into this category, which keeps the suite fast and CI-friendly.

### API / integration tests
`tests/api/test_auth.py` exercises full HTTP request/response cycles through the
Flask test client (`client.post(...)`, `client.get(...)`), validating status
codes, response shapes, and side effects (token issuance, audit logging).

### Why heuristic-fallback testing matters
Every AI/ML-dependent service (`Predictor`, `ResumeAnalyzer`, `QuestionPaperAnalyzer`)
was deliberately designed with **non-LLM fallback paths**, and those fallback
paths are what's unit-tested — this means the test suite passes in CI **without**
requiring a running Ollama instance or trained ML models, while still proving the
platform degrades gracefully rather than crashing when those dependencies are
unavailable.

### What requires manual / staging verification
The following are exercised by the test suite at the *interface* level (mocked or
fallback-path) but should be manually verified against a live stack before
production sign-off:
- End-to-end RAG answer quality with a real Qwen 3 model
- ChromaDB persistence across container restarts
- Email/SMS delivery (requires real SMTP/Twilio credentials)
- OCR accuracy on real scanned documents (EasyOCR/Tesseract are not mocked, but
  no test fixtures with real scanned images are bundled)
- ML model training accuracy with realistic data volumes (test fixtures use
  synthetic minimal data)

## Running the Suite

```bash
cd backend
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing -v
open htmlcov/index.html   # visual coverage report
```

## CI Pipeline

See [`.github/workflows/ci.yml`](../.github/workflows/ci.yml):
1. `backend-test` — flake8 lint, black format check, pytest with coverage gate
2. `frontend-test` — ESLint, Vitest, production build check
3. `docker-build` — builds and pushes both images (main branch only, after tests pass)

# 🎓 AI Campus Intelligence Platform

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![React](https://img.shields.io/badge/React-18.3-blue)
![License](https://img.shields.io/badge/license-MIT-purple)
![LLM](https://img.shields.io/badge/LLM-Qwen3_8B_(Local)-orange)

**A unified AI-powered educational operating system built on local LLMs.**

[Features](#features) · [Tech Stack](#tech-stack) · [Quick Start](#quick-start) · [Architecture](#architecture) · [Phases](#build-phases)

</div>

---

## Features

| Module | Description |
|---|---|
| 🤖 **PDF RAG Engine** | Upload PDFs, ask questions, get cited answers via Qwen 3 |
| 📊 **Excel / CSV Analytics** | Upload datasets, generate charts, query in plain English |
| 🗄️ **MongoDB NL Query** | Ask questions about students, placements, fees in natural language |
| 👁️ **OCR Engine** | Process scanned documents and images with EasyOCR + Tesseract |
| 📄 **Resume Analyzer** | ATS scoring, skill gap analysis, job role matching |
| 📈 **Placement Analytics** | Trends, company stats, package analysis |
| 📅 **Attendance Analytics** | Per-student, per-course, at-risk detection |
| 🧠 **Multi-Agent AI** | 9 specialised agents routed by a smart query classifier |
| 🔮 **ML Predictions** | Attendance, CGPA, placement, fee default prediction |
| 📚 **Library / Hostel / Events** | Module-specific assistants |
| 🔔 **Notifications** | Email (SMTP) + SMS (Twilio) alerts |
| 📋 **Report Generator** | PDF and Excel export for all analytics |

---

## Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Framework | Flask 3.0 + Gunicorn |
| Database | MongoDB Atlas (PyMongo) |
| Vector DB | ChromaDB |
| LLM | Qwen 3 8B via Ollama (local) |
| Embeddings | all-MiniLM-L6-v2 (Sentence Transformers) |
| ML | Scikit-learn, XGBoost |
| OCR | EasyOCR + Tesseract |
| Auth | Flask-JWT-Extended + bcrypt |

### Frontend
| Layer | Technology |
|---|---|
| Framework | React 18 + Vite |
| Styling | Tailwind CSS |
| Routing | React Router v6 |
| HTTP | Axios |
| Charts | Recharts + Chart.js |
| State | Context API |

---

## Project Structure

```
college-ai-campus-intelligence-platform/
├── .env.example          ← committed (placeholders only)
├── .env                  ← YOUR FILE — gitignored, never committed, holds real secrets
├── .gitignore
├── .gitleaks.toml        ← secret-scanning rules (CI)
├── .githooks/
│   └── pre-commit        ← blocks committing .env / secret-shaped strings
├── SECURITY.md           ← how secrets are handled, what to do if one leaks
├── scripts/
│   └── setup-env.sh      ← generates .env with strong random secrets
├── README.md
├── docker-compose.yml
├── backend/
│   ├── app.py             (Flask factory — validates secrets on prod startup)
│   ├── config/             (settings, database, ChromaDB, logging)
│   ├── routes/             (17 blueprints — auth, chat, documents, ML, OCR, etc.)
│   ├── models/             (MongoDB schemas, validators, response helpers)
│   ├── services/           (Excel/CSV/OCR/ML/notification business logic)
│   ├── rag/                (PDF processing, embeddings, vector store, LLM client)
│   ├── agents/             (9 specialised AI agents + orchestrator)
│   ├── tests/               (120 tests)
│   └── uploads/, chroma_db/, logs/   ← gitignored — runtime-generated data
├── frontend/
│   └── src/
│       ├── pages/          (30 route pages)
│       ├── components/     (layout, common, charts)
│       ├── context/        (Auth, Theme, Chat)
│       └── api/             (Axios client + service modules)
├── docker/                 (Dockerfiles, nginx configs, mongo-init.js)
├── docs/                   (PRD, TDD, diagrams, API reference, guides)
└── .github/workflows/      (CI: secret-scan → backend-test → frontend-test → docker-build)
```

**What never gets committed** (enforced by `.gitignore` + pre-commit hook + CI scan):
`.env`, `uploads/`, `chroma_db/`, `logs/`, trained `*.pkl`/`*.joblib` model files,
`node_modules/`, `__pycache__/`.

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- MongoDB Atlas account (or local MongoDB)
- [Ollama](https://ollama.ai) installed locally
- Tesseract OCR installed

### 1. Clone & set up your secrets safely

```bash
git clone https://github.com/your-org/college-ai-campus-intelligence-platform.git
cd college-ai-campus-intelligence-platform

# Auto-generates .env with strong random secrets (never committed to git)
bash scripts/setup-env.sh

# Then edit .env to add your real MongoDB URI / email / Twilio credentials
```

> 🔒 **Before you push to GitHub**, run `git config core.hooksPath .githooks`
> once to enable a pre-commit check that blocks `.env` and obvious secrets
> from ever being staged. Full details in [SECURITY.md](./SECURITY.md).
> The repo's `.env.example` only ever contains placeholders — your real
> `.env` is gitignored and stays on your machine / deployment server only.

### 2. Pull Qwen 3 model

```bash
ollama pull qwen3:8b
# For better quality (needs more RAM):
ollama pull qwen3:14b
```

### 3. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run development server
flask run --port 5000
```

### 4. Frontend setup

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

### 5. Docker (recommended for production)

```bash
docker compose up --build
# Frontend: http://localhost
# Backend:  http://localhost:5000
```

### 6. Want a free hosted demo instead?

Skip Docker/Ollama entirely and deploy to **Vercel (frontend) + Render
(backend) + MongoDB Atlas + Groq** — all free, no credit card needed.
Full walkthrough: [`docs/DEPLOY_FREE_TIER.md`](./docs/DEPLOY_FREE_TIER.md).

> This swaps local Ollama for Groq's free hosted LLM API (Render's free tier
> can't run Ollama — no GPU/RAM for it). Good for demos and project
> submissions; for real student data, use the self-hosted Docker setup above
> instead — see [Limitations](./docs/DEPLOY_FREE_TIER.md#limitations-of-this-setup).

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  React Frontend                      │
│  (Vite + Tailwind + React Router + Axios + Charts)  │
└───────────────────────┬─────────────────────────────┘
                        │ REST API (JWT)
┌───────────────────────▼─────────────────────────────┐
│                 Flask Backend                         │
│                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ Smart Router│  │ Agent System │  │ Auth / JWT │  │
│  └──────┬──────┘  └──────┬───────┘  └────────────┘  │
│         │                │                           │
│  ┌──────▼──────────────▼──────────────────────────┐ │
│  │              Service Layer                      │ │
│  │  PDF RAG │ Excel │ CSV │ OCR │ Resume │ ML     │ │
│  └──────────────────────────────────────────────── ┘ │
└───────────┬──────────────┬──────────────┬────────────┘
            │              │              │
    ┌───────▼────┐  ┌──────▼──────┐  ┌───▼──────────┐
    │  MongoDB   │  │  ChromaDB   │  │  Ollama/Qwen  │
    │  Atlas     │  │  (vectors)  │  │  (local LLM) │
    └────────────┘  └─────────────┘  └──────────────┘
```

---

## Build Phases — All Complete ✅

| Phase | Module | Status |
|---|---|---|
| 1 | Project Setup & Scaffolding | ✅ Complete |
| 2 | Authentication System | ✅ Complete |
| 3 | PDF RAG Engine | ✅ Complete |
| 4 | Excel Analytics Engine | ✅ Complete |
| 5 | CSV Analytics Engine | ✅ Complete |
| 6 | MongoDB Query Engine | ✅ Complete |
| 7 | Smart Query Router | ✅ Complete |
| 8 | Multi-Agent Architecture | ✅ Complete |
| 9 | Resume Analyzer | ✅ Complete |
| 10 | Dashboards & Analytics UI | ✅ Complete |
| 11 | Machine Learning Modules | ✅ Complete |
| 12 | OCR Engine | ✅ Complete |
| 13 | Notification Engine | ✅ Complete |
| 14 | Testing Suite (120 tests) | ✅ Complete |
| 15 | Docker & Containerisation | ✅ Complete |
| 16 | CI/CD & Deployment | ✅ Complete |
| 17 | Documentation | ✅ Complete |

📚 Full documentation index: [`docs/`](./docs) — PRD, TDD, architecture/ER/sequence
diagrams, API reference, deployment guide, user & admin manuals, testing report,
and viva Q&A.

---

## API Overview

Base URL: `http://localhost:5000/api`

17 route modules, 90+ endpoints covering auth, documents, chat, Excel/CSV
analytics, MongoDB NL query, the smart router + 9 agents, resume analysis, OCR,
ML predictions, students, faculty, admin, and notifications.

**Full reference:** [`docs/API_DOCUMENTATION.md`](./docs/API_DOCUMENTATION.md)

Quick examples:

| Endpoint | Description |
|---|---|
| `POST /auth/login` | Login, receive JWT tokens |
| `POST /chat/message` | Send message → RAG-powered answer |
| `POST /router/ask` | Smart-routed query across 9 specialised agents |
| `POST /documents/upload/pdf` | Upload PDF → chunked, embedded, indexed |
| `POST /excel/upload` | Upload workbook → auto-analysed |
| `POST /mongo-query/ask` | Ask MongoDB data in plain English |
| `POST /resume/analyze` | ATS score + skill gap analysis |
| `GET /ml/predict/<student_id>` | Attendance/CGPA/placement/fee-risk prediction |
| `GET /analytics/dashboard` | Dashboard stats |

---

## Default Credentials (dev only)

| Role | Email | Password |
|---|---|---|
| Admin | admin@campus.edu | admin123 |
| Faculty | faculty@campus.edu | faculty123 |
| Student | student@campus.edu | student123 |

> ⚠️ Change all credentials before going to production.

---

## Environment Variables

See [`.env.example`](./.env.example) for the full list.

Key variables:

```env
MONGO_URI=mongodb+srv://...
OLLAMA_MODEL=qwen3:8b
JWT_SECRET_KEY=your-secret
CHROMA_PERSIST_DIR=./chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

---

## Testing

```bash
# Backend
cd backend
pytest tests/ --cov=. --cov-report=html -v

# Frontend
cd frontend
npm run test:coverage

# E2E (Phase 14)
npx playwright test
```

---

## License

MIT © 2024 AI Campus Intelligence Platform

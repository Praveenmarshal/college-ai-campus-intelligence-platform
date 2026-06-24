# Deployment Guide

## Option A — Docker Compose (recommended)

### Prerequisites
- Docker Engine 24+ and Docker Compose v2
- 16GB+ RAM recommended (Qwen 3 8B + EasyOCR + ChromaDB all run locally)
- (Optional) NVIDIA GPU + nvidia-container-toolkit for faster Ollama inference

### Steps

```bash
git clone <repo-url>
cd college-ai-campus-intelligence-platform
cp .env.example .env
# Edit .env: set MONGO_URI (or leave pointing at the bundled mongo service),
# JWT_SECRET_KEY, SECRET_KEY, MAIL_*, TWILIO_* as needed.

docker compose up --build -d

# First boot only — wait ~2-5 min for ollama-init to pull qwen3:8b
docker compose logs -f ollama-init

# Seed demo accounts (dev/staging only)
curl -X POST http://localhost:5000/api/auth/seed
```

Visit `http://localhost` (frontend, proxied through Nginx) or
`http://localhost:5000/api/health` to verify all services are up.

### Updating

```bash
git pull
docker compose up --build -d
```

### Scaling the backend

```bash
docker compose up -d --scale backend=3
# Put a load balancer (or the bundled nginx upstream) in front
```

---

## Option B — Bare Metal / VM

### Backend

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install system deps for OCR
sudo apt-get install -y tesseract-ocr poppler-utils

# Install & start Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull qwen3:8b
ollama serve &

export FLASK_ENV=production
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 "app:create_app()"
```

### Frontend

```bash
cd frontend
npm ci
npm run build
# Serve dist/ with any static file server, e.g.:
npx serve -s dist -l 80
# Or copy dist/ into an Nginx docroot using docker/nginx-spa.conf as reference
```

### MongoDB

Use **MongoDB Atlas** (recommended — managed, automatic backups) and set
`MONGO_URI` accordingly. For self-hosted MongoDB, follow the official
[installation guide](https://www.mongodb.com/docs/manual/installation/) and run
`mongod --auth`.

---

## Environment Variables Checklist (Production)

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | ✅ | Random 32+ char string |
| `JWT_SECRET_KEY` | ✅ | Different from `SECRET_KEY` |
| `MONGO_URI` | ✅ | Atlas connection string with credentials |
| `OLLAMA_BASE_URL` | ✅ | `http://ollama:11434` in Docker, `http://localhost:11434` bare metal |
| `OLLAMA_MODEL` | ✅ | `qwen3:8b` or `qwen3:14b` (needs more RAM) |
| `FRONTEND_URL` | ✅ | For CORS — your production domain |
| `MAIL_*` | optional | Only needed for email notifications |
| `TWILIO_*` | optional | Only needed for SMS notifications |

`ProductionConfig.validate()` in `config/settings.py` will raise on startup if
`SECRET_KEY`, `JWT_SECRET_KEY`, or `MONGO_URI` are missing.

---

## Health Checks for Load Balancers / Orchestrators

- Backend liveness: `GET /api/health/ping` → `{"status": "ok"}`
- Backend readiness (checks Mongo/Chroma/Ollama): `GET /api/health`
- Frontend: `GET /index.html` (200 OK)

## Reverse Proxy / TLS

Use `docker/nginx.conf` as a starting point. Mount your TLS certs and uncomment
the HTTPS server block. For automated certs, put
[Certbot](https://certbot.eff.org/) or a managed load balancer (ALB, Cloudflare)
in front.

## Backups

- **MongoDB**: Atlas continuous backups, or `mongodump` on a cron if self-hosted.
- **ChromaDB**: back up the `chroma_db/` volume — it's a SQLite + Parquet-based
  persistent store; can be restored by copying the directory back.
- **Uploaded files**: back up the `uploads/` volume.

## Scaling Notes

- Ollama inference is the bottleneck under load — consider a dedicated GPU host
  for Ollama if concurrent chat usage is high, and point multiple backend
  replicas at the same `OLLAMA_BASE_URL`.
- ChromaDB is embedded/file-based by default in this setup; for high write
  concurrency consider running ChromaDB in client/server mode instead.

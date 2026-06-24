# Free-Tier Demo Deployment Guide
## Vercel (frontend) + Render (backend) + MongoDB Atlas + Groq

This deploys a fully working demo at **$0/month**, with no credit card required
anywhere in the chain. It's intended for demos, portfolios, and college
project submissions — not for production use with real student data (see
[Limitations](#limitations-of-this-setup) at the bottom).

**What's different from the local/Docker setup:**
- **Groq** (free hosted LLM API) replaces **Ollama** — Render's free tier has
  no GPU and not enough RAM to run a local model. Everything else (RAG
  pipeline, agents, NL query engines) works identically against Groq.
- **EasyOCR** is dropped in favor of **Tesseract** — same reason, smaller
  footprint. OCR still works, just with a lighter engine.
- **XGBoost** is dropped — placement prediction automatically falls back to
  scikit-learn's RandomForestClassifier, same training/inference code path.

None of this requires touching application code — it's all environment
variable configuration (`LLM_PROVIDER=groq`, a lean `requirements-render.txt`).

---

## Prerequisites

- A GitHub account with this repo pushed (see main README for git setup)
- A free [Vercel](https://vercel.com) account (sign in with GitHub)
- A free [Render](https://render.com) account (sign in with GitHub)
- A free [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) account
- A free [Groq](https://console.groq.com) account

---

## Step 1 — MongoDB Atlas (free M0 cluster)

1. Sign up at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas/register).
2. Create a new project, then **Build a Database** → choose the **M0 Free**
   tier → pick any region.
3. **Database Access** → Add New Database User → username/password
   authentication. Save these credentials somewhere safe (a password manager,
   not a chat window or a commit).
4. **Network Access** → Add IP Address → **Allow Access from Anywhere**
   (`0.0.0.0/0`). This is required because Render's free tier uses dynamic
   IPs. *(This is one of the production limitations — see below.)*
5. **Database** → Connect → Drivers → copy the connection string. It looks
   like:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
6. Replace `<username>`/`<password>` with your real values, and add the
   database name before the `?`:
   ```
   mongodb+srv://myuser:mypassword@cluster0.xxxxx.mongodb.net/campus_ai?retryWrites=true&w=majority
   ```
   Keep this string — it's your `MONGO_URI`.

---

## Step 2 — Groq (free LLM API)

1. Sign up at [console.groq.com](https://console.groq.com) (GitHub/Google
   sign-in works, no card needed).
2. **API Keys** → **Create API Key** → copy it immediately (shown only once).
   Keep this — it's your `GROQ_API_KEY`.
3. That's it. Groq's free tier gives generous rate limits on
   `llama-3.3-70b-versatile`, which is what `GROQ_MODEL` defaults to in this
   project — strong enough for RAG, NL-query, and resume analysis.

---

## Step 3 — Deploy the backend to Render

1. Push your code to GitHub first if you haven't (see main README).
2. On Render: **New +** → **Blueprint**.
3. Connect your GitHub repo. Render will detect `render.yaml` at the repo
   root and propose the `campus-ai-backend` service automatically.
4. Click **Apply**. Render will prompt you for every secret marked
   `sync: false` in `render.yaml`:

   | Key | Value |
   |---|---|
   | `SECRET_KEY` | generate with `python3 -c "import secrets; print(secrets.token_hex(32))"` |
   | `JWT_SECRET_KEY` | generate the same way (a *different* value) |
   | `MONGO_URI` | your Atlas connection string from Step 1 |
   | `GROQ_API_KEY` | your Groq key from Step 2 |
   | `FRONTEND_URL` | leave blank for now — you'll fill this in after Step 4 |
   | `MAIL_USERNAME` / `MAIL_PASSWORD` | optional, skip unless you want email notifications |
   | `TWILIO_*` | optional, skip unless you want SMS notifications |

5. Render builds and deploys. First build takes ~5-10 minutes (installing
   `torch` CPU wheels is the slow part). Watch the build logs.
6. Once live, note your backend URL — something like
   `https://campus-ai-backend.onrender.com`.
7. Verify it's working:
   ```bash
   curl https://campus-ai-backend.onrender.com/api/health/ping
   # Expect: {"status":"ok","message":"pong"}

   curl https://campus-ai-backend.onrender.com/api/health
   # Check services.llm.status is "healthy" and provider is "groq"
   ```

> ⚠️ **Free tier cold starts**: after 15 minutes of no traffic, Render spins
> the instance down. The next request wakes it up, which takes 30-60
> seconds. This is expected — not a bug. If you're demoing live, hit the
> `/api/health/ping` endpoint a minute beforehand to warm it up.

---

## Step 4 — Deploy the frontend to Vercel

1. On Vercel: **Add New** → **Project** → import the same GitHub repo.
2. Vercel will ask for the project root — set it to `frontend` (this repo is
   a monorepo with `frontend/` and `backend/` as siblings).
3. Framework preset should auto-detect as **Vite**. If not, set manually
   (build command `npm run build`, output directory `dist` — already
   declared in `frontend/vercel.json`).
4. **Environment Variables** → add:

   | Key | Value |
   |---|---|
   | `VITE_API_BASE_URL` | your Render backend URL from Step 3, e.g. `https://campus-ai-backend.onrender.com` |

5. Click **Deploy**. Takes 1-2 minutes.
6. Note your Vercel URL — something like `https://campus-ai-platform.vercel.app`.

---

## Step 5 — Connect the two (CORS)

Go back to Render → your service → **Environment** → set the `FRONTEND_URL`
variable you skipped in Step 3 to your actual Vercel URL:

```
FRONTEND_URL=https://campus-ai-platform.vercel.app
```

Save — Render will redeploy automatically. This is required because the
backend's CORS config (`backend/app.py` → `CORS_ORIGINS`) only allows
requests from `FRONTEND_URL`; without this, the browser will block every API
call with a CORS error.

---

## Step 6 — Seed demo data and verify

The seed endpoint is locked down in production by default. To use it safely
on your Render deployment:

1. On Render → your service → **Environment** → add `SEED_SECRET` set to any
   random string (e.g. generate one with
   `python3 -c "import secrets; print(secrets.token_hex(16))"`).
2. Call the endpoint once with that secret in a header:
   ```bash
   curl -X POST https://campus-ai-backend.onrender.com/api/auth/seed \
     -H "X-Seed-Secret: your-random-string-here"
   ```
3. (Optional) Remove the `SEED_SECRET` env var afterward to close the door
   again — the endpoint will fall back to refusing all production requests.

Or skip seeding entirely and just **register an account through the UI's
"Create one" link** — that always works regardless of environment.

Visit your Vercel URL, register/login, and try:
- **AI Chat** → ask a question (exercises Groq)
- **Admin → Upload PDF** (if you registered as admin) → exercises the RAG
  pipeline end-to-end through Groq + ChromaDB

---

## Limitations of this setup

This is intentionally a **demo configuration**, not production-grade. Before
using it for anything with real student data:

| Limitation | Why | Fix |
|---|---|---|
| Render free tier has **no persistent disk** | Uploaded PDFs and the ChromaDB vector index live on ephemeral storage — wiped on every redeploy or restart | Upgrade to a paid Render plan with a disk, or move uploads/ChromaDB to S3-compatible storage |
| Cold starts (~30-60s) | Free tier sleeps after 15 min idle | Upgrade to a paid plan, or accept it for a demo |
| MongoDB Atlas open to `0.0.0.0/0` | Render's free tier has no static IP to allowlist | Use a paid Render plan with a static outbound IP, then restrict Atlas network access to just that IP |
| Groq is a third-party API | Defeats the "fully local, data never leaves campus" privacy goal of the original design | Switch `LLM_PROVIDER=ollama` and self-host once you have real infrastructure — see main [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) |
| No OCR via EasyOCR | Lean requirements drop it for build-size reasons | Tesseract fallback still works for OCR; for full EasyOCR accuracy, deploy backend with `requirements.txt` on a host with more resources |

For a real institutional deployment, follow
[`docs/DEPLOYMENT_GUIDE.md`](./DEPLOYMENT_GUIDE.md) instead — Docker Compose
with self-hosted Ollama, a persistent-disk host, and a properly restricted
MongoDB network policy.

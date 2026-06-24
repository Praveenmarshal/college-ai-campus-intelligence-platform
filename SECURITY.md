# Security Policy — Secrets & Credentials

This document explains how secrets are handled in this repository and what to
do before pushing to a public GitHub repo.

## ⚠️ Before your first `git push`

1. **Confirm `.env` is never tracked.**
   ```bash
   git ls-files | grep '\.env$'
   ```
   This should print **nothing**. If it prints `.env`, stop — see
   ["I already committed a secret"](#i-already-committed-a-secret) below.

2. **Enable the local pre-commit hook** (blocks `.env` and obvious secret
   patterns from ever being staged):
   ```bash
   git config core.hooksPath .githooks
   ```

3. **Never paste real values into `.env.example`.** That file is committed —
   it must only ever contain placeholders like `your-secret-key-here`.

## How secrets are supposed to flow

```
.env.example   (committed — placeholders only)
      │  cp
      ▼
.env           (NEVER committed — .gitignore'd — your real secrets live here)
      │  python-dotenv loads it at runtime
      ▼
os.environ     (read by backend/config/settings.py via os.getenv())
```

Real secrets only ever exist in:
- your local `.env` file (gitignored)
- your deployment platform's environment variable / secrets manager
  (e.g. Docker Compose `env_file: .env`, GitHub Actions Secrets, Render/Railway/
  AWS Secrets Manager, etc.)

They are **never** hardcoded in source files. `backend/config/settings.py`
only contains harmless dev-mode fallback strings (e.g.
`dev-secret-key-change-in-prod`) that are explicitly rejected by
`ProductionConfig.validate()` if you try to deploy with them still set —
see [backend/config/settings.py](./backend/config/settings.py).

## What's protected and how

| Layer | Mechanism |
|---|---|
| Working directory | `.gitignore` excludes `.env`, `.env.*.local`, and all upload/log/model directories |
| Local commits | `.githooks/pre-commit` blocks staging a real `.env` file or strings matching secret patterns (Mongo URIs with credentials, AWS keys, Twilio tokens, private key blocks) |
| CI / GitHub | `.github/workflows/ci.yml` runs Gitleaks (`secret-scan` job) on every push and PR, **before** any other job runs, using rules in `.gitleaks.toml` |
| Production runtime | `ProductionConfig.validate()` refuses to start the app if `SECRET_KEY`/`JWT_SECRET_KEY` are missing **or** still equal to a known placeholder value, or if `MONGO_URI` still contains `<username>`/`<password>` |

## Generating real secrets

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Run this twice — once for `SECRET_KEY`, once for `JWT_SECRET_KEY` — and paste
the results into your local `.env`.

## If you're forking/cloning this repo

Your `.env` is yours alone. The committed `.env.example` is the only file
that should ever appear in version control. If you add new environment
variables, add the **key with a placeholder value** to `.env.example`, never
the key with your real value.

## I already committed a secret

If a real secret was ever pushed to GitHub (even if you deleted it in a later
commit — it's still in git history and possibly already scraped by bots):

1. **Rotate the credential immediately** — treat it as compromised. For
   example, in MongoDB Atlas: Database Access → edit user → reset password.
   For Twilio: regenerate the Auth Token. This step matters more than
   anything below; removing it from git history does not "unleak" it.
2. Remove it from git history with
   [git filter-repo](https://github.com/newren/git-filter-repo) or the
   [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) — `git rm`
   alone is not enough, history still has it.
3. Force-push the cleaned history and ask any collaborators to re-clone.
4. Consider the repository's prior commit SHAs compromised — if it was
   public even briefly, assume the old secret was seen.

## Reporting a vulnerability

If you find a security issue in this codebase itself (not a leaked credential
in someone's fork), open a private security advisory on the repository
rather than a public issue.

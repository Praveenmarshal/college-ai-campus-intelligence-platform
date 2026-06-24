#!/usr/bin/env bash
# scripts/setup-env.sh
#
# One-time setup helper: creates .env from .env.example and auto-generates
# strong random values for every secret field, instead of leaving placeholder
# strings that someone might accidentally ship to production.
#
# Usage:
#   bash scripts/setup-env.sh
#
# Safe to re-run — it will refuse to overwrite an existing .env.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
EXAMPLE_FILE="$ROOT_DIR/.env.example"

if [[ -f "$ENV_FILE" ]]; then
  echo "⚠️  $ENV_FILE already exists — refusing to overwrite it."
  echo "   Delete it first if you really want to regenerate, or edit it by hand."
  exit 1
fi

if [[ ! -f "$EXAMPLE_FILE" ]]; then
  echo "❌ $EXAMPLE_FILE not found. Run this script from the repo root."
  exit 1
fi

cp "$EXAMPLE_FILE" "$ENV_FILE"

gen_secret() {
  python3 -c "import secrets; print(secrets.token_hex(32))"
}

gen_urlsafe() {
  python3 -c "import secrets; print(secrets.token_urlsafe(24))"
}

# Replace placeholder values with real generated secrets, in place.
# Uses a temp file for portability across GNU/BSD sed.
replace_value() {
  local key="$1"
  local value="$2"
  local tmp
  tmp=$(mktemp)
  awk -v key="$key" -v value="$value" '
    BEGIN { FS="="; OFS="=" }
    $1 == key { print key, value; next }
    { print }
  ' "$ENV_FILE" > "$tmp"
  mv "$tmp" "$ENV_FILE"
}

echo "🔐 Generating secure random secrets…"
replace_value "SECRET_KEY" "$(gen_secret)"
replace_value "JWT_SECRET_KEY" "$(gen_secret)"
replace_value "MONGO_ROOT_PASSWORD" "$(gen_urlsafe)"
replace_value "MONGO_APP_PASSWORD" "$(gen_urlsafe)"

echo ""
echo "✅ Created $ENV_FILE with auto-generated secrets."
echo ""
echo "Still needed before you can fully run the app:"
echo "  - MONGO_URI            → your real MongoDB Atlas connection string (or leave as-is to use the bundled local mongo container)"
echo "  - MAIL_USERNAME / MAIL_PASSWORD   → only needed for email notifications"
echo "  - TWILIO_*              → only needed for SMS notifications"
echo ""
echo "Reminder: $ENV_FILE is gitignored and will NEVER be committed. Never paste its contents into a commit, issue, or chat."

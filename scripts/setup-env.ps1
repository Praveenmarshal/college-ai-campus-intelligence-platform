# scripts/setup-env.ps1
#
# Windows PowerShell version of setup-env.sh.
# Creates .env from .env.example and auto-generates strong random values
# for every secret field, so you never accidentally ship placeholder
# strings like "your-super-secret-key-change-in-production" to production.
#
# Usage (from the project root, in PowerShell):
#   .\scripts\setup-env.ps1
#
# Safe to re-run — it will refuse to overwrite an existing .env.

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RootDir ".env"
$ExampleFile = Join-Path $RootDir ".env.example"

if (Test-Path $EnvFile) {
    Write-Host "WARNING: $EnvFile already exists - refusing to overwrite it." -ForegroundColor Yellow
    Write-Host "Delete it first if you really want to regenerate, or edit it by hand." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $ExampleFile)) {
    Write-Host "ERROR: $ExampleFile not found. Run this script from the repo root (or via .\scripts\setup-env.ps1)." -ForegroundColor Red
    exit 1
}

Copy-Item $ExampleFile $EnvFile

function New-Secret {
    # 32 random bytes -> 64-char hex string (matches Python's secrets.token_hex(32))
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    return ($bytes | ForEach-Object { $_.ToString("x2") }) -join ""
}

function New-UrlSafeSecret {
    # ~24 random bytes, base64url-encoded (matches Python's secrets.token_urlsafe(24))
    $bytes = New-Object byte[] 24
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $b64 = [Convert]::ToBase64String($bytes)
    return $b64.TrimEnd("=").Replace("+", "-").Replace("/", "_")
}

function Set-EnvValue {
    param(
        [string]$Key,
        [string]$Value
    )
    $content = Get-Content $EnvFile
    $found = $false
    $updated = $content | ForEach-Object {
        if ($_ -match "^$Key=") {
            $found = $true
            "$Key=$Value"
        } else {
            $_
        }
    }
    if (-not $found) {
        $updated += "$Key=$Value"
    }
    Set-Content -Path $EnvFile -Value $updated
}

Write-Host "Generating secure random secrets..." -ForegroundColor Cyan

Set-EnvValue -Key "SECRET_KEY" -Value (New-Secret)
Set-EnvValue -Key "JWT_SECRET_KEY" -Value (New-Secret)
Set-EnvValue -Key "MONGO_ROOT_PASSWORD" -Value (New-UrlSafeSecret)
Set-EnvValue -Key "MONGO_APP_PASSWORD" -Value (New-UrlSafeSecret)

Write-Host ""
Write-Host "Created $EnvFile with auto-generated secrets." -ForegroundColor Green
Write-Host ""
Write-Host "Still needed before you can fully run the app:" -ForegroundColor Yellow
Write-Host "  - MONGO_URI              -> your real MongoDB Atlas connection string"
Write-Host "  - GROQ_API_KEY            -> your real Groq API key (or set LLM_PROVIDER=ollama for local)"
Write-Host "  - MAIL_USERNAME / MAIL_PASSWORD  -> only needed for email notifications"
Write-Host "  - TWILIO_*                -> only needed for SMS notifications"
Write-Host ""
Write-Host "Edit them now with:  notepad .env" -ForegroundColor Cyan
Write-Host ""
Write-Host "Reminder: $EnvFile is gitignored and will NEVER be committed." -ForegroundColor Yellow
Write-Host "Never paste its contents into a commit, issue, or chat." -ForegroundColor Yellow

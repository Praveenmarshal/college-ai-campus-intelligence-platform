"""
config/settings.py
Application configuration using environment variables.
Supports development, testing, and production modes.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """Base configuration shared across all environments."""

    # App
    APP_NAME = os.getenv("APP_NAME", "AI Campus Intelligence Platform")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
    DEBUG = False
    TESTING = False

    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/campus_ai")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "campus_ai")

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret-change-in-prod")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 2592000))
    )
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # LLM Provider — "gemini", "ollama" (local) or "groq" (free hosted)
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

    # Gemini Config
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # Ollama / LLM
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", 120))

    # Groq (used when LLM_PROVIDER=groq)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_TIMEOUT = int(os.getenv("GROQ_TIMEOUT", 60))

    # ChromaDB
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "campus_docs")

    # Embedding Model
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # File Uploads
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 52428800))  # 50 MB
    ALLOWED_EXTENSIONS = set(
        os.getenv("ALLOWED_EXTENSIONS", "pdf,xlsx,xls,csv,png,jpg,jpeg,tiff").split(",")
    )

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

    # CORS
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    CORS_ORIGINS = [FRONTEND_URL, "http://localhost:3000"]

    # Email
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@campus.edu")

    # Twilio
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

    # Rate Limiting
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "100 per hour")
    RATELIMIT_STORAGE_URL = os.getenv("RATELIMIT_STORAGE_URL", "memory://")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "./logs/app.log")

    # Upload subdirectories
    UPLOAD_DIRS = {
        "pdf": "pdfs",
        "excel": "excels",
        "csv": "csvs",
        "image": "images",
        "resume": "resumes",
    }


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = "DEBUG"


class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    MONGO_DB_NAME = "campus_ai_test"
    CHROMA_PERSIST_DIR = "./chroma_db_test"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=30)


class ProductionConfig(BaseConfig):
    """Production configuration — all secrets must come from environment."""
    DEBUG = False
    LOG_LEVEL = "WARNING"

    # Known placeholder/dev-default values that must NEVER reach production
    _UNSAFE_DEFAULTS = {
        "SECRET_KEY": {"dev-secret-key-change-in-prod", "your-super-secret-key-change-in-production"},
        "JWT_SECRET_KEY": {"jwt-dev-secret-change-in-prod", "your-jwt-secret-key-change-in-production"},
    }

    @classmethod
    def validate(cls):
        """
        Ensure required secrets are set in production AND are not left as
        placeholder/example values from .env.example. Called automatically
        from create_app() when FLASK_ENV=production.
        """
        required = ["SECRET_KEY", "JWT_SECRET_KEY", "MONGO_URI"]
        missing = [k for k in required if not os.getenv(k)]
        if missing:
            raise ValueError(
                f"Missing required environment variables for production: {missing}. "
                f"Copy .env.example to .env and set real values — never commit .env to git."
            )

        unsafe = [
            key for key, bad_values in cls._UNSAFE_DEFAULTS.items()
            if os.getenv(key) in bad_values
        ]
        if unsafe:
            raise ValueError(
                f"The following variables are still set to placeholder values from "
                f".env.example: {unsafe}. Generate real secrets before deploying, e.g.: "
                f"python -c \"import secrets; print(secrets.token_hex(32))\""
            )

        mongo_uri = os.getenv("MONGO_URI", "")
        if "<username>" in mongo_uri or "<password>" in mongo_uri:
            raise ValueError(
                "MONGO_URI still contains placeholder <username>/<password> — "
                "set your real connection string in .env."
            )


# Config registry
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config():
    """Return the active config class based on FLASK_ENV."""
    env = os.getenv("FLASK_ENV", "development")
    return config_by_name.get(env, DevelopmentConfig)

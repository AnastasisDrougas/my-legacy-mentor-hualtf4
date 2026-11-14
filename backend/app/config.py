import os


class Settings:
    # Backend configuration
    APP_ENV = os.getenv("APP_ENV", "development")
    BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

    # SQLite configuration
    DATABASE_PATH = os.getenv(
        "DATABASE_PATH",
        "data/knowledge_legacy.db"
    )

    # Frontend configuration
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8501"
    ).split(",")

    # AI configuration
    AI_PROVIDER = os.getenv("AI_PROVIDER", "mock")
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "")
    AI_BASE_URL = os.getenv("AI_BASE_URL", "")


settings = Settings()
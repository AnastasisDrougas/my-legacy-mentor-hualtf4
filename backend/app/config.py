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
    # LLM configuration
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")


settings = Settings()
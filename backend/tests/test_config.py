from app.config import settings


def test_backend_port():
    # Verify backend port configuration
    assert isinstance(settings.BACKEND_PORT, int)
    assert 1 <= settings.BACKEND_PORT <= 65535


def test_database_path():
    # Verify SQLite path is configured
    assert settings.DATABASE_PATH


def test_cors_origins():
    # Verify CORS configuration
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) > 0
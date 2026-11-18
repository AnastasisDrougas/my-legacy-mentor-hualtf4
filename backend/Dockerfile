
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/app/data/knowledge_legacy.db \
    UPLOAD_DIR=/app/data/uploads \
    HF_HOME=/app/model_cache

WORKDIR /app

# Install Backend and AI dependencies
COPY backend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Copy Backend application
COPY backend/app ./app

# Copy AI module
COPY ai ./ai

# Prepare persistent storage and model cache
RUN mkdir -p \
    /app/data/uploads \
    /app/ai/storage/chroma \
    /app/model_cache \
    && useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app

# Run as non-root user
USER appuser

EXPOSE 8000

# Backend health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

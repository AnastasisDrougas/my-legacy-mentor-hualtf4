
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Frontend dependencies
COPY frontend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Copy Streamlit application
COPY frontend/ ./

# Create non-root user
RUN useradd --create-home --uid 10002 appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8501

# Start Streamlit
CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true"]

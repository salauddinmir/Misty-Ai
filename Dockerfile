# MISTY backend — production image for Render (FastAPI + uvicorn).
# PostgreSQL is selected automatically when MISTY_DB_URL starts with
# postgresql:// (set it to the Supabase connection string on Render).

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# System deps for optional speech pipeline (espeak/whisper) — installed but not
# strictly required; the app degrades gracefully if absent.
RUN apt-get update \
    && apt-get install -y --no-install-recommends espeak ffmpeg gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# data/ is where SQLite lives when MISTY_DB_URL is not postgresql.
# Render's filesystem is ephemeral between deploys — prefer PostgreSQL.
RUN mkdir -p data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import json,urllib.request; \
                   response=urllib.request.urlopen('http://localhost:8000/health', timeout=4); \
                   payload=json.load(response); \
                   assert payload.get('ready') is True"

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Single-container image: FastAPI serving API (+ static React UI when built in Phase 09).
# AgentBase runtime contract: listen on 8080, expose GET /health.
FROM python:3.11-slim

WORKDIR /app

# Install deps first (better layer caching).
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# App code + data (termbase.json). Secrets are NOT copied (see .dockerignore);
# LLM_* are injected via the AgentBase credential module at runtime.
COPY backend/ backend/

ENV PYTHONPATH=/app/backend
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --app-dir backend"]

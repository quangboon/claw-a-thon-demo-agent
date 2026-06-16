# Multi-stage: build the React UI, then run FastAPI serving API + static UI in one container.
# AgentBase runtime contract: listen on 8080, expose GET /health.

# --- Stage 1: build the React UI → /backend/static ---
FROM node:20-slim AS web
WORKDIR /web
COPY web/package.json ./
RUN npm install
COPY web/ ./
# vite outDir is ../backend/static (relative to /web) → writes to /backend/static
RUN npm run build

# --- Stage 2: Python API + bundled UI ---
FROM python:3.11-slim
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# App code + data (termbase.json). Secrets excluded via .dockerignore; LLM_* injected at runtime.
COPY backend/ backend/
# Multi-tenant seed profiles (Domain Packs) — resolved relative to CWD /app (settings.profiles_dir="profiles").
COPY profiles/ profiles/
# Built UI from stage 1 (local backend/static is .dockerignored).
COPY --from=web /backend/static backend/static

ENV PYTHONPATH=/app/backend
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --app-dir backend"]

# syntax=docker/dockerfile:1.7

# --- Build frontend ---
FROM node:20-alpine AS frontend
WORKDIR /opt/app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Build backend image ---
FROM python:3.11-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FRONTEND_DIST=/app/static
WORKDIR /opt/app
COPY pyproject.toml uv.lock ./
RUN pip install --upgrade pip && pip install .
COPY . ./
COPY --from=frontend /opt/app/frontend/dist /app/static
EXPOSE 8080
CMD uvicorn app.web_server:app --host 0.0.0.0 --port ${PORT:-8080}

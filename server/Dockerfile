FROM node:24-slim AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim AS builder

WORKDIR /build

RUN python -m venv /opt/venv

COPY server/requirements.txt ./
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt \
    && /opt/venv/bin/pip check


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app server/src/ ./
COPY --chown=app:app server/gunicorn.conf.py ./
COPY --from=frontend-builder /frontend/dist ./frontend

USER app

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; host = os.getenv('APP_HOST', '0.0.0.0'); host = '127.0.0.1' if host == '0.0.0.0' else host; response = urllib.request.build_opener(urllib.request.ProxyHandler({})).open('http://' + host + ':5000/health', timeout=3); raise SystemExit(0 if response.status == 200 else 1)"]

CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app app

COPY --chown=app:app src/ ./
COPY --chown=app:app gunicorn.conf.py ./

USER app

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; host = os.getenv('APP_HOST', '0.0.0.0'); host = '127.0.0.1' if host == '0.0.0.0' else host; response = urllib.request.build_opener(urllib.request.ProxyHandler({})).open('http://' + host + ':5000/health', timeout=3); raise SystemExit(0 if response.status == 200 else 1)"]

CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]

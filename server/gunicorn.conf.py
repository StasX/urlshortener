import os

# Network
bind = f"{os.getenv('APP_HOST', '0.0.0.0')}:5000"  # nosec B104

# Workers (Gunicorn uses gthread when threads > 1).
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
worker_class = "gthread"
threads = 2

# Connection handling
timeout = 30
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
capture_output = True

# Process
preload_app = False

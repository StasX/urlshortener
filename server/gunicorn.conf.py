import os

# Network
bind = f"{os.getenv('APP_HOST', '0.0.0.0')}:5000"  # nosec B104

# Socket.IO rooms are in-process; multiple workers require a message broker
# and sticky routing across separately deployed single-worker instances.
workers = 1
worker_class = "gthread"
threads = 100

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

FROM mongo:8.0

EXPOSE 27017

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["mongosh", "--quiet", "--host", "127.0.0.1", "--port", "27017", "--eval", "quit(db.adminCommand({ ping: 1 }).ok === 1 ? 0 : 1)"]

# Use the official entrypoint and mongod command; persist data at /data/db.

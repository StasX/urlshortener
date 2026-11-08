FROM mongo:8.0

ENV HOME=/data/db

RUN mkdir -p /data/db /data/configdb \
    && chown -R mongodb:mongodb /data/db /data/configdb

USER mongodb

EXPOSE 27017

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["mongosh", "--quiet", "--host", "127.0.0.1", "--port", "27017", "--eval", "quit(db.adminCommand({ ping: 1 }).ok === 1 ? 0 : 1)"]

# URL Shortener

Guests can create unmanaged links that expire after 24 hours. Expired links
stop redirecting immediately; MongoDB's TTL index removes them in the background.
Links created while signed in stay in the user's dashboard and do not expire.

Run the Flask application and MongoDB with Docker Compose:

1. Copy `.env.example` to `.env` and set `SECRET_KEY` to a random value. Generate
   one with `python -c "import secrets; print(secrets.token_hex(32))"`.
2. Run `docker compose up --build -d` from the repository root.
3. Open `http://localhost:5000`. Check status with `docker compose ps` and logs
   with `docker compose logs -f`.

The server waits for MongoDB to become healthy. Both images include health
checks. MongoDB is reachable as `db:27017` inside the Compose network and is not
published to the host. Database data persists in the `mongodb_data` named volume.

Run `docker compose down` to stop the services while retaining database data.
If you change `APP_PORT`, update `PUBLIC_BASE_URL` to match the public address.
Set `PASSWORDS_SALT` to the original value when using legacy accounts.
Compose loads the server's environment from `.env`, including the database
name and port, bind address, worker count, and public URL. Compose sets
`DB_HOST` directly to the `db` service name. `APP_PORT` controls the
host port; the container listens on port 5000. Database credentials are currently
unused by the application.

For an existing database, see [the short-link migration instructions](LINK_MIGRATION.md).

## Continuous integration

The GitHub Actions workflow runs on pushes, pull requests, and manual dispatch.
It runs the Python unittest suite and JavaScript checks, builds both Docker
images, waits for healthy services, verifies non-root users, and tests guest
expiry, registration/login, ownership, and rate limits against real MongoDB.
Checkov, Trivy, and Bandit run as separate security checks. Logs are uploaded as
artifacts, and the CI containers and volumes are removed after the run.

To run the integration check locally with Compose already running:

```sh
docker compose exec -T server python - < server/tests/smoke_compose.py
```

In PowerShell, use:

```powershell
Get-Content server/tests/smoke_compose.py -Raw | docker compose exec -T server python -
```

The check creates a separate temporary database and removes it afterward.

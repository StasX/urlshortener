# Shorty - URL Shortener

A Flask and MongoDB application for creating short links, revealing redirect
destinations, and tracking visits. The interface uses Jinja templates,
Bootstrap, jQuery, and Chart.js with a responsive dark green theme.

## Features

- **Guest links:** create short links without an account. These links are
  unmanaged, expire after 24 hours, and do not appear in a dashboard.
- **Member links:** register or sign in before creating a link to keep it
  without an expiry date and manage it from your dashboard.
- **Link management:** view destinations and visit counts, see a visit chart,
  and delete your own links.
- **Destination lookup:** reveal the next redirect destination of a public
  HTTP or HTTPS URL without signing in.
- **Authentication:** registration with password confirmation, scrypt password
  hashing, login, and logout.
- **Error handling:** matching error pages and inline messages, including
  validation errors, missing links, server errors, and rate limits.

Expired guest links stop redirecting immediately. MongoDB removes their records
in the background through a TTL index, so physical deletion may happen later.
Guest links remain unmanaged if their creator subsequently registers or signs in.

## Quick start

Install Docker with Docker Compose, then run these commands from the repository
root. Python is only needed for the secret-generation command below; Node.js is
only needed if you run JavaScript tests outside CI.

1. Create the local environment file:

   ```sh
   cp .env.example .env
   ```

   In PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Generate a secret and paste it into `SECRET_KEY` in `.env`:

   ```sh
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

3. Build and start the services:

   ```sh
   docker compose up --build -d
   ```

4. Open [http://localhost:5000](http://localhost:5000).

Keep `.env` private; it is ignored by Git and is not baked into the images.
Compose passes the server settings at runtime.

## Configuration

Compose loads the server's environment from the root `.env` file. The example
file documents the initial values.

| Variable | Example value | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | A generated random secret | Signs Flask session cookies; keep it stable across restarts. |
| `DB_NAME` | `urlshortener` | MongoDB database name. |
| `DB_PORT` | `27017` | MongoDB's container port; keep this value for the supplied database service. |
| `APP_HOST` | `0.0.0.0` | Gunicorn bind address inside the server container. |
| `APP_PORT` | `5000` | Published host port for the application. |
| `PUBLIC_BASE_URL` | `http://localhost:5000` | Public HTTP or HTTPS origin used to generate short links. |
| `GUNICORN_WORKERS` | `2` | Number of Gunicorn worker processes. |
| `PASSWORDS_SALT` | Empty for new installations | Original salt required to verify legacy password hashes. |
| `DB_USER`, `DB_PASSWORD` | Empty | Reserved settings; the application currently does not use database authentication. |

`DB_HOST` is set directly to `db` in Compose's `environment` section. It does
not belong in `.env` for this setup. If you change `APP_PORT`, update
`PUBLIC_BASE_URL` to the matching public address. Generated links use this
configured origin rather than incoming request headers.

Gunicorn settings live in `server/gunicorn.conf.py`: two worker processes by
default, two threads per worker, a 30-second timeout, and logs sent to container
output. Flask-Limiter currently uses in-memory storage with a default limit of
four requests per minute per client IP, per endpoint, in each worker. Health
checks are exempt.

## Containers, networking, and storage

| Service | Build context | Runtime user | Health check |
| --- | --- | --- | --- |
| `server` | `server/` | `app` | HTTP request to `/health` on port 5000. |
| `db` | `db/` | `mongodb` | MongoDB ping using `mongosh`. |

The server waits for MongoDB to become healthy before starting. Both services
join the internal `backend` bridge network. Only the server also joins the
`frontend` network, which provides external connectivity for destination lookup.
MongoDB has no published host port; the server connects to `db:27017`.
Docker administrators can still access containers directly.

MongoDB stores data at `/data/db` in the `mongodb_data` named volume. The volume
survives service restarts, image rebuilds, and `docker compose down`.

```sh
# View service health and status
docker compose ps

# Follow application and database logs
docker compose logs -f

# Rebuild and apply code or configuration changes
docker compose up --build -d

# Stop and remove containers while keeping database data
docker compose down
```

For an existing database from before the unique short-code field was introduced,
follow [the short-link migration instructions](LINK_MIGRATION.md) before starting
the updated application.

## Tests

Run all commands from the repository root.

### Python tests

Use Python 3.12 and install the application dependencies before running the suite:

```sh
python -m pip install -r server/requirements.txt
python -m unittest discover -s server/tests -v
```

These tests cover password hashing, URL validation and resolution, short-link
creation, migration behavior, authentication guards, and deletion permissions.
Database-facing unit tests use mocks. Tests requiring missing application
packages are skipped, so install the dependencies for full coverage.

### JavaScript tests

Use Node.js 24, matching CI:

```sh
node --check server/src/static/js/main.js
node --test server/tests/test_delete_url.js
```

`test_delete_url.js` uses Node's built-in test runner and modules; no npm install
is needed. It checks the browser-side deletion function: the DELETE request,
button state, successful reload, and failure message. It simulates AJAX calls
without launching a browser.

### Server and MongoDB integration

Start Compose first, then run:

```sh
docker compose exec -T server python - < server/tests/smoke_compose.py
```

In PowerShell:

```powershell
Get-Content server/tests/smoke_compose.py -Raw | docker compose exec -T server python -
```

This check uses Flask's test client and real MongoDB. It verifies page rendering,
registration, password confirmation, login/logout, guest expiry, the TTL index,
visit counting, permanent member links, dashboard isolation, deletion permissions,
and the styled rate-limit response. It creates a separate temporary database and
removes it afterward, leaving the application database unchanged.

This is an integration check. It does not launch a browser, execute page
JavaScript, or send requests through Gunicorn. CI separately checks the running
server's `/health` endpoint over HTTP.

## Continuous integration

[The GitHub Actions workflow](.github/workflows/main.yml) runs on pushes, pull
requests, and manual dispatch:

- **Tests:** Python unittest suite, JavaScript syntax validation, and the Node.js
  deletion test.
- **Containers:** image builds, Compose health checks, non-root user checks,
  HTTP health verification, and the real MongoDB integration check.
- **Security:** Checkov scans Dockerfiles and GitHub Actions; Trivy scans the
  repository for vulnerabilities and secrets; Bandit scans Python application
  code and the Gunicorn configuration.

CI generates a disposable `.env` with a random session secret. It uploads test,
container, and security reports as artifacts with 14-day retention. The container
job removes its Compose services and volumes when it finishes.

## Project layout

```text
.github/workflows/main.yml    GitHub Actions pipeline
db/Dockerfile               MongoDB image and health check
server/
   Dockerfile                Python application image and health check
   gunicorn.conf.py          Gunicorn process configuration
   requirements.txt          Python dependencies
   src/
     app.py                  Flask setup, health route, and error handlers
     migrations/             Legacy short-code migration
     models/                 MongoEngine user and link documents
     views/                  Authentication, link, and dashboard routes
     utils/                  Security, validation, and configuration helpers
     templates/              Jinja pages and shared layouts
     static/                 CSS and browser JavaScript
   tests/                    Python, JavaScript, and integration checks
docker-compose.yml          Services, networks, and persistent volume
.env.example                Configuration template
LINK_MIGRATION.md           Existing-database migration instructions
```

`.editorconfig` and `.gitattributes` keep text files in UTF-8 with LF line endings.

# Shorty - URL Shortener

A Vue 3 and TypeScript SPA backed by a Flask JSON API and MongoDB. Create
short links, reveal redirect destinations, and track visits in the original
responsive dark green design, with Bootstrap and Chart.js bundled by Vite.

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
  hashing, JWT sign-in, and persistent token revocation on logout.
- **Error handling:** matching error pages and inline messages, including
  validation errors, missing links, server errors, and rate limits.

Expired guest links stop redirecting immediately. MongoDB removes their records
in the background through a TTL index, so physical deletion may happen later.
Guest links remain unmanaged if their creator subsequently registers or signs in.

## Quick start

Install Docker with Docker Compose, then run these commands from the repository
root. Python is only needed for the secret-generation command below; Node.js is
only needed for frontend development and tests outside Docker (use Node.js 24).

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
| `SECRET_KEY` | A generated random secret | Signs JWTs; use at least 32 random bytes and keep it stable across workers/restarts. |
| `DB_NAME` | `urlshortener` | MongoDB database name. |
| `DB_PORT` | `27017` | MongoDB's container port; keep this value for the supplied database service. |
| `APP_HOST` | `0.0.0.0` | Gunicorn bind address inside the server container. |
| `APP_PORT` | `5000` | Published host port for the application. |
| `PUBLIC_BASE_URL` | `http://localhost:5000` | Public HTTP or HTTPS origin used to generate short links. |
| `GUNICORN_WORKERS` | `2` | Number of Gunicorn worker processes. |
| `SPA_DEV_ORIGIN` | Empty | Optional trusted Vite origin, such as `http://localhost:5173`; leave blank in production. |
| `PASSWORDS_SALT` | Empty for new installations | Original salt required to verify legacy password hashes. |
| `DB_USER`, `DB_PASSWORD` | Empty | Reserved settings; the application currently does not use database authentication. |

`DB_HOST` is set directly to `db` in Compose's `environment` section. It does
not belong in `.env` for this setup. If you change `APP_PORT`, update
`PUBLIC_BASE_URL` to the matching public address. Generated links use this
configured origin rather than incoming request headers.

Gunicorn settings live in `server/gunicorn.conf.py`: two worker processes by
default, two threads per worker, a 30-second timeout, and logs sent to container
output. Flask-Limiter currently uses in-memory storage with a default limit of
60 requests per minute per client IP and endpoint, in each worker. Login,
registration, link creation, and destination lookup have a limit of four per
minute. The SPA shell, assets, and health endpoint are exempt.

## Containers, networking, and storage

| Service | Build context | Runtime user | Health check |
| --- | --- | --- | --- |
| `server` | Repository root (`server/Dockerfile`) | `app` | HTTP request to `/health` on port 5000. |
| `db` | `db/` | `mongodb` | MongoDB ping using `mongosh`. |

The server image has three stages: Node.js 24 builds the Vue TypeScript app, a
Python 3.12 builder installs/checks dependencies in `/opt/venv`, and the Python
runtime copies the virtual environment, API code, and frontend bundle. Node.js
is not included in the runtime. Build from the repository root with
`docker build -f server/Dockerfile -t urlshortener .`.

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

## JWT authentication and API

JWTs are stored in HttpOnly cookies scoped to `/api/`, with a one-hour expiry.
They are never exposed to Vue or stored in localStorage. Vue restores the
signed-in user through `/api/auth/me` after a page reload. Cookies use `SameSite=Lax`
and are marked `Secure` when `PUBLIC_BASE_URL` uses HTTPS.

Authenticated mutations send the readable `csrf_access_token` cookie value in
`X-CSRF-TOKEN`. The server checks it against the signed JWT and checks browser
origins on all API writes, including login and registration. Logout revokes the
JWT in MongoDB across workers/restarts; a TTL index removes expired revocation
records. Users sign in again when their token expires; refresh tokens are not
currently issued. Existing accounts and links are preserved, but old Flask
session cookies no longer authenticate requests, so users must sign in again.

| Method | Route | Purpose |
| --- | --- | --- |
| POST | `/api/auth/register` | Validate registration and set JWT/CSRF cookies. |
| POST | `/api/auth/login` | Verify credentials and set JWT/CSRF cookies. |
| GET | `/api/auth/me` | Return the signed-in user, or `null` for a guest. |
| POST | `/api/auth/logout` | Revoke the current JWT and clear cookies. |
| POST | `/api/links` | Create a guest or member short link. |
| GET | `/api/links` | List links owned by the JWT's user. |
| DELETE | `/api/links/<id>` | Delete a link owned by the JWT's user. |
| POST | `/api/resolve` | Reveal one redirect from a public URL. |
| GET | `/<code>` | Redirect and atomically increment the visit count. |
| GET | `/health` | Application health check. |

API requests and errors use JSON. Vue Router handles home, login, registration,
and dashboard navigation without reloading the page. Flask serves the built SPA
at these paths for direct navigation, while short-code redirects remain on Flask.
Minimal server-rendered error pages retain the same design for invalid/expired
short links and other non-API errors.

## Frontend development

Start Compose for Flask and MongoDB, set `SPA_DEV_ORIGIN=http://localhost:5173`
in `.env`, and recreate the server with `docker compose up -d server`.
Then run:

```sh
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` and `/health` to port 5000.
Short links use the configured `PUBLIC_BASE_URL` and redirect through Flask.
For a production build, leave `SPA_DEV_ORIGIN` blank and rebuild the image.

## Tests

### Python API tests

From the repository root, use Python 3.12 and install the dependencies:

```sh
python -m pip install -r server/requirements.txt
python -m unittest discover -s server/tests -v
```

Tests cover password hashing, URL validation/resolution, migration behavior,
short links, token validation, expiry/revocation, CSRF, origin checks, and owner
permissions. Database calls are mocked in unit tests. Install the requirements
to avoid dependency-related skips.

### Vue TypeScript and browser tests

From `frontend/`, use Node.js 24:

```sh
npm ci
npm run typecheck
npm run build
npm test
npx playwright install chromium
npm run test:browser
```

`build` includes strict Vue/TypeScript checking. The Node.js API-client tests
verify JSON requests, CSRF headers, cookies, and error handling. Playwright launches
Chromium and Vite to test guest links, registration, sign-in, dashboard deletion,
expired authentication, and mobile navigation using intercepted API responses.

To exercise the full browser-to-Gunicorn-to-MongoDB flow, point the same browser
command at a disposable Compose environment:

```sh
LIVE_E2E_BASE_URL=http://localhost:5000 npm run test:browser
```

In PowerShell:

```powershell
$env:LIVE_E2E_BASE_URL='http://localhost:5000'
npm run test:browser
Remove-Item Env:LIVE_E2E_BASE_URL
```

The full browser test creates a test account and a guest link, so use a disposable
database. CI runs it against its isolated containers and removes their volumes.

### Server and MongoDB integration

From the repository root, start Compose first, then run:

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
JWT cookies, CSRF, token revocation, and JSON rate-limit responses. It creates a separate temporary database and
removes it afterward, leaving the application database unchanged.

This is an integration check. It does not launch a browser, execute page
JavaScript, or send requests through Gunicorn. CI separately checks the running
server's `/health` endpoint over HTTP.

## Continuous integration

[The GitHub Actions workflow](.github/workflows/main.yml) runs on pushes, pull
requests, and manual dispatch:

- **API tests:** Python unittest suite.
- **Frontend:** npm dependency installation, strict TypeScript checks, production
  build, API-client tests, and Chromium browser flows.
- **Containers:** image builds, Compose health checks, non-root user checks,
  HTTP health verification, real MongoDB integration, and a full browser test
  against the running Vue/JWT application.
- **Security:** Checkov scans Dockerfiles and GitHub Actions; Trivy scans the
  repository for vulnerabilities and secrets; Bandit scans Python application
  code and the Gunicorn configuration.

CI generates a disposable `.env` with a random JWT signing secret. It uploads test,
container, and security reports as artifacts with 14-day retention. The container
job removes its Compose services and volumes when it finishes.

The container job uses `ubuntu-22.04` to avoid MongoDB 8.0's startup failure on
newer GitHub-hosted runner kernels. See the
[GitHub runner issue](https://github.com/actions/runner-images/issues/15005).
If MongoDB reports the same kernel incompatibility on another host, check that
host's kernel against the [MongoDB compatibility notice](https://www.mongodb.com/docs/v8.0/release-notes/8.0/).
Changing the Docker image's Linux distribution does not change the host kernel.

## Project layout

```text
.github/workflows/main.yml    API, frontend, container, and security CI
frontend/
  src/                       Vue TypeScript views, shared components, API client
  tests/                     API-client tests using Node.js
  e2e/                       Mocked browser and live full-stack tests
  vite.config.ts             Vue build and API development proxy
  tsconfig.json              Strict TypeScript configuration
  package-lock.json          Locked frontend dependencies
db/Dockerfile                MongoDB image and health check
server/
  Dockerfile                 Vue build, Python builder, and non-root runtime
  gunicorn.conf.py           Gunicorn process configuration
  requirements.txt           Python dependencies
  src/
    app.py                   SPA hosting, JWT/API setup, health, error handlers
    migrations/              Legacy short-code migration
    models/                  Users, links, and revoked tokens
    views/                   JSON authentication and link APIs, redirects
    utils/                   JWT, security, validation, and configuration helpers
    templates/               Minimal server-rendered error pages
    static/                  Error-page styles
  tests/                     Python API and MongoDB integration checks
.dockerignore                Root build-context exclusions
docker-compose.yml           Services, networks, and persistent volume
.env.example                 Configuration template
LINK_MIGRATION.md            Existing-database migration instructions
```

`.editorconfig` and `.gitattributes` keep text files in UTF-8 with LF line endings.

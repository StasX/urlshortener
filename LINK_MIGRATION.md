Configure `PUBLIC_BASE_URL` in `.env` to the public origin, for example
`PUBLIC_BASE_URL=https://short.example.com`. The local development default is
`http://localhost:5000`. Generated links use this setting rather than request
headers. Redirect lookups use only the code and work over either scheme or host.

For an existing database:

1. Back up MongoDB and stop all application instances.
2. Set `PUBLIC_BASE_URL` and the existing `DB_NAME`, `DB_HOST`, and `DB_PORT` settings.
3. From the project root, run `python src/migrations/migrate_short_codes.py` before starting the updated application.
4. Start the application after the migration succeeds.

The migration preserves codes and visit counts, updates displayed short URLs to
the configured origin, and creates a unique code index. It checks all records
before writing and stops if legacy links have invalid or duplicate codes. Resolve
those records before rerunning it. The migration can be rerun after interruption.
An empty database needs no migration; MongoEngine creates the unique index.

Keep old domains routed to the application if previously issued links must remain
reachable. Changing the configured origin cannot update links already shared.

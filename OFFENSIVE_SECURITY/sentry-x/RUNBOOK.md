# RUNBOOK

## Running tests

```bash
source venv/bin/activate

# Unit tests only (no DB required - DB tests auto-skip if unreachable)
pytest tests/ -v -m "not integration" 2>/dev/null || pytest tests/ -v --ignore=tests/test_db.py

# Full suite including DB integration tests (requires a reachable test DB)
export SENTRYX_TEST_DB_HOST=localhost
export SENTRYX_TEST_DB_PORT=5432
export SENTRYX_TEST_DB_NAME=sentryx_test
export SENTRYX_TEST_DB_USER=sentryx_test
export SENTRYX_TEST_DB_PASSWORD=testpass123
pytest tests/ -v --cov=sentryx --cov-report=term-missing
```

Setting up the test database (one-time, local):

```bash
sudo -u postgres psql -c "CREATE USER sentryx_test WITH PASSWORD 'testpass123' SUPERUSER;"
sudo -u postgres psql -c "CREATE DATABASE sentryx_test OWNER sentryx_test;"
PGPASSWORD=testpass123 psql -h localhost -U sentryx_test -d sentryx_test -f migrations/001_init.sql
```

## Linting / static analysis

```bash
flake8 src/ tests/            # style
black --check --line-length 100 src/ tests/   # formatting
mypy src/sentryx/              # types
bandit -r src/ -q               # security static analysis
pip-audit -r requirements.txt   # known CVEs in dependencies
```

All five must be clean before merging - this is exactly what `.github/workflows/ci.yml` enforces.

## Deploying

### Option A — Docker Compose (recommended for a single host)

```bash
cp .env.example .env    # fill in secrets
docker compose up -d db
# wait for db healthcheck to pass (docker compose ps)
docker compose run --rm app sentryx check
```

The Postgres container auto-applies `migrations/*.sql` on first boot via
`docker-entrypoint-initdb.d`. On an existing volume, apply new migrations
manually:

```bash
docker compose exec -T db psql -U $SENTRYX_DB_USER -d $SENTRYX_DB_NAME \
    -f /docker-entrypoint-initdb.d/00X_new_migration.sql
```

### Option B — Bare metal / VM

See README.md "Quick start (local, no Docker)".

## Rollback

**Application code**: redeploy the previous Docker image tag
(`sentryx:<previous-sha>`) or `git checkout <previous-tag>` and reinstall
(`pip install -e .`). The app is stateless aside from the database, so
rolling the app back is safe at any time.

**Database schema**: `migrations/001_init.sql` is the only migration in this
delivery and it is purely additive (no destructive changes), so there is
nothing to roll back yet. For future migrations, write a matching
`00X_down.sql` alongside each `00X_up.sql` before applying it in production -
this repo does not yet have a migration framework (Alembic) wired in; see
"Known gaps" below.

**Data**: `scan_sessions` rows cascade-delete their children
(`tool_runs`, `vulnerabilities`, `fixes`, `ai_summaries`); `api_usage` rows
survive session deletion (`ON DELETE SET NULL`) so cost history is never
silently lost. Take a `pg_dump` before any destructive operation:

```bash
pg_dump -h $SENTRYX_DB_HOST -U $SENTRYX_DB_USER $SENTRYX_DB_NAME > backup-$(date +%F).sql
```

## Acceptance checklist

Before considering a change ready to merge:

- [ ] `pytest tests/` passes locally with a real test database (95/95 at time of writing)
- [ ] `flake8 src/ tests/` clean
- [ ] `black --check` clean
- [ ] `mypy src/sentryx/` clean
- [ ] `bandit -r src/` clean (or new findings explicitly suppressed with a
      `# nosec` comment explaining why)
- [ ] `pip-audit -r requirements.txt` clean, or a documented exception
- [ ] If `requirements.txt` changed: re-run `pip-audit` and re-pin to a
      specific version (never a range) before committing
- [ ] If `migrations/` changed: migration applies cleanly to a fresh
      database (`psql -f migrations/00X_*.sql`) and is idempotent
      (`CREATE TABLE IF NOT EXISTS`, etc.)
- [ ] CI green on the PR (`.github/workflows/ci.yml`)

## Cutting a release

```bash
git tag -a v0.1.0 -m "SENTRY-X v0.1.0"
git push origin v0.1.0
scripts/generate_checksums.sh > CHECKSUMS.sha256   # attach to the GitHub release, don't commit it
```

## Known gaps (not covered by this delivery)

- **No migration framework** (Alembic/Flyway) - `migrations/001_init.sql` is
  applied by hand or via the Postgres container's init-script mechanism.
  Fine for one migration; add Alembic before this grows to several.
- **No secrets vault integration** - secrets are environment variables only
  (`.env` locally, container env vars / CI secrets elsewhere). For a real
  production deployment, wire in Vault/AWS Secrets Manager/etc. and have
  `config.py` read from there instead.
- **No code signing / release signing** - this delivery has no cosign/GPG
  signing step. Add one in CI before treating built images as attestable
  artifacts.
- **No Metasploit/exploitation module** - see README "Scope note."
- **IAM / cloud deployment** - this repo does not include Terraform/IAM
  policies because no specific cloud target was given. The Docker image is
  cloud-agnostic; least-privilege IAM is a property of *where* you deploy
  it, not of the application code itself.

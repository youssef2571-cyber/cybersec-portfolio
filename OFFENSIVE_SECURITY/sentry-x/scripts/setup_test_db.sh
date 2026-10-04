#!/usr/bin/env bash
# Create and migrate a local PostgreSQL test database for running the full
# test suite (including tests/test_db.py integration tests).
set -euo pipefail

DB_USER="${SENTRYX_TEST_DB_USER:-sentryx_test}"
DB_PASS="${SENTRYX_TEST_DB_PASSWORD:-testpass123}"
DB_NAME="${SENTRYX_TEST_DB_NAME:-sentryx_test}"

echo "Creating role '${DB_USER}' and database '${DB_NAME}'..."
sudo -u postgres psql -v ON_ERROR_STOP=1 -c \
    "DO \$\$ BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_USER}') THEN
            CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}' SUPERUSER;
        END IF;
    END \$\$;"
sudo -u postgres psql -v ON_ERROR_STOP=1 -tc \
    "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'" | grep -q 1 || \
    sudo -u postgres psql -v ON_ERROR_STOP=1 -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

echo "Applying migrations..."
PGPASSWORD="${DB_PASS}" psql -h localhost -U "${DB_USER}" -d "${DB_NAME}" \
    -v ON_ERROR_STOP=1 -f "$(dirname "$0")/../migrations/001_init.sql"

echo "Done. Export these before running pytest:"
echo "  export SENTRYX_TEST_DB_HOST=localhost"
echo "  export SENTRYX_TEST_DB_PORT=5432"
echo "  export SENTRYX_TEST_DB_NAME=${DB_NAME}"
echo "  export SENTRYX_TEST_DB_USER=${DB_USER}"
echo "  export SENTRYX_TEST_DB_PASSWORD=${DB_PASS}"

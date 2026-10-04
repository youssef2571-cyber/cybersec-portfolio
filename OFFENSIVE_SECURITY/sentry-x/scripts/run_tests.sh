#!/usr/bin/env bash
# Run the full test suite with coverage. Assumes SENTRYX_TEST_DB_* env vars
# are set (see scripts/setup_test_db.sh) - DB-dependent tests auto-skip
# otherwise.
set -euo pipefail
cd "$(dirname "$0")/.."
pytest tests/ -v --cov=sentryx --cov-report=term-missing "$@"

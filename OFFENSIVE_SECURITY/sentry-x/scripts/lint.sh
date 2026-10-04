#!/usr/bin/env bash
# Run every static-analysis check this project requires before merge.
# Mirrors .github/workflows/ci.yml exactly.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== flake8 =="
flake8 src/ tests/

echo "== black --check =="
black --check --line-length 100 src/ tests/

echo "== mypy =="
mypy src/sentryx/

echo "== bandit =="
bandit -r src/ -q

echo "== pip-audit =="
pip-audit -r requirements.txt

echo "All checks passed."

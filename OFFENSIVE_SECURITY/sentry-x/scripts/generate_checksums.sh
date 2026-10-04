#!/usr/bin/env bash
# Generate a SHA256 checksum manifest of every tracked file, for release
# artifacts. Run this when cutting a release (e.g. in a GitHub Actions
# release job), not as a committed file in the repo - it goes stale the
# moment any tracked file changes.
#
# Usage: scripts/generate_checksums.sh > CHECKSUMS.sha256
set -euo pipefail
cd "$(dirname "$0")/.."

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git ls-files | sort | xargs sha256sum
else
    find . -type f -not -path './.git/*' -not -name '*.pyc' \
        | sed 's|^\./||' | sort | xargs sha256sum
fi

#!/usr/bin/env bash
# Publish the SDK wheel + sdist to PyPI (or TestPyPI).
#
# Requires: uv, a PyPI/TestPyPI API token exported as TWINE_PASSWORD
# (username is always `__token__`).
#
# Usage:
#   ./scripts/publish.sh --test   # dry-run to TestPyPI
#   ./scripts/publish.sh          # publish to real PyPI

set -euo pipefail

cd "$(dirname "$0")/.."

REPO="pypi"
if [ "${1:-}" = "--test" ]; then
  REPO="testpypi"
fi

if [ -z "${TWINE_PASSWORD:-}" ]; then
  echo "FAIL: TWINE_PASSWORD unset. Export a $REPO API token first." >&2
  exit 1
fi

export TWINE_USERNAME="${TWINE_USERNAME:-__token__}"

echo "[publish] validating dist/ artifacts"
uv tool run twine check dist/venturalitica-0.6.0*

echo "[publish] uploading to $REPO"
if [ "$REPO" = "testpypi" ]; then
  uv tool run twine upload --repository testpypi dist/venturalitica-0.6.0*
else
  uv tool run twine upload dist/venturalitica-0.6.0*
fi

echo "[publish] done."

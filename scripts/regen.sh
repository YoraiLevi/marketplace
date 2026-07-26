#!/usr/bin/env bash
# Regenerate all marketplace manifests and the generated catalog doc from src/.
# Pass --check to verify the committed output is in sync WITHOUT writing.
#   ./scripts/regen.sh          # write everything
#   ./scripts/regen.sh --check  # CI-style drift check (exit 1 on drift)
set -euo pipefail
cd "$(dirname "$0")/.."
exec uv run scripts/generate_manifest.py "$@"

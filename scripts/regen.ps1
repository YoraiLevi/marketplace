#!/usr/bin/env pwsh
# Regenerate all marketplace manifests and the generated catalog doc from src/.
# Pass --check to verify the committed output is in sync WITHOUT writing.
#   ./scripts/regen.ps1          # write everything
#   ./scripts/regen.ps1 --check  # CI-style drift check (exit 1 on drift)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
uv run scripts/generate_manifest.py @args
exit $LASTEXITCODE

#!/usr/bin/env bash
# Decrypt SOPS secrets + pulumi up (homelab stack) — imports live resources on first run.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
uv sync --quiet
exec uv run python ./scripts/pulumi_run.py up "$@"

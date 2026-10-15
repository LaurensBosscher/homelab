#!/usr/bin/env bash
# Decrypt SOPS secrets + pulumi preview (homelab stack).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
uv sync --quiet
exec uv run python ./scripts/pulumi_run.py preview "$@"

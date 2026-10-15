#!/usr/bin/env python3
"""Load SOPS secrets, then run pulumi against the homelab stack."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from infra_secrets import load_into_environ  # noqa: E402


def main(argv: list[str]) -> int:
    if not argv:
        print(
            "usage: pulumi_run.py <preview|up|refresh|...> [extra pulumi args...]",
            file=sys.stderr,
        )
        return 2

    load_into_environ(override=False)
    if not os.environ.get("CLOUDFLARE_API_TOKEN"):
        print("CLOUDFLARE_API_TOKEN is not set after sops load", file=sys.stderr)
        return 1

    # Local file backend; empty passphrase is fine for a personal laptop state store.
    os.environ.setdefault("PULUMI_CONFIG_PASSPHRASE", "")

    pulumi = shutil.which("pulumi")
    if pulumi is None:
        print("pulumi not found on PATH", file=sys.stderr)
        return 1

    cmd = [pulumi, *argv, "--stack", "homelab"]
    return subprocess.call(cmd, cwd=str(ROOT))  # noqa: S603


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

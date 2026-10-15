"""Decrypt infrastructure/cloudflare/secrets.enc.env via sops (no plaintext on disk)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENC_SECRETS = PROJECT_ROOT / "secrets.enc.env"
LOCAL_SECRETS = PROJECT_ROOT / "local_secrets.env"


def parse_dotenv(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.removeprefix("export ").partition("=")
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        result[key] = value
    return result


def decrypt_secrets(enc_file: Path = ENC_SECRETS) -> dict[str, str]:
    if not enc_file.exists() and LOCAL_SECRETS.exists():
        return parse_dotenv(LOCAL_SECRETS.read_text(encoding="utf-8"))
    if not enc_file.exists():
        msg = (
            f"Missing {enc_file} (and no {LOCAL_SECRETS.name}). "
            "Create with: sops encrypt --filename-override "
            "infrastructure/cloudflare/secrets.enc.env plaintext.env "
            "> infrastructure/cloudflare/secrets.enc.env"
        )
        raise FileNotFoundError(msg)
    if shutil.which("sops") is None:
        msg = f"Found {enc_file} but 'sops' is not on PATH"
        raise RuntimeError(msg)

    command = [
        "sops",
        "-d",
        "--input-type",
        "dotenv",
        "--output-type",
        "dotenv",
        str(enc_file),
    ]
    try:
        result = subprocess.run(  # noqa: S603
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        msg = (
            f"sops could not decrypt {enc_file}: {(exc.stderr or '').strip()}. "
            "Your SSH key must be a recipient in repo-root .sops.yaml."
        )
        raise RuntimeError(msg) from exc

    secrets = parse_dotenv(result.stdout)
    if LOCAL_SECRETS.exists():
        secrets |= parse_dotenv(LOCAL_SECRETS.read_text(encoding="utf-8"))
    return secrets


def load_into_environ(*, override: bool = False) -> None:
    for key, value in decrypt_secrets().items():
        if override or key not in os.environ:
            os.environ[key] = value

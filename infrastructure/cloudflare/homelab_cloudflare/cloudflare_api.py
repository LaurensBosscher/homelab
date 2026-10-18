"""Minimal Cloudflare REST helper for resources the provider cannot manage."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

_API = "https://api.cloudflare.com/client/v4"


def api_token() -> str:
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not token:
        msg = "CLOUDFLARE_API_TOKEN is required"
        raise RuntimeError(msg)
    return token


def request(method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = None if body is None else json.dumps(body).encode()
    url = f"{_API}{path}"
    if not url.startswith("https://api.cloudflare.com/"):
        msg = f"Refusing non-Cloudflare URL: {url}"
        raise ValueError(msg)
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_token()}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            parsed: dict[str, Any] = json.load(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        msg = f"Cloudflare {method} {path} failed: {exc.code} {detail}"
        raise RuntimeError(msg) from exc
    if not parsed.get("success", False):
        msg = f"Cloudflare {method} {path} unsuccessful: {parsed}"
        raise RuntimeError(msg)
    return parsed

"""Minimal Cloudflare REST helper for resources the provider cannot manage."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from enum import Enum
from typing import Any

_API = "https://api.cloudflare.com/client/v4"
# Cloudflare: "Record does not exist."
_DNS_RECORD_MISSING = 81044
_CLOUDFLARE_ID = re.compile(r"^[0-9a-f]{32}$")


def api_token() -> str:
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not token:
        msg = "CLOUDFLARE_API_TOKEN is required"
        raise RuntimeError(msg)
    return token


class DnsDeleteOutcome(Enum):
    DELETED = "deleted"
    ALREADY_GONE = "already_gone"


def classify_dns_delete(status: int, body: str) -> DnsDeleteOutcome:
    """A DNS DELETE 404, or error 81044, means the record is already gone."""
    if status == 404 or _has_error_code(body, _DNS_RECORD_MISSING):
        return DnsDeleteOutcome.ALREADY_GONE
    if 200 <= status < 300:
        if body.strip():
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError as exc:
                msg = f"Cloudflare DELETE dns record returned {status} with non-JSON body"
                raise RuntimeError(msg) from exc
            if isinstance(parsed, dict) and parsed.get("success") is False:
                msg = f"Cloudflare DELETE dns record unsuccessful: {parsed}"
                raise RuntimeError(msg)
        return DnsDeleteOutcome.DELETED
    msg = f"Cloudflare DELETE dns record failed: {status} {body}"
    raise RuntimeError(msg)


def delete_dns_record(zone_id: str, record_id: str) -> DnsDeleteOutcome:
    zone = _cloudflare_id(zone_id, label="zone id")
    record = _cloudflare_id(record_id, label="DNS record id")
    status, body = _http_call("DELETE", f"/zones/{zone}/dns_records/{record}")
    return classify_dns_delete(status, body)


def request(method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    status, detail = _http_call(method, path, body)
    if status >= 400:
        msg = f"Cloudflare {method} {path} failed: {status} {detail}"
        raise RuntimeError(msg)
    parsed: dict[str, Any] = json.loads(detail) if detail else {}
    if not parsed.get("success", False):
        msg = f"Cloudflare {method} {path} unsuccessful: {parsed}"
        raise RuntimeError(msg)
    return parsed


def _http_call(method: str, path: str, body: dict[str, Any] | None = None) -> tuple[int, str]:
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
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def _cloudflare_id(value: str, *, label: str) -> str:
    normalized = value.strip().lower()
    if _CLOUDFLARE_ID.fullmatch(normalized) is None:
        msg = f"invalid Cloudflare {label}"
        raise ValueError(msg)
    return normalized


def _has_error_code(body: str, code: int) -> bool:
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return False
    if not isinstance(parsed, dict):
        return False
    errors = parsed.get("errors")
    if not isinstance(errors, list):
        return False
    return any(isinstance(error, dict) and error.get("code") == code for error in errors)

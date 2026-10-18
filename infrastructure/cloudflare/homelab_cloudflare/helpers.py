from __future__ import annotations

import ipaddress
import os
from typing import Any

import pulumi

_ACCOUNT_CFG = "homelab-cloudflare"

# Cloudflare DNS TTL `1` means AUTO.
CLOUDFLARE_AUTO: float = 1.0


def account_id() -> str:
    return pulumi.Config(_ACCOUNT_CFG).require("accountId")


def require_env(name: str) -> str:
    """Read a SOPS value placed in the environment by scripts/pulumi_run.py."""
    value = os.environ.get(name, "").strip()
    if not value:
        msg = (
            f"{name} is not set. Add it to infrastructure/cloudflare/secrets.enc.env "
            "and run through ./pulumi_preview.sh so sops can decrypt it."
        )
        raise RuntimeError(msg)
    return value


def _parse_cidrs(raw: str, *, source: str) -> list[str]:
    cidrs: list[str] = []
    for part in raw.split(","):
        text = part.strip()
        if not text:
            continue
        try:
            network = ipaddress.ip_network(text, strict=False)
        except ValueError as exc:
            msg = f"{source} has an invalid CIDR {text!r}"
            raise RuntimeError(msg) from exc
        rendered = str(network)
        if rendered not in cidrs:
            cidrs.append(rendered)
    return cidrs


def env_cidrs(name: str, *extra_names: str) -> list[str]:
    """Comma-separated CIDRs from SOPS. `name` is required; extra names are optional."""
    cidrs = _parse_cidrs(require_env(name), source=name)
    for extra in extra_names:
        raw = os.environ.get(extra, "").strip()
        if not raw:
            continue
        for cidr in _parse_cidrs(raw, source=extra):
            if cidr not in cidrs:
                cidrs.append(cidr)
    return cidrs


def resource_opts(
    *,
    import_id: str | None = None,
    depends_on: list[Any] | None = None,
    ignore_changes: list[str] | None = None,
    protect: bool = False,
    additional: dict[str, Any] | None = None,
) -> pulumi.ResourceOptions:
    cfg = pulumi.Config(_ACCOUNT_CFG)
    import_existing = cfg.get_bool("importExisting")
    if import_existing is None:
        import_existing = True

    kwargs: dict[str, Any] = {}
    if import_existing and import_id:
        kwargs["import_"] = import_id
    if depends_on:
        kwargs["depends_on"] = depends_on
    if ignore_changes:
        kwargs["ignore_changes"] = ignore_changes
    if protect:
        kwargs["protect"] = True
    if additional:
        kwargs.update(additional)
    return pulumi.ResourceOptions(**kwargs)

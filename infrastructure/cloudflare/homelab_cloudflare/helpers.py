from __future__ import annotations

from typing import Any

import pulumi

_ACCOUNT_CFG = "homelab-cloudflare"

# Cloudflare DNS TTL `1` means AUTO.
CLOUDFLARE_AUTO: float = 1.0


def account_id() -> str:
    return pulumi.Config(_ACCOUNT_CFG).require("accountId")


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

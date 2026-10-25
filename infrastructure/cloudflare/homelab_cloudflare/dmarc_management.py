"""Cloudflare DMARC Management.

No provider resource yet. Dynamic resource over
PATCH /zones/{id}/email/auth/dmarc-reports. The `_dmarc` TXT records in
`dns.py` must include each zone's Cloudflare RUA or reports are dropped.
`skip_wizard` keeps Cloudflare from rewriting those TXT records itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pulumi
from pulumi.dynamic import (
    CreateResult,
    DiffResult,
    ReadResult,
    Resource,
    ResourceProvider,
    UpdateResult,
)

from homelab_cloudflare.cloudflare_api import request
from homelab_cloudflare.helpers import resource_opts


def _ensure(*, zone_id: str, enabled: bool, skip_wizard: bool) -> dict[str, Any]:
    result = request(
        "PATCH",
        f"/zones/{zone_id}/email/auth/dmarc-reports",
        {"enabled": enabled, "skip_wizard": skip_wizard},
    )
    data = result.get("result")
    if not isinstance(data, dict):
        msg = f"Unexpected DMARC Management PATCH response for zone {zone_id}"
        raise TypeError(msg)
    return data


def _read_live(zone_id: str) -> dict[str, Any]:
    result = request("GET", f"/zones/{zone_id}/email/auth/dmarc-reports")
    data = result.get("result")
    if not isinstance(data, dict):
        msg = f"Unexpected DMARC Management GET response for zone {zone_id}"
        raise TypeError(msg)
    return data


class _DmarcManagementProvider(ResourceProvider):
    @override
    def create(self, props: dict[str, Any]) -> CreateResult:
        zone_id = str(props["zone_id"])
        enabled = bool(props.get("enabled", True))
        skip_wizard = bool(props.get("skip_wizard", True))
        live = _ensure(zone_id=zone_id, enabled=enabled, skip_wizard=skip_wizard)
        return CreateResult(
            id_=zone_id,
            outs={
                "zone_id": zone_id,
                "enabled": enabled,
                "skip_wizard": skip_wizard,
                "rua_prefix": live.get("rua_prefix"),
            },
        )

    @override
    def diff(self, _id: str, olds: dict[str, Any], news: dict[str, Any]) -> DiffResult:
        watched = ("enabled", "skip_wizard", "zone_id")
        changed = [key for key in watched if olds.get(key) != news.get(key)]
        return DiffResult(
            changes=bool(changed),
            replaces=["zone_id"] if "zone_id" in changed else [],
            stables=[],
            delete_before_replace=False,
        )

    @override
    def update(self, _id: str, _olds: dict[str, Any], news: dict[str, Any]) -> UpdateResult:
        zone_id = str(news["zone_id"])
        enabled = bool(news.get("enabled", True))
        skip_wizard = bool(news.get("skip_wizard", True))
        live = _ensure(zone_id=zone_id, enabled=enabled, skip_wizard=skip_wizard)
        return UpdateResult(
            outs={
                "zone_id": zone_id,
                "enabled": enabled,
                "skip_wizard": skip_wizard,
                "rua_prefix": live.get("rua_prefix"),
            },
        )

    @override
    def read(self, id_: str, props: dict[str, Any]) -> ReadResult:
        live = _read_live(id_)
        return ReadResult(
            id_=id_,
            outs={
                "zone_id": id_,
                "enabled": bool(live.get("enabled")),
                "skip_wizard": bool(props.get("skip_wizard", True)),
                "rua_prefix": live.get("rua_prefix"),
            },
        )

    @override
    def delete(self, _id: str, _props: dict[str, Any]) -> None:
        # Leave reporting on. Disabling drops visibility without a DNS benefit.
        return None


class DmarcManagement(Resource):
    zone_id: pulumi.Output[str]
    enabled: pulumi.Output[bool]
    skip_wizard: pulumi.Output[bool]
    rua_prefix: pulumi.Output[str | None]

    def __init__(
        self,
        name: str,
        *,
        zone_id: pulumi.Input[str],
        enabled: pulumi.Input[bool] = True,
        skip_wizard: pulumi.Input[bool] = True,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__(
            _DmarcManagementProvider(),
            name,
            {
                "zone_id": zone_id,
                "enabled": enabled,
                "skip_wizard": skip_wizard,
                "rua_prefix": None,
            },
            opts,
        )


@dataclass(frozen=True, slots=True)
class DmarcManagementResources:
    by_name: dict[str, DmarcManagement]


def create_dmarc_management(*, zone_ids: dict[str, pulumi.Input[str]]) -> DmarcManagementResources:
    by_name: dict[str, DmarcManagement] = {}
    # No import_: Pulumi dynamic resources cannot import. create() PATCHes
    # enabled=true, which is safe when the zone is already on.
    for zone_name, resource_name in (
        ("bosscher.ch", "dmarc-mgmt-bosscher-ch"),
        ("laurensbosscher.nl", "dmarc-mgmt-laurensbosscher-nl"),
    ):
        by_name[zone_name] = DmarcManagement(
            resource_name,
            zone_id=zone_ids[zone_name],
            enabled=True,
            skip_wizard=True,
            opts=resource_opts(),
        )

    pulumi.export("dmarc_management_zones", sorted(by_name))
    return DmarcManagementResources(by_name=by_name)

"""Zone bot settings.

The pulumi-cloudflare 6.x Bot Management resource PUTs read-only
`using_latest_model`, which Cloudflare rejects (API 10400). This dynamic
resource writes only the managed knobs.
"""

from __future__ import annotations

from typing import Any, Final, override

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

# Managed knobs only. Do not send read-only `using_latest_model`.
_MANAGED_KEYS: Final[tuple[str, ...]] = (
    "enable_js",
    "fight_mode",
    "ai_bots_protection",
    "content_bots_protection",
    "crawler_protection",
    "is_robots_txt_managed",
)


def _managed_body(props: dict[str, Any]) -> dict[str, Any]:
    return {
        "enable_js": bool(props["enable_js"]),
        "fight_mode": bool(props["fight_mode"]),
        "ai_bots_protection": str(props["ai_bots_protection"]),
        "content_bots_protection": str(props["content_bots_protection"]),
        "crawler_protection": str(props["crawler_protection"]),
        "is_robots_txt_managed": bool(props["is_robots_txt_managed"]),
    }


def _outs(zone_id: str, props: dict[str, Any]) -> dict[str, Any]:
    return {"zone_id": zone_id, **_managed_body(props)}


def _ensure(props: dict[str, Any]) -> None:
    zone_id = str(props["zone_id"])
    result = request("PUT", f"/zones/{zone_id}/bot_management", _managed_body(props))
    if not isinstance(result.get("result"), dict):
        msg = f"Unexpected Bot Management PUT response for zone {zone_id}"
        raise TypeError(msg)


def _read_live(zone_id: str) -> dict[str, Any]:
    result = request("GET", f"/zones/{zone_id}/bot_management")
    data = result.get("result")
    if not isinstance(data, dict):
        msg = f"Unexpected Bot Management GET response for zone {zone_id}"
        raise TypeError(msg)
    return data


class _BotManagementProvider(ResourceProvider):
    @override
    def create(self, props: dict[str, Any]) -> CreateResult:
        zone_id = str(props["zone_id"])
        _ensure(props)
        return CreateResult(id_=zone_id, outs=_outs(zone_id, props))

    @override
    def diff(self, _id: str, olds: dict[str, Any], news: dict[str, Any]) -> DiffResult:
        changed = [key for key in ("zone_id", *_MANAGED_KEYS) if olds.get(key) != news.get(key)]
        return DiffResult(
            changes=bool(changed),
            replaces=["zone_id"] if "zone_id" in changed else [],
            stables=[],
            delete_before_replace=False,
        )

    @override
    def update(self, _id: str, _olds: dict[str, Any], news: dict[str, Any]) -> UpdateResult:
        zone_id = str(news["zone_id"])
        _ensure(news)
        return UpdateResult(outs=_outs(zone_id, news))

    @override
    def read(self, id_: str, props: dict[str, Any]) -> ReadResult:
        live = _read_live(id_)
        merged = {
            "enable_js": bool(live.get("enable_js", props.get("enable_js"))),
            "fight_mode": bool(live.get("fight_mode", props.get("fight_mode"))),
            "ai_bots_protection": str(
                live.get("ai_bots_protection", props.get("ai_bots_protection", "disabled"))
            ),
            "content_bots_protection": str(
                live.get(
                    "content_bots_protection",
                    props.get("content_bots_protection", "disabled"),
                )
            ),
            "crawler_protection": str(
                live.get("crawler_protection", props.get("crawler_protection", "disabled"))
            ),
            "is_robots_txt_managed": bool(
                live.get("is_robots_txt_managed", props.get("is_robots_txt_managed"))
            ),
        }
        return ReadResult(id_=id_, outs=_outs(id_, merged))

    @override
    def delete(self, _id: str, _props: dict[str, Any]) -> None:
        # Zone singleton. Dropping it from state must not turn protections off.
        return None


class BotManagement(Resource):
    zone_id: pulumi.Output[str]
    enable_js: pulumi.Output[bool]
    fight_mode: pulumi.Output[bool]
    ai_bots_protection: pulumi.Output[str]
    content_bots_protection: pulumi.Output[str]
    crawler_protection: pulumi.Output[str]
    is_robots_txt_managed: pulumi.Output[bool]

    def __init__(
        self,
        name: str,
        *,
        zone_id: pulumi.Input[str],
        enable_js: pulumi.Input[bool],
        fight_mode: pulumi.Input[bool],
        ai_bots_protection: pulumi.Input[str],
        content_bots_protection: pulumi.Input[str],
        crawler_protection: pulumi.Input[str],
        is_robots_txt_managed: pulumi.Input[bool],
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__(
            _BotManagementProvider(),
            name,
            {
                "zone_id": zone_id,
                "enable_js": enable_js,
                "fight_mode": fight_mode,
                "ai_bots_protection": ai_bots_protection,
                "content_bots_protection": content_bots_protection,
                "crawler_protection": crawler_protection,
                "is_robots_txt_managed": is_robots_txt_managed,
            },
            opts,
        )

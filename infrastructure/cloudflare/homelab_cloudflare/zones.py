from __future__ import annotations

from dataclasses import dataclass

import pulumi_cloudflare as cloudflare

from homelab_cloudflare.helpers import account_id, resource_opts

_BOSSCHER_CH_ZONE_ID = "e32ce9cb10fafea8ee531b713afdcc10"
_BOSSSCHER_ORG_ZONE_ID = "981bc8749d817cd910da39e8a8aefd7f"
_LAURENSBOSSCHER_NL_ZONE_ID = "80109e07e6038846aa25d17367211948"


@dataclass(frozen=True, slots=True)
class Zones:
    by_name: dict[str, cloudflare.Zone]


def create_zones() -> Zones:
    acct = account_id()
    by_name: dict[str, cloudflare.Zone] = {}

    by_name["bosscher.ch"] = cloudflare.Zone(
        "zone-bosscher-ch",
        account={"id": acct},
        name="bosscher.ch",
        type="full",
        paused=False,
        vanity_name_servers=[],
        opts=resource_opts(protect=True, import_id=_BOSSCHER_CH_ZONE_ID),
    )

    by_name["bossscher.org"] = cloudflare.Zone(
        "zone-bossscher-org",
        account={"id": acct},
        name="bossscher.org",
        type="full",
        paused=False,
        vanity_name_servers=[],
        opts=resource_opts(protect=True, import_id=_BOSSSCHER_ORG_ZONE_ID),
    )

    by_name["laurensbosscher.nl"] = cloudflare.Zone(
        "zone-laurensbosscher-nl",
        account={"id": acct},
        name="laurensbosscher.nl",
        type="full",
        paused=False,
        vanity_name_servers=[],
        opts=resource_opts(protect=True, import_id=_LAURENSBOSSCHER_NL_ZONE_ID),
    )

    return Zones(by_name=by_name)


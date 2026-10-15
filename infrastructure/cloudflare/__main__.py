from __future__ import annotations

import pulumi

from homelab_cloudflare.dns import create_dns_records
from homelab_cloudflare.tunnels import create_tunnels
from homelab_cloudflare.zones import create_zones

cfg = pulumi.Config("homelab-cloudflare")
pulumi.export("account_id", cfg.require("accountId"))
pulumi.export("account_name", cfg.get("accountName") or "Laurens homelab")

zones = create_zones()
zone_ids: dict[str, pulumi.Input[str]] = {name: zone.id for name, zone in zones.by_name.items()}
dns = create_dns_records(zone_ids=zone_ids)
tunnels = create_tunnels()

_ = (zones, dns, tunnels)

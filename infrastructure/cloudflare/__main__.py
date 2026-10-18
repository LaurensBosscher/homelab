from __future__ import annotations

import pulumi

from homelab_cloudflare.access import create_access
from homelab_cloudflare.dmarc_management import create_dmarc_management
from homelab_cloudflare.dns import create_dns_records
from homelab_cloudflare.notifications import create_tunnel_notifications
from homelab_cloudflare.r2 import create_r2_buckets
from homelab_cloudflare.tunnels import create_tunnels
from homelab_cloudflare.zones import create_zones

cfg = pulumi.Config("homelab-cloudflare")
pulumi.export("account_id", cfg.require("accountId"))
pulumi.export("account_name", cfg.get("accountName") or "Laurens homelab")

zones = create_zones()
zone_ids: dict[str, pulumi.Input[str]] = {name: zone.id for name, zone in zones.by_name.items()}
dns = create_dns_records(zone_ids=zone_ids)
dmarc = create_dmarc_management(zone_ids=zone_ids)
r2 = create_r2_buckets()
tunnels = create_tunnels()
tunnel_notifications = create_tunnel_notifications(tunnels=tunnels)
access = create_access()
pulumi.export("access_agent_client_id", access.service_token.client_id)
pulumi.export("access_agent_client_secret", access.service_token.client_secret)

_ = (zones, dns, dmarc, r2, tunnels, tunnel_notifications, access)

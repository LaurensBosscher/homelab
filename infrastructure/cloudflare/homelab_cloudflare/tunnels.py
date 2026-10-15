from __future__ import annotations

from dataclasses import dataclass

import pulumi_cloudflare as cloudflare

from homelab_cloudflare.helpers import account_id, resource_opts
from homelab_cloudflare.inventory import tunnels as tunnel_refs


@dataclass(frozen=True, slots=True)
class Tunnels:
    k8s: cloudflare.ZeroTrustTunnelCloudflared
    openstick: cloudflare.ZeroTrustTunnelCloudflared


def create_tunnels() -> Tunnels:
    acct = account_id()
    k8s = cloudflare.ZeroTrustTunnelCloudflared(
        tunnel_refs.k8s_tunnel.resource_name,
        account_id=acct,
        name=tunnel_refs.k8s_tunnel.name,
        config_src="cloudflare",
        opts=resource_opts(
            protect=True,
            import_id=tunnel_refs.k8s_tunnel.import_id(acct),
            ignore_changes=["tunnel_secret", "conns_active_at", "conns_inactive_at"],
        ),
    )
    openstick = cloudflare.ZeroTrustTunnelCloudflared(
        tunnel_refs.openstick.resource_name,
        account_id=acct,
        name=tunnel_refs.openstick.name,
        config_src="cloudflare",
        opts=resource_opts(
            protect=True,
            import_id=tunnel_refs.openstick.import_id(acct),
            ignore_changes=["tunnel_secret", "conns_active_at", "conns_inactive_at"],
        ),
    )
    return Tunnels(k8s=k8s, openstick=openstick)

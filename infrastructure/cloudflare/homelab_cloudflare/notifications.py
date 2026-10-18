"""Tunnel health and lifecycle alerts.

Dollar budget alerts already exist in the dashboard and are not a Pulumi
resource. This stack does not add a Workers request alert: the account is on
the Free plan.
"""

from __future__ import annotations

from dataclasses import dataclass

import pulumi
import pulumi_cloudflare as cloudflare

from homelab_cloudflare.helpers import account_id, resource_opts
from homelab_cloudflare.tunnels import Tunnels

# Same mailbox already used by the account's Cloudflare alerts.
TUNNEL_ALERT_EMAILS: tuple[str, ...] = ("laurens@laurensbosscher.nl",)


@dataclass(frozen=True, slots=True)
class TunnelNotifications:
    health: cloudflare.NotificationPolicy
    lifecycle: cloudflare.NotificationPolicy


def create_tunnel_notifications(*, tunnels: Tunnels) -> TunnelNotifications:
    acct = account_id()
    mechanisms = cloudflare.NotificationPolicyMechanismsArgs(
        emails=[
            cloudflare.NotificationPolicyMechanismsEmailArgs(id=email)
            for email in TUNNEL_ALERT_EMAILS
        ],
    )
    health = cloudflare.NotificationPolicy(
        "notify-tunnel-health",
        account_id=acct,
        name="Tunnel health",
        description="Email when k8s-tunnel or openstick health status changes.",
        enabled=True,
        alert_type="tunnel_health_event",
        mechanisms=mechanisms,
        filters=cloudflare.NotificationPolicyFiltersArgs(
            tunnel_ids=[tunnels.k8s.id, tunnels.openstick.id],
        ),
        opts=resource_opts(),
    )
    lifecycle = cloudflare.NotificationPolicy(
        "notify-tunnel-lifecycle",
        account_id=acct,
        name="Tunnel created / deleted",
        description="Email when a Cloudflare Tunnel is created or deleted in this account.",
        enabled=True,
        alert_type="tunnel_update_event",
        mechanisms=mechanisms,
        opts=resource_opts(),
    )
    pulumi.export("tunnel_alert_emails", list(TUNNEL_ALERT_EMAILS))
    return TunnelNotifications(health=health, lifecycle=lifecycle)

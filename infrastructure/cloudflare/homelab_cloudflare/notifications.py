"""Tunnel health and lifecycle alerts.

Dollar budget alerts already exist in the dashboard and are not a Pulumi
resource. This stack does not add a Workers request alert: the account is on
the Free plan.
"""

from __future__ import annotations

from dataclasses import dataclass

import pulumi_cloudflare as cloudflare

from homelab_cloudflare.helpers import account_id, require_env, resource_opts
from homelab_cloudflare.tunnels import Tunnels


@dataclass(frozen=True, slots=True)
class TunnelNotifications:
    health: cloudflare.NotificationPolicy
    lifecycle: cloudflare.NotificationPolicy


def create_tunnel_notifications(*, tunnels: Tunnels) -> TunnelNotifications:
    acct = account_id()
    alert_email = require_env("ACCESS_EMAIL_LAURENS")
    mechanisms = cloudflare.NotificationPolicyMechanismsArgs(
        emails=[cloudflare.NotificationPolicyMechanismsEmailArgs(id=alert_email)],
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
    return TunnelNotifications(health=health, lifecycle=lifecycle)

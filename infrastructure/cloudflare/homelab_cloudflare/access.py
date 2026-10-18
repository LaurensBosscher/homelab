from __future__ import annotations

import ipaddress
import json
import urllib.error
import urllib.request
from dataclasses import dataclass

import pulumi
import pulumi_cloudflare as cloudflare

from homelab_cloudflare.helpers import account_id, env_cidrs, require_env, resource_opts

# GitHub webhook deliveries come from the `hooks` list, not Actions runners.
# https://api.github.com/meta — `actions` is thousands of shared runner CIDRs.
_GITHUB_META_URL = "https://api.github.com/meta"

# Live Cloudflare Access inventory (account 1ce5b40c4616a803216dff853ef6bc81).
# Policies are reusable and attached to apps by id + precedence.
_POLICY_ALLOW_LAURENS = "2d0a3dce-c353-4905-8482-46fb7c097ad8"
_POLICY_ALLOW_EVERYONE_CH = "50d94650-799a-43f5-8bc1-8e0f0543552a"
_POLICY_ALLOW_JAGODA = "631b6cd0-cd1d-4cfc-a335-b54c9c9384bc"
_POLICY_ALLOW_EVERYONE = "5b69403e-4582-422c-847b-30d77c5f2908"
_POLICY_WORKERS_PREVIEW = "435019b6-e2aa-4003-bde6-a4a986dbcb8d"

_IDP_ONETIMEPIN = "d532f784-f359-4ee1-a665-e252e1affdf7"

_APP_BOOKMARKS = "765c0c6e-b9f5-47b0-a7a0-512ad180318e"
_APP_AIOSTREAMS = "50ac511b-c684-49a1-a251-77c7cc2d6024"
_APP_WILDCARD = "7e7e79da-9545-4f50-b36e-8aa3dc4801fc"
_APP_BOSSCHER_CH = "0b9fad7d-edc5-4297-b3f2-9cfb610fb8b0"
_APP_LAUNCHER = "64079540-3a30-4c62-9590-6e1597893bb2"
_APP_ARGOCD_WEBHOOK = "3f4585b9-03d6-49ca-be3d-7f461fdd34a4"
_APP_SHARED_JAGODA = "9c16d8c4-50fe-4b3c-bab7-0a2c4da8045c"


@dataclass(frozen=True, slots=True)
class Access:
    identity_provider: cloudflare.ZeroTrustAccessIdentityProvider
    service_token: cloudflare.ZeroTrustAccessServiceToken
    policies: dict[str, cloudflare.ZeroTrustAccessPolicy]
    applications: dict[str, cloudflare.ZeroTrustAccessApplication]


def _policy_import(acct: str, policy_id: str) -> str:
    return f"{acct}/{policy_id}"


def _account_import(acct: str, resource_id: str) -> str:
    return f"accounts/{acct}/{resource_id}"


def _binding(
    policy: cloudflare.ZeroTrustAccessPolicy, precedence: int
) -> dict[str, pulumi.Input[str] | int]:
    return {"id": policy.id, "precedence": precedence}


def _public_destinations(uris: list[str]) -> list[dict[str, str]]:
    return [{"type": "public", "uri": uri} for uri in uris]


def _ip_includes(cidrs: list[str]) -> list[dict[str, dict[str, str]]]:
    return [{"ip": {"ip": cidr}} for cidr in cidrs]


def _github_hook_cidrs() -> list[str]:
    """Current GitHub webhook source ranges. Refreshed on each preview/up."""
    request = urllib.request.Request(
        _GITHUB_META_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "homelab-cloudflare-pulumi",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        msg = f"Could not read GitHub hook IP ranges from {_GITHUB_META_URL}"
        raise RuntimeError(msg) from exc
    hooks = payload.get("hooks") if isinstance(payload, dict) else None
    if not isinstance(hooks, list) or not hooks:
        msg = "GitHub meta response did not include hook IP ranges"
        raise RuntimeError(msg)
    cidrs: list[str] = []
    for item in hooks:
        if not isinstance(item, str):
            msg = "GitHub meta hooks entry was not a CIDR string"
            raise RuntimeError(msg)
        try:
            network = ipaddress.ip_network(item, strict=False)
        except ValueError as exc:
            msg = f"GitHub meta published an invalid hook CIDR {item!r}"
            raise RuntimeError(msg) from exc
        rendered = str(network)
        if rendered not in cidrs:
            cidrs.append(rendered)
    return sorted(cidrs, key=lambda cidr: (":" in cidr, cidr))


def create_access() -> Access:
    acct = account_id()
    email_laurens = require_env("ACCESS_EMAIL_LAURENS")
    email_jagoda = require_env("ACCESS_EMAIL_JAGODA")
    home_cidr = require_env("ACCESS_HOME_CIDR")
    # Home CIDR is always included. Add Jagoda later with ACCESS_AIOSTREAMS_EXTRA_CIDRS.
    aiostreams_cidrs = env_cidrs("ACCESS_HOME_CIDR", "ACCESS_AIOSTREAMS_EXTRA_CIDRS")
    policies: dict[str, cloudflare.ZeroTrustAccessPolicy] = {}

    policies["allow-laurensbosscher-nl"] = cloudflare.ZeroTrustAccessPolicy(
        "access-policy-allow-laurensbosscher-nl",
        account_id=acct,
        name="Allow @laurensbosscher.nl",
        decision="allow",
        session_duration="730h",
        includes=[{"email_domain": {"domain": "laurensbosscher.nl"}}],
        opts=resource_opts(import_id=_policy_import(acct, _POLICY_ALLOW_LAURENS)),
    )
    policies["aiostreams-ips"] = cloudflare.ZeroTrustAccessPolicy(
        "access-policy-allow-everyone-ch",
        account_id=acct,
        name="AIOStreams allowed IPs",
        decision="bypass",
        session_duration="24h",
        includes=_ip_includes(aiostreams_cidrs),
        opts=resource_opts(import_id=_policy_import(acct, _POLICY_ALLOW_EVERYONE_CH)),
    )
    policies["allow-jagoda"] = cloudflare.ZeroTrustAccessPolicy(
        "access-policy-allow-jagoda",
        account_id=acct,
        name="Allow Jagoda",
        decision="allow",
        session_duration="24h",
        includes=[{"email": {"email": email_jagoda}}],
        opts=resource_opts(import_id=_policy_import(acct, _POLICY_ALLOW_JAGODA)),
    )
    policies["allow-everyone"] = cloudflare.ZeroTrustAccessPolicy(
        "access-policy-allow-everyone",
        account_id=acct,
        name="Allow Everyone",
        decision="bypass",
        session_duration="24h",
        includes=[{"everyone": {}}],
        opts=resource_opts(import_id=_policy_import(acct, _POLICY_ALLOW_EVERYONE)),
    )
    policies["workers-preview"] = cloudflare.ZeroTrustAccessPolicy(
        "access-policy-workers-preview",
        account_id=acct,
        name="Cloudflare Workers Preview URLs",
        decision="allow",
        includes=[{"email": {"email": email_laurens}}],
        opts=resource_opts(import_id=_policy_import(acct, _POLICY_WORKERS_PREVIEW)),
    )
    service_token = cloudflare.ZeroTrustAccessServiceToken(
        "access-service-token-homelab-agents",
        account_id=acct,
        name="homelab-agents",
        # Non-expiring. Rotate by bumping client_secret_version if it leaks.
        duration="forever",
        opts=resource_opts(),
    )
    policies["homelab-agents"] = cloudflare.ZeroTrustAccessPolicy(
        "access-policy-homelab-agents",
        account_id=acct,
        name="Homelab agent service token",
        decision="non_identity",
        # Include is the token. Require is AND, so the same token is rejected
        # from every other network.
        includes=[{"service_token": {"token_id": service_token.id}}],
        requires=[{"ip": {"ip": home_cidr}}],
        opts=resource_opts(),
    )
    policies["github-hooks"] = cloudflare.ZeroTrustAccessPolicy(
        "access-policy-github-hooks",
        account_id=acct,
        name="GitHub webhook source IPs",
        decision="bypass",
        includes=_ip_includes(_github_hook_cidrs()),
        opts=resource_opts(),
    )

    identity_provider = cloudflare.ZeroTrustAccessIdentityProvider(
        "access-idp-onetimepin",
        account_id=acct,
        name="One-time PIN",
        type="onetimepin",
        config={
            "redirect_url": "https://laurens-bosscher.cloudflareaccess.com/cdn-cgi/access/callback",
        },
        opts=resource_opts(
            import_id=_account_import(acct, _IDP_ONETIMEPIN),
            # Cloudflare owns the callback URL and reports an empty display name.
            ignore_changes=["name", "config"],
        ),
    )

    applications: dict[str, cloudflare.ZeroTrustAccessApplication] = {}
    applications["bookmarks-alameda"] = cloudflare.ZeroTrustAccessApplication(
        "access-app-bookmarks-alameda",
        account_id=acct,
        name="bookmarks-alameda - Cloudflare Pages",
        type="self_hosted",
        domain="*.bookmarks-alameda.pages.dev",
        destinations=_public_destinations(
            ["*.bookmarks-alameda.pages.dev", "bookmarks.bosscher.ch"]
        ),
        session_duration="24h",
        app_launcher_visible=True,
        auto_redirect_to_identity=False,
        allowed_idps=[identity_provider.id],
        enable_binding_cookie=False,
        http_only_cookie_attribute=True,
        options_preflight_bypass=False,
        policies=[
            _binding(policies["homelab-agents"], 1),
            _binding(policies["allow-laurensbosscher-nl"], 2),
        ],
        opts=resource_opts(import_id=_account_import(acct, _APP_BOOKMARKS)),
    )
    applications["aiostreams"] = cloudflare.ZeroTrustAccessApplication(
        "access-app-aiostreams",
        account_id=acct,
        name="AIOStreams",
        type="self_hosted",
        domain="aiostreams.bosscher.ch/stremio/*.json",
        destinations=_public_destinations(["aiostreams.bosscher.ch/stremio/*.json"]),
        session_duration="24h",
        app_launcher_visible=False,
        auto_redirect_to_identity=False,
        enable_binding_cookie=False,
        http_only_cookie_attribute=False,
        options_preflight_bypass=False,
        policies=[_binding(policies["aiostreams-ips"], 1)],
        opts=resource_opts(import_id=_account_import(acct, _APP_AIOSTREAMS)),
    )
    applications["wildcard-bosscher-ch"] = cloudflare.ZeroTrustAccessApplication(
        "access-app-wildcard-bosscher-ch",
        account_id=acct,
        name="*.bosscher.ch",
        type="self_hosted",
        domain="*.bosscher.ch",
        destinations=_public_destinations(["*.bosscher.ch"]),
        session_duration="730h",
        app_launcher_visible=True,
        auto_redirect_to_identity=False,
        allow_authenticate_via_warp=False,
        enable_binding_cookie=True,
        http_only_cookie_attribute=True,
        options_preflight_bypass=False,
        same_site_cookie_attribute="none",
        # Service Auth is first so a token from home is not sent to the email login.
        # It does not set Cf-Access-Authenticated-User-Email.
        policies=[
            _binding(policies["homelab-agents"], 1),
            _binding(policies["allow-laurensbosscher-nl"], 2),
        ],
        opts=resource_opts(import_id=_account_import(acct, _APP_WILDCARD)),
    )
    for key, hostname in (
        ("kite", "kite.bosscher.ch"),
        ("shelfarr", "shelfarr.bosscher.ch"),
    ):
        applications[key] = cloudflare.ZeroTrustAccessApplication(
            f"access-app-{key}",
            account_id=acct,
            name=hostname,
            type="self_hosted",
            domain=hostname,
            destinations=_public_destinations([hostname]),
            session_duration="730h",
            app_launcher_visible=False,
            auto_redirect_to_identity=False,
            allow_authenticate_via_warp=False,
            enable_binding_cookie=True,
            http_only_cookie_attribute=True,
            options_preflight_bypass=False,
            same_site_cookie_attribute="none",
            policies=[
                _binding(policies["homelab-agents"], 1),
                _binding(policies["allow-laurensbosscher-nl"], 2),
            ],
            opts=resource_opts(),
        )
    applications["bosscher-ch"] = cloudflare.ZeroTrustAccessApplication(
        "access-app-bosscher-ch",
        account_id=acct,
        name="bosscher.ch",
        type="self_hosted",
        domain="bosscher.ch",
        destinations=_public_destinations(["bosscher.ch", "laurensbosscher.nl"]),
        session_duration="24h",
        app_launcher_visible=True,
        auto_redirect_to_identity=False,
        enable_binding_cookie=False,
        http_only_cookie_attribute=False,
        options_preflight_bypass=False,
        policies=[_binding(policies["allow-everyone"], 1)],
        opts=resource_opts(import_id=_account_import(acct, _APP_BOSSCHER_CH)),
    )
    applications["app-launcher"] = cloudflare.ZeroTrustAccessApplication(
        "access-app-launcher",
        account_id=acct,
        name="App Launcher",
        type="app_launcher",
        domain="laurens-bosscher.cloudflareaccess.com",
        session_duration="168h",
        auto_redirect_to_identity=True,
        allowed_idps=[identity_provider.id],
        policies=[
            _binding(policies["homelab-agents"], 1),
            _binding(policies["allow-laurensbosscher-nl"], 2),
        ],
        opts=resource_opts(import_id=_account_import(acct, _APP_LAUNCHER)),
    )
    applications["argocd-webhook"] = cloudflare.ZeroTrustAccessApplication(
        "access-app-argocd-webhook",
        account_id=acct,
        name="argocd webhook (GitHub hooks)",
        type="self_hosted",
        domain="argocd.bosscher.ch/api/webhook",
        destinations=_public_destinations(["argocd.bosscher.ch/api/webhook"]),
        session_duration="24h",
        app_launcher_visible=True,
        auto_redirect_to_identity=False,
        enable_binding_cookie=False,
        http_only_cookie_attribute=False,
        options_preflight_bypass=False,
        policies=[_binding(policies["github-hooks"], 1)],
        opts=resource_opts(import_id=_account_import(acct, _APP_ARGOCD_WEBHOOK)),
    )
    applications["shared-with-jagoda"] = cloudflare.ZeroTrustAccessApplication(
        "access-app-shared-with-jagoda",
        account_id=acct,
        name="Shared With Jagoda",
        type="self_hosted",
        domain="wanderer.bosscher.ch",
        destinations=_public_destinations(
            [
                "wanderer.bosscher.ch",
                "norish.bosscher.ch",
                "stacks.bosscher.ch",
                "calibre-web.bosscher.ch",
            ]
        ),
        session_duration="24h",
        app_launcher_visible=True,
        auto_redirect_to_identity=False,
        enable_binding_cookie=False,
        http_only_cookie_attribute=False,
        options_preflight_bypass=False,
        policies=[
            _binding(policies["homelab-agents"], 1),
            _binding(policies["allow-jagoda"], 2),
            _binding(policies["allow-laurensbosscher-nl"], 3),
        ],
        opts=resource_opts(import_id=_account_import(acct, _APP_SHARED_JAGODA)),
    )

    return Access(
        identity_provider=identity_provider,
        service_token=service_token,
        policies=policies,
        applications=applications,
    )

from __future__ import annotations

from dataclasses import dataclass

import pulumi
import pulumi_cloudflare as cloudflare

from homelab_cloudflare.bot_management import BotManagement
from homelab_cloudflare.helpers import account_id, resource_opts

_BOSSCHER_CH_ZONE_ID = "e32ce9cb10fafea8ee531b713afdcc10"
_BOSSSCHER_ORG_ZONE_ID = "981bc8749d817cd910da39e8a8aefd7f"
_LAURENSBOSSCHER_NL_ZONE_ID = "80109e07e6038846aa25d17367211948"

# Existing bosscher.ch cache rule. Kept so the import updates it in place.
_BOSSCHER_CH_CACHE_RULESET_ID = "fda2d59bb8fd4865abc96a6da66ad55f"
_BOSSCHER_CH_CACHE_RULE_ID = "94805434c1254400b0d192cd866c02ac"

# Executed by id with no pinned version, so emergency rules apply when
# Cloudflare publishes them. The catalog was present and the phase entrypoint was not.
_FREE_MANAGED_RULESET_ID = "77454fe2d30c4220b5701f6fdfb893ba"

# Request-phase cache rules can only see the URL, not the response
# Content-Type. Bypass every video/HLS/DASH extension so a cache rule cannot
# store video on the Free plan (Cloudflare ToS; not Cloudflare Stream).
_VIDEO_EXTENSIONS: tuple[str, ...] = (
    "3g2",
    "3gp",
    "asf",
    "avi",
    "divx",
    "f4v",
    "flv",
    "m2ts",
    "m2v",
    "m3u8",
    "m4s",
    "m4v",
    "mkv",
    "mov",
    "mp4",
    "mpd",
    "mpe",
    "mpeg",
    "mpg",
    "mts",
    "ogv",
    "qt",
    "rm",
    "rmvb",
    "ts",
    "vob",
    "webm",
    "wmv",
)

# Live bosscher.ch "cache default file extensions" list, minus avi/mkv/mp4/webm.
_STATIC_EXTENSIONS: tuple[str, ...] = (
    "7z",
    "avif",
    "apk",
    "bin",
    "bmp",
    "bz2",
    "class",
    "css",
    "csv",
    "doc",
    "docx",
    "dmg",
    "ejs",
    "eot",
    "eps",
    "exe",
    "flac",
    "gif",
    "gz",
    "ico",
    "iso",
    "jar",
    "jpg",
    "jpeg",
    "js",
    "mid",
    "midi",
    "mp3",
    "ogg",
    "otf",
    "pdf",
    "pict",
    "pls",
    "png",
    "ppt",
    "pptx",
    "ps",
    "rar",
    "svg",
    "svgz",
    "swf",
    "tar",
    "tif",
    "tiff",
    "ttf",
    "webp",
    "woff",
    "woff2",
    "xls",
    "xlsx",
    "zip",
    "zst",
)


def _extension_in(extensions: tuple[str, ...]) -> str:
    quoted = " ".join(f'"{ext}"' for ext in extensions)
    return f"(http.request.uri.path.extension in {{{quoted}}})"


@dataclass(frozen=True, slots=True)
class Zones:
    by_name: dict[str, cloudflare.Zone]
    settings: dict[str, dict[str, cloudflare.ZoneSetting]]
    dnssec: dict[str, cloudflare.ZoneDnssec]
    precursors: dict[str, cloudflare.Precursor]
    bot_management: dict[str, BotManagement]
    tiered_cache: dict[str, cloudflare.TieredCache]
    cache_rulesets: dict[str, cloudflare.Ruleset]
    waf_rulesets: dict[str, cloudflare.Ruleset]


def _zone_setting(
    *,
    slug: str,
    zone_id: pulumi.Input[str],
    import_zone_id: str,
    setting_id: str,
    value: str,
) -> cloudflare.ZoneSetting:
    return cloudflare.ZoneSetting(
        f"zone-setting-{slug}-{setting_id.replace('_', '-')}",
        zone_id=zone_id,
        setting_id=setting_id,
        value=value,
        opts=resource_opts(import_id=f"{import_zone_id}/{setting_id}"),
    )


def _cache_rules(*, keep_rule_ref: str | None) -> list[cloudflare.RulesetRuleArgs]:
    # First match wins. Video bypass stays above the static-extension cache.
    # `id` is read-only on ruleset rules; the provider tracks them by `ref`.
    bypass = cloudflare.RulesetRuleArgs(
        action="set_cache_settings",
        expression=_extension_in(_VIDEO_EXTENSIONS),
        description="Do not cache video (Cloudflare ToS)",
        enabled=True,
        action_parameters=cloudflare.RulesetRuleActionParametersArgs(cache=False),
    )
    if keep_rule_ref is None:
        cache_static = cloudflare.RulesetRuleArgs(
            action="set_cache_settings",
            expression=_extension_in(_STATIC_EXTENSIONS),
            description="Cache static file extensions except video",
            enabled=True,
            action_parameters=cloudflare.RulesetRuleActionParametersArgs(cache=True),
        )
    else:
        cache_static = cloudflare.RulesetRuleArgs(
            ref=keep_rule_ref,
            action="set_cache_settings",
            expression=_extension_in(_STATIC_EXTENSIONS),
            description="Cache static file extensions except video",
            enabled=True,
            action_parameters=cloudflare.RulesetRuleActionParametersArgs(cache=True),
        )
    return [bypass, cache_static]


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

    # Do not manage security_header: nested dynamic `value` panics provider Read.
    # ssl stays at the live mode. strict breaks www (cert is not valid for www)
    # and direct.laurensbosscher.nl (origin port 443 is closed).
    settings: dict[str, dict[str, cloudflare.ZoneSetting]] = {
        "bosscher.ch": {
            "min_tls_version": _zone_setting(
                slug="bosscher-ch",
                zone_id=by_name["bosscher.ch"].id,
                import_zone_id=_BOSSCHER_CH_ZONE_ID,
                setting_id="min_tls_version",
                value="1.2",
            ),
            "ssl": _zone_setting(
                slug="bosscher-ch",
                zone_id=by_name["bosscher.ch"].id,
                import_zone_id=_BOSSCHER_CH_ZONE_ID,
                setting_id="ssl",
                value="full",
            ),
            "always_use_https": _zone_setting(
                slug="bosscher-ch",
                zone_id=by_name["bosscher.ch"].id,
                import_zone_id=_BOSSCHER_CH_ZONE_ID,
                setting_id="always_use_https",
                value="on",
            ),
            "rocket_loader": _zone_setting(
                slug="bosscher-ch",
                zone_id=by_name["bosscher.ch"].id,
                import_zone_id=_BOSSCHER_CH_ZONE_ID,
                setting_id="rocket_loader",
                value="off",
            ),
        },
        "bossscher.org": {
            "min_tls_version": _zone_setting(
                slug="bossscher-org",
                zone_id=by_name["bossscher.org"].id,
                import_zone_id=_BOSSSCHER_ORG_ZONE_ID,
                setting_id="min_tls_version",
                value="1.2",
            ),
            "ssl": _zone_setting(
                slug="bossscher-org",
                zone_id=by_name["bossscher.org"].id,
                import_zone_id=_BOSSSCHER_ORG_ZONE_ID,
                setting_id="ssl",
                value="full",
            ),
            "always_use_https": _zone_setting(
                slug="bossscher-org",
                zone_id=by_name["bossscher.org"].id,
                import_zone_id=_BOSSSCHER_ORG_ZONE_ID,
                setting_id="always_use_https",
                value="on",
            ),
            "rocket_loader": _zone_setting(
                slug="bossscher-org",
                zone_id=by_name["bossscher.org"].id,
                import_zone_id=_BOSSSCHER_ORG_ZONE_ID,
                setting_id="rocket_loader",
                value="off",
            ),
        },
        "laurensbosscher.nl": {
            "min_tls_version": _zone_setting(
                slug="laurensbosscher-nl",
                zone_id=by_name["laurensbosscher.nl"].id,
                import_zone_id=_LAURENSBOSSCHER_NL_ZONE_ID,
                setting_id="min_tls_version",
                value="1.2",
            ),
            "ssl": _zone_setting(
                slug="laurensbosscher-nl",
                zone_id=by_name["laurensbosscher.nl"].id,
                import_zone_id=_LAURENSBOSSCHER_NL_ZONE_ID,
                setting_id="ssl",
                value="flexible",
            ),
            "always_use_https": _zone_setting(
                slug="laurensbosscher-nl",
                zone_id=by_name["laurensbosscher.nl"].id,
                import_zone_id=_LAURENSBOSSCHER_NL_ZONE_ID,
                setting_id="always_use_https",
                value="on",
            ),
            "rocket_loader": _zone_setting(
                slug="laurensbosscher-nl",
                zone_id=by_name["laurensbosscher.nl"].id,
                import_zone_id=_LAURENSBOSSCHER_NL_ZONE_ID,
                setting_id="rocket_loader",
                value="off",
            ),
        },
    }

    # Signing is already on. bossscher.org and laurensbosscher.nl stay pending
    # until the registrar publishes the DS record; status=active is the enable
    # flag, and Cloudflare reports pending until that DS is seen.
    dnssec = {
        "bosscher.ch": cloudflare.ZoneDnssec(
            "zone-dnssec-bosscher-ch",
            zone_id=by_name["bosscher.ch"].id,
            status="active",
            opts=resource_opts(import_id=_BOSSCHER_CH_ZONE_ID),
        ),
        "bossscher.org": cloudflare.ZoneDnssec(
            "zone-dnssec-bossscher-org",
            zone_id=by_name["bossscher.org"].id,
            status="active",
            opts=resource_opts(import_id=_BOSSSCHER_ORG_ZONE_ID),
        ),
        "laurensbosscher.nl": cloudflare.ZoneDnssec(
            "zone-dnssec-laurensbosscher-nl",
            zone_id=by_name["laurensbosscher.nl"].id,
            status="active",
            opts=resource_opts(import_id=_LAURENSBOSSCHER_NL_ZONE_ID),
        ),
    }

    # default_mode is deprecated in the provider schema but still the only write
    # path. Omit empty enforcement_rules (that also warns).
    precursors = {
        "bosscher.ch": cloudflare.Precursor(
            "zone-precursor-bosscher-ch",
            zone_id=by_name["bosscher.ch"].id,
            default_mode="min-friction",
            opts=resource_opts(import_id=_BOSSCHER_CH_ZONE_ID),
        ),
        "bossscher.org": cloudflare.Precursor(
            "zone-precursor-bossscher-org",
            zone_id=by_name["bossscher.org"].id,
            default_mode="min-friction",
            opts=resource_opts(import_id=_BOSSSCHER_ORG_ZONE_ID),
        ),
        "laurensbosscher.nl": cloudflare.Precursor(
            "zone-precursor-laurensbosscher-nl",
            zone_id=by_name["laurensbosscher.nl"].id,
            default_mode="min-friction",
            opts=resource_opts(import_id=_LAURENSBOSSCHER_NL_ZONE_ID),
        ),
    }

    # Fight Mode stays off on the app/media zones: it challenges non-browser
    # clients and Free-plan Bot Fight Mode cannot be skipped per path.
    # laurensbosscher.nl is the public site, so Fight Mode is on there.
    # Fight Mode requires enable_js=True (API 10400).
    bot_management = {
        "bosscher.ch": BotManagement(
            "zone-bot-management-bosscher-ch",
            zone_id=by_name["bosscher.ch"].id,
            enable_js=False,
            fight_mode=False,
            ai_bots_protection="block",
            content_bots_protection="disabled",
            crawler_protection="disabled",
            is_robots_txt_managed=True,
            opts=resource_opts(),
        ),
        "bossscher.org": BotManagement(
            "zone-bot-management-bossscher-org",
            zone_id=by_name["bossscher.org"].id,
            enable_js=False,
            fight_mode=False,
            ai_bots_protection="block",
            content_bots_protection="disabled",
            crawler_protection="disabled",
            is_robots_txt_managed=True,
            opts=resource_opts(),
        ),
        "laurensbosscher.nl": BotManagement(
            "zone-bot-management-laurensbosscher-nl",
            zone_id=by_name["laurensbosscher.nl"].id,
            enable_js=True,
            fight_mode=True,
            ai_bots_protection="block",
            content_bots_protection="disabled",
            crawler_protection="disabled",
            is_robots_txt_managed=True,
            opts=resource_opts(),
        ),
    }

    # Smart Tiered Cache is free (not Argo Smart Routing).
    tiered_cache = {
        "bosscher.ch": cloudflare.TieredCache(
            "zone-tiered-cache-bosscher-ch",
            zone_id=by_name["bosscher.ch"].id,
            value="on",
            opts=resource_opts(import_id=_BOSSCHER_CH_ZONE_ID),
        ),
        "bossscher.org": cloudflare.TieredCache(
            "zone-tiered-cache-bossscher-org",
            zone_id=by_name["bossscher.org"].id,
            value="on",
            opts=resource_opts(import_id=_BOSSSCHER_ORG_ZONE_ID),
        ),
        "laurensbosscher.nl": cloudflare.TieredCache(
            "zone-tiered-cache-laurensbosscher-nl",
            zone_id=by_name["laurensbosscher.nl"].id,
            value="on",
            opts=resource_opts(import_id=_LAURENSBOSSCHER_NL_ZONE_ID),
        ),
    }

    cache_rulesets = {
        "bosscher.ch": cloudflare.Ruleset(
            "zone-cache-ruleset-bosscher-ch",
            zone_id=by_name["bosscher.ch"].id,
            name="default",
            kind="zone",
            phase="http_request_cache_settings",
            rules=_cache_rules(keep_rule_ref=_BOSSCHER_CH_CACHE_RULE_ID),
            opts=resource_opts(
                import_id=f"zones/{_BOSSCHER_CH_ZONE_ID}/{_BOSSCHER_CH_CACHE_RULESET_ID}",
            ),
        ),
        "bossscher.org": cloudflare.Ruleset(
            "zone-cache-ruleset-bossscher-org",
            zone_id=by_name["bossscher.org"].id,
            name="default",
            kind="zone",
            phase="http_request_cache_settings",
            rules=_cache_rules(keep_rule_ref=None),
            opts=resource_opts(),
        ),
        "laurensbosscher.nl": cloudflare.Ruleset(
            "zone-cache-ruleset-laurensbosscher-nl",
            zone_id=by_name["laurensbosscher.nl"].id,
            name="default",
            kind="zone",
            phase="http_request_cache_settings",
            rules=_cache_rules(keep_rule_ref=None),
            opts=resource_opts(),
        ),
    }

    pulumi.export("zone_names", list(by_name))
    pulumi.export("zone_setting_count", sum(len(per_zone) for per_zone in settings.values()))
    pulumi.export("zone_dnssec_count", len(dnssec))
    pulumi.export("zone_precursor_count", len(precursors))
    pulumi.export("zone_bot_management_count", len(bot_management))
    pulumi.export("zone_tiered_cache_count", len(tiered_cache))
    # Same ruleset on every zone. No per-path skip: the rules are CVE
    # signatures, and playback URLs do not resemble them.
    waf_rulesets = {
        name: cloudflare.Ruleset(
            f"zone-waf-ruleset-{name.replace('.', '-')}",
            zone_id=zone.id,
            name="default",
            description="Cloudflare Free Managed Ruleset",
            kind="zone",
            phase="http_request_firewall_managed",
            rules=[
                cloudflare.RulesetRuleArgs(
                    action="execute",
                    expression="true",
                    description="Cloudflare Free Managed Ruleset",
                    enabled=True,
                    action_parameters=cloudflare.RulesetRuleActionParametersArgs(
                        id=_FREE_MANAGED_RULESET_ID,
                    ),
                )
            ],
            opts=resource_opts(),
        )
        for name, zone in by_name.items()
    }

    pulumi.export("zone_cache_ruleset_count", len(cache_rulesets))
    pulumi.export("zone_waf_ruleset_count", len(waf_rulesets))
    return Zones(
        by_name=by_name,
        settings=settings,
        dnssec=dnssec,
        precursors=precursors,
        bot_management=bot_management,
        tiered_cache=tiered_cache,
        cache_rulesets=cache_rulesets,
        waf_rulesets=waf_rulesets,
    )

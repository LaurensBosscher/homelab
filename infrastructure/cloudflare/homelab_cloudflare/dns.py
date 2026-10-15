from __future__ import annotations

from dataclasses import dataclass

import pulumi
import pulumi_cloudflare as cloudflare

from homelab_cloudflare.helpers import CLOUDFLARE_AUTO, resource_opts


@dataclass(frozen=True, slots=True)
class DnsRecords:
    by_logical_name: dict[str, cloudflare.DnsRecord]


def create_dns_records(*, zone_ids: dict[str, pulumi.Input[str]]) -> DnsRecords:
    by_logical: dict[str, cloudflare.DnsRecord] = {}
    by_logical["dns-bosscher-ch-a-bosscher-ch-c2770f07"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-a-bosscher-ch-c2770f07",
        zone_id=zone_ids["bosscher.ch"],
        name="bosscher.ch",
        type="A",
        ttl=CLOUDFLARE_AUTO,
        content="75.2.60.5",
        proxied=True,
        comment="Netifly host",
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/c2770f07e6071a878ff92c7e563d78ea",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-a-www-bosscher-ch-ae796cc2"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-a-www-bosscher-ch-ae796cc2",
        zone_id=zone_ids["bosscher.ch"],
        name="www.bosscher.ch",
        type="A",
        ttl=CLOUDFLARE_AUTO,
        content="75.2.60.5",
        proxied=True,
        comment="Netifly host",
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/ae796cc21c4023d19d97d8e9f0267c86",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-aiostreams-bosscher-ch-eb48eed3"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-aiostreams-bosscher-ch-eb48eed3",
        zone_id=zone_ids["bosscher.ch"],
        name="aiostreams.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/eb48eed3879e680392762e892eca77f0",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-alertmanager-bosscher-ch-38eaba60"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-alertmanager-bosscher-ch-38eaba60",
        zone_id=zone_ids["bosscher.ch"],
        name="alertmanager.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/38eaba6082e21d571b2a9d07020149db",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-argocd-bosscher-ch-888f3136"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-argocd-bosscher-ch-888f3136",
        zone_id=zone_ids["bosscher.ch"],
        name="argocd.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/888f313651ff96520a4ac3c1374d35cd",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-audiobookshelf-bosscher-ch-8bab70f2"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-audiobookshelf-bosscher-ch-8bab70f2",
        zone_id=zone_ids["bosscher.ch"],
        name="audiobookshelf.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/8bab70f263fcaf5955a843cc793500af",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-bentopdf-bosscher-ch-2382c1de"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-bentopdf-bosscher-ch-2382c1de",
        zone_id=zone_ids["bosscher.ch"],
        name="bentopdf.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/2382c1de9270cc38958415e69f8467d5",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-beszel-bosscher-ch-d70483af"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-beszel-bosscher-ch-d70483af",
        zone_id=zone_ids["bosscher.ch"],
        name="beszel.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/d70483afd4771136faf96d32aecd01d8",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-beszel-openstick-bosscher-ch-cd48de0b"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-beszel-openstick-bosscher-ch-cd48de0b",
        zone_id=zone_ids["bosscher.ch"],
        name="beszel_openstick.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="9ec2e211-3f7b-4664-b720-29d02010af13.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/cd48de0bfd93b027fe5588f0b4db4c07",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-bookshelf-bosscher-ch-4becfdeb"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-bookshelf-bosscher-ch-4becfdeb",
        zone_id=zone_ids["bosscher.ch"],
        name="bookshelf.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/4becfdeb9e5e738e3e123bbe6051ecbd",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-calibre-web-bosscher-ch-f64aa11d"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-calibre-web-bosscher-ch-f64aa11d",
        zone_id=zone_ids["bosscher.ch"],
        name="calibre-web.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/f64aa11d4a95bf7e3765ce6c3481f412",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-dozzle-openstick-bosscher-ch-ef0ba1da"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-dozzle-openstick-bosscher-ch-ef0ba1da",
        zone_id=zone_ids["bosscher.ch"],
        name="dozzle_openstick.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="9ec2e211-3f7b-4664-b720-29d02010af13.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/ef0ba1dabdb38b05320fd1055e3b83f6",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-fusion-bosscher-ch-2e31b4e1"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-fusion-bosscher-ch-2e31b4e1",
        zone_id=zone_ids["bosscher.ch"],
        name="fusion.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/2e31b4e177490c28384aefac8e67a685",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-fusion-openstick-bosscher-ch-ac6d272c"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-fusion-openstick-bosscher-ch-ac6d272c",
        zone_id=zone_ids["bosscher.ch"],
        name="fusion_openstick.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="9ec2e211-3f7b-4664-b720-29d02010af13.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/ac6d272c3468d55bba7361641ebc0cbd",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-gatus-bosscher-ch-3411fc95"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-gatus-bosscher-ch-3411fc95",
        zone_id=zone_ids["bosscher.ch"],
        name="gatus.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/3411fc95d09a84831dbe0d416c8e3cea",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-gatus-openstick-bosscher-ch-fb3ee5a9"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-gatus-openstick-bosscher-ch-fb3ee5a9",
        zone_id=zone_ids["bosscher.ch"],
        name="gatus_openstick.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="9ec2e211-3f7b-4664-b720-29d02010af13.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/fb3ee5a9a4d202c9ac92fc92521ae34d",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-grafana-bosscher-ch-21f92fbc"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-grafana-bosscher-ch-21f92fbc",
        zone_id=zone_ids["bosscher.ch"],
        name="grafana.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/21f92fbce4210ce3353be4e78fd3d156",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-home-bosscher-ch-94998f9e"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-home-bosscher-ch-94998f9e",
        zone_id=zone_ids["bosscher.ch"],
        name="home.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/94998f9eeb00fe53ddadaf084e44c573",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-it-tools-bosscher-ch-ddaee577"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-it-tools-bosscher-ch-ddaee577",
        zone_id=zone_ids["bosscher.ch"],
        name="it-tools.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/ddaee577caaf398e96902ceb9c5da0cf",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-kite-bosscher-ch-46fc0d97"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-kite-bosscher-ch-46fc0d97",
        zone_id=zone_ids["bosscher.ch"],
        name="kite.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/46fc0d975f9e082255636eca9af24d45",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-linkwarden-bosscher-ch-8b46a63f"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-linkwarden-bosscher-ch-8b46a63f",
        zone_id=zone_ids["bosscher.ch"],
        name="linkwarden.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/8b46a63fc7a9fd1cf8d6c954d1c7776e",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-listenarr-bosscher-ch-248bd7fc"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-listenarr-bosscher-ch-248bd7fc",
        zone_id=zone_ids["bosscher.ch"],
        name="listenarr.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/248bd7fc3f6405e8ee930ac8f0944dea",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-mydia-bosscher-ch-bd076901"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-mydia-bosscher-ch-bd076901",
        zone_id=zone_ids["bosscher.ch"],
        name="mydia.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/bd07690104dc2a5019b5cf3118c4a47b",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-nanobot-bosscher-ch-4b5fc1a6"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-nanobot-bosscher-ch-4b5fc1a6",
        zone_id=zone_ids["bosscher.ch"],
        name="nanobot.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/4b5fc1a6b56dd6e5b6aaf519ee9ad34d",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-norish-bosscher-ch-867a0bc3"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-norish-bosscher-ch-867a0bc3",
        zone_id=zone_ids["bosscher.ch"],
        name="norish.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/867a0bc340f8eaf7ba313799791d3cd7",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-obsidian-live-sync-bosscher-ch-4155feb9"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-obsidian-live-sync-bosscher-ch-4155feb9",
        zone_id=zone_ids["bosscher.ch"],
        name="obsidian-live-sync.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/4155feb9aa1fd17b9f6c0a5814de1e7f",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-openclaw-bosscher-ch-2c95f2a8"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-openclaw-bosscher-ch-2c95f2a8",
        zone_id=zone_ids["bosscher.ch"],
        name="openclaw.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/2c95f2a85037d1310e91cc23e7b578c9",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-opencode-bosscher-ch-4b471de9"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-opencode-bosscher-ch-4b471de9",
        zone_id=zone_ids["bosscher.ch"],
        name="opencode.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/4b471de9afdb807e5564cdb4c9b255ba",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-pico-openstick-bosscher-ch-713efae2"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-pico-openstick-bosscher-ch-713efae2",
        zone_id=zone_ids["bosscher.ch"],
        name="pico_openstick.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="9ec2e211-3f7b-4664-b720-29d02010af13.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/713efae2275f8cd01c9230e50ac86c27",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-playarr-bosscher-ch-c3500f3a"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-playarr-bosscher-ch-c3500f3a",
        zone_id=zone_ids["bosscher.ch"],
        name="playarr.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/c3500f3a0f9973bd2b8724e32f0badb1",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-prometheus-bosscher-ch-504f9a54"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-prometheus-bosscher-ch-504f9a54",
        zone_id=zone_ids["bosscher.ch"],
        name="prometheus.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/504f9a544f3e308f769eea785ddfafaa",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-prowlarr-bosscher-ch-e739992a"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-prowlarr-bosscher-ch-e739992a",
        zone_id=zone_ids["bosscher.ch"],
        name="prowlarr.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/e739992a6bb7f5c0f5826266dbb9b03e",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-qbittorrent-bosscher-ch-47377d22"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-qbittorrent-bosscher-ch-47377d22",
        zone_id=zone_ids["bosscher.ch"],
        name="qbittorrent.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/47377d2255f6e86ced38139db7270a4b",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-questarr-bosscher-ch-2376cff4"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-questarr-bosscher-ch-2376cff4",
        zone_id=zone_ids["bosscher.ch"],
        name="questarr.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/2376cff41c388fe308ff18dc2a25023f",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-radarr-bosscher-ch-b84b762f"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-radarr-bosscher-ch-b84b762f",
        zone_id=zone_ids["bosscher.ch"],
        name="radarr.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/b84b762f52a0c33f7476c40f0ad03318",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-rdt-client-bosscher-ch-59fd764a"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-rdt-client-bosscher-ch-59fd764a",
        zone_id=zone_ids["bosscher.ch"],
        name="rdt-client.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/59fd764a1e153c0c623d08b1e3c932b5",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-redlib-bosscher-ch-80f36bad"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-redlib-bosscher-ch-80f36bad",
        zone_id=zone_ids["bosscher.ch"],
        name="redlib.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/80f36bade1d2601ec53f3c21d426c851",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-sabnzbd-bosscher-ch-983d1a9b"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-sabnzbd-bosscher-ch-983d1a9b",
        zone_id=zone_ids["bosscher.ch"],
        name="sabnzbd.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/983d1a9b9eb4dfd5a416a4f825d7f385",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-shelfarr-bosscher-ch-29e0e792"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-shelfarr-bosscher-ch-29e0e792",
        zone_id=zone_ids["bosscher.ch"],
        name="shelfarr.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/29e0e79206021ef2eb022d9830b47250",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-shiori-bosscher-ch-00e3c116"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-shiori-bosscher-ch-00e3c116",
        zone_id=zone_ids["bosscher.ch"],
        name="shiori.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/00e3c1167dcb2915f01df282154b371a",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-sonarr-bosscher-ch-ec25b0e9"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-sonarr-bosscher-ch-ec25b0e9",
        zone_id=zone_ids["bosscher.ch"],
        name="sonarr.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/ec25b0e953e05709de0fb4a9eb8de33d",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-ssh-openstick-bosscher-ch-940a7fdc"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-ssh-openstick-bosscher-ch-940a7fdc",
        zone_id=zone_ids["bosscher.ch"],
        name="ssh_openstick.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="9ec2e211-3f7b-4664-b720-29d02010af13.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/940a7fdcd80c2cf15e9d30130f9c85ad",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-stacks-bosscher-ch-4ca301ad"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-stacks-bosscher-ch-4ca301ad",
        zone_id=zone_ids["bosscher.ch"],
        name="stacks.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/4ca301addc5464f571efd398f964511a",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-stremio-bosscher-ch-b681ae9a"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-stremio-bosscher-ch-b681ae9a",
        zone_id=zone_ids["bosscher.ch"],
        name="stremio.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/b681ae9a6d665b12f56e9ea5d72cdb2b",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-termix-bosscher-ch-c19f11c9"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-termix-bosscher-ch-c19f11c9",
        zone_id=zone_ids["bosscher.ch"],
        name="termix.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/c19f11c9f9a86a6db1fa494426da8078",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-wanderer-bosscher-ch-e3ca1c4a"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-wanderer-bosscher-ch-e3ca1c4a",
        zone_id=zone_ids["bosscher.ch"],
        name="wanderer.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/e3ca1c4a04fde8239bef2353e26a6ebc",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-your-spotify-api-bosscher-ch-3ef70019"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-your-spotify-api-bosscher-ch-3ef70019",
        zone_id=zone_ids["bosscher.ch"],
        name="your-spotify-api.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/3ef70019570294f15f02e85610633d3b",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-cname-your-spotify-bosscher-ch-6167bedb"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-cname-your-spotify-bosscher-ch-6167bedb",
        zone_id=zone_ids["bosscher.ch"],
        name="your-spotify.bosscher.ch",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="74c090cd-5046-4cb3-9b9f-43f013822d1c.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/6167bedbaeff537c9769c2f717672f6a",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-mx-bosscher-ch-e97d72e8"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-mx-bosscher-ch-e97d72e8",
        zone_id=zone_ids["bosscher.ch"],
        name="bosscher.ch",
        type="MX",
        ttl=3600.0,
        content="alt3.aspmx.l.google.com",
        priority=10,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/e97d72e8fba452fdc2183b918dd2b73e",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-mx-bosscher-ch-547286b8"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-mx-bosscher-ch-547286b8",
        zone_id=zone_ids["bosscher.ch"],
        name="bosscher.ch",
        type="MX",
        ttl=3600.0,
        content="aspmx.l.google.com",
        priority=1,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/547286b8a832ee27f3c512a63dee4b7f",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-mx-bosscher-ch-82770cb0"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-mx-bosscher-ch-82770cb0",
        zone_id=zone_ids["bosscher.ch"],
        name="bosscher.ch",
        type="MX",
        ttl=3600.0,
        content="alt2.aspmx.l.google.com",
        priority=5,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/82770cb0c1c08c75f14e2a4b03422479",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-mx-bosscher-ch-47609206"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-mx-bosscher-ch-47609206",
        zone_id=zone_ids["bosscher.ch"],
        name="bosscher.ch",
        type="MX",
        ttl=3600.0,
        content="alt1.aspmx.l.google.com",
        priority=5,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/47609206a15a8a29b70bcaef5f1fdef8",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-mx-bosscher-ch-212b3170"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-mx-bosscher-ch-212b3170",
        zone_id=zone_ids["bosscher.ch"],
        name="bosscher.ch",
        type="MX",
        ttl=3600.0,
        content="alt4.aspmx.l.google.com",
        priority=10,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/212b3170827f67301c62feb80c064f42",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-txt-bosscher-ch-1a182776"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-txt-bosscher-ch-1a182776",
        zone_id=zone_ids["bosscher.ch"],
        name="bosscher.ch",
        type="TXT",
        ttl=3600.0,
        content="\"v=spf1 include:_spf.google.com -all\"",
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/1a18277637671e2f2d95f8a23166e685",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-txt-bosscher-ch-dad94f5e"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-txt-bosscher-ch-dad94f5e",
        zone_id=zone_ids["bosscher.ch"],
        name="bosscher.ch",
        type="TXT",
        ttl=3600.0,
        content="\"google-site-verification=IazzZBMjPprsjeE9Pv16bX7z0FXmVFjj0Lw9RQ7eP0A\"",
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/dad94f5e9cb9595a48c0b85e2ce2957d",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-txt-dmarc-bosscher-ch-bb26c997"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-txt-dmarc-bosscher-ch-bb26c997",
        zone_id=zone_ids["bosscher.ch"],
        name="_dmarc.bosscher.ch",
        type="TXT",
        ttl=CLOUDFLARE_AUTO,
        content="\"v=DMARC1; p=reject; adkim=s; aspf=s; pct=100\"",
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/bb26c997373ed0cf160cffe0ce8cf589",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-txt-google-domainkey-bosscher-ch-10dc05ea"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-txt-google-domainkey-bosscher-ch-10dc05ea",
        zone_id=zone_ids["bosscher.ch"],
        name="google._domainkey.bosscher.ch",
        type="TXT",
        ttl=CLOUDFLARE_AUTO,
        content="\"v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDBtbbVYxKj9ItpoiTeA2RfyJaRyo1UayyfKG3zkPe8xM8U120d+JYA5Oid8wsnG7H5e/pwzq4OcJqvAn/kIsIeP9InrQevX08jnNmziXoLNcQAv0F7jrnaucXXNExMVknhayvhPiRscrDr+Q2cYSmBnbXRLmclpuzB4fwsTzsPGwIDAQAB\"",
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/10dc05eafbe3d5ce5296863f839eafec",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-aaaa-bookmarks-bosscher-ch-48751173"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-aaaa-bookmarks-bosscher-ch-48751173",
        zone_id=zone_ids["bosscher.ch"],
        name="bookmarks.bosscher.ch",
        type="AAAA",
        ttl=CLOUDFLARE_AUTO,
        content="100::",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/4875117322f34f123f24a97935a9ddc4",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-aaaa-collection-bosscher-ch-d10419c8"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-aaaa-collection-bosscher-ch-d10419c8",
        zone_id=zone_ids["bosscher.ch"],
        name="collection.bosscher.ch",
        type="AAAA",
        ttl=CLOUDFLARE_AUTO,
        content="100::",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/d10419c885960d8b5dba1c8ff582fdc5",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-aaaa-hikes-bosscher-ch-4ab299ae"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-aaaa-hikes-bosscher-ch-4ab299ae",
        zone_id=zone_ids["bosscher.ch"],
        name="hikes.bosscher.ch",
        type="AAAA",
        ttl=CLOUDFLARE_AUTO,
        content="100::",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/4ab299ae2c9151232b40842d42eb8d73",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-aaaa-portfolio-bosscher-ch-0b3f12b5"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-aaaa-portfolio-bosscher-ch-0b3f12b5",
        zone_id=zone_ids["bosscher.ch"],
        name="portfolio.bosscher.ch",
        type="AAAA",
        ttl=CLOUDFLARE_AUTO,
        content="100::",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/0b3f12b5b41317bba4b34b00790e8386",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bosscher-ch-aaaa-weekend-bosscher-ch-71c489dd"] = cloudflare.DnsRecord(
        "dns-bosscher-ch-aaaa-weekend-bosscher-ch-71c489dd",
        zone_id=zone_ids["bosscher.ch"],
        name="weekend.bosscher.ch",
        type="AAAA",
        ttl=CLOUDFLARE_AUTO,
        content="100::",
        proxied=True,
        opts=resource_opts(
            import_id="e32ce9cb10fafea8ee531b713afdcc10/71c489ddbde81441e4fa8c4e74e59cee",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bossscher-org-cname-aiostreams-bossscher-org-de14b67e"] = cloudflare.DnsRecord(
        "dns-bossscher-org-cname-aiostreams-bossscher-org-de14b67e",
        zone_id=zone_ids["bossscher.org"],
        name="aiostreams.bossscher.org",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="5e317939-f1e9-46e1-83c9-50f3d44d38b5.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="981bc8749d817cd910da39e8a8aefd7f/de14b67e91588c683ab05681707fa851",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bossscher-org-cname-audiobooks-bossscher-org-4d22e97e"] = cloudflare.DnsRecord(
        "dns-bossscher-org-cname-audiobooks-bossscher-org-4d22e97e",
        zone_id=zone_ids["bossscher.org"],
        name="audiobooks.bossscher.org",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="5e317939-f1e9-46e1-83c9-50f3d44d38b5.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="981bc8749d817cd910da39e8a8aefd7f/4d22e97ed5b26abf2a0e7c30fa64d4b6",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bossscher-org-cname-books-bossscher-org-ab833eb7"] = cloudflare.DnsRecord(
        "dns-bossscher-org-cname-books-bossscher-org-ab833eb7",
        zone_id=zone_ids["bossscher.org"],
        name="books.bossscher.org",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="5e317939-f1e9-46e1-83c9-50f3d44d38b5.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="981bc8749d817cd910da39e8a8aefd7f/ab833eb725bc981d53646a8b0ea75ffa",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bossscher-org-cname-books-download-bossscher-org-cbe4ec15"] = cloudflare.DnsRecord(
        "dns-bossscher-org-cname-books-download-bossscher-org-cbe4ec15",
        zone_id=zone_ids["bossscher.org"],
        name="books-download.bossscher.org",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="5e317939-f1e9-46e1-83c9-50f3d44d38b5.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="981bc8749d817cd910da39e8a8aefd7f/cbe4ec1500f89e517f901ba9ffef3910",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bossscher-org-cname-cockpit-bossscher-org-c3662a72"] = cloudflare.DnsRecord(
        "dns-bossscher-org-cname-cockpit-bossscher-org-c3662a72",
        zone_id=zone_ids["bossscher.org"],
        name="cockpit.bossscher.org",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="5e317939-f1e9-46e1-83c9-50f3d44d38b5.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="981bc8749d817cd910da39e8a8aefd7f/c3662a729ca799a054ee6e26112b3d01",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bossscher-org-cname-hello-bossscher-org-fad4b621"] = cloudflare.DnsRecord(
        "dns-bossscher-org-cname-hello-bossscher-org-fad4b621",
        zone_id=zone_ids["bossscher.org"],
        name="hello.bossscher.org",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="407b9d24-e5f7-4aa8-8f5a-ad32566cda8a.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="981bc8749d817cd910da39e8a8aefd7f/fad4b6214d4c38fd735de77579d11e73",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bossscher-org-cname-rss-bossscher-org-25616342"] = cloudflare.DnsRecord(
        "dns-bossscher-org-cname-rss-bossscher-org-25616342",
        zone_id=zone_ids["bossscher.org"],
        name="rss.bossscher.org",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="5e317939-f1e9-46e1-83c9-50f3d44d38b5.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="981bc8749d817cd910da39e8a8aefd7f/256163423362adcce029a39b149a0848",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bossscher-org-cname-sabnzbd-bossscher-org-730575d7"] = cloudflare.DnsRecord(
        "dns-bossscher-org-cname-sabnzbd-bossscher-org-730575d7",
        zone_id=zone_ids["bossscher.org"],
        name="sabnzbd.bossscher.org",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="5e317939-f1e9-46e1-83c9-50f3d44d38b5.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="981bc8749d817cd910da39e8a8aefd7f/730575d727f78f198ffc351a4446b07e",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bossscher-org-cname-ssh-bossscher-org-015411fd"] = cloudflare.DnsRecord(
        "dns-bossscher-org-cname-ssh-bossscher-org-015411fd",
        zone_id=zone_ids["bossscher.org"],
        name="ssh.bossscher.org",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="5e317939-f1e9-46e1-83c9-50f3d44d38b5.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="981bc8749d817cd910da39e8a8aefd7f/015411fdaf13741e5471f609d4a96713",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bossscher-org-cname-stremio-bossscher-org-9c66e105"] = cloudflare.DnsRecord(
        "dns-bossscher-org-cname-stremio-bossscher-org-9c66e105",
        zone_id=zone_ids["bossscher.org"],
        name="stremio.bossscher.org",
        type="CNAME",
        ttl=CLOUDFLARE_AUTO,
        content="5e317939-f1e9-46e1-83c9-50f3d44d38b5.cfargotunnel.com",
        proxied=True,
        opts=resource_opts(
            import_id="981bc8749d817cd910da39e8a8aefd7f/9c66e1058e513154cc6ed41b1b7f455d",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-bossscher-org-txt-dmarc-bossscher-org-cfb7832b"] = cloudflare.DnsRecord(
        "dns-bossscher-org-txt-dmarc-bossscher-org-cfb7832b",
        zone_id=zone_ids["bossscher.org"],
        name="_dmarc.bossscher.org",
        type="TXT",
        ttl=CLOUDFLARE_AUTO,
        content="\"v=DMARC1; p=none; rua=mailto:928143443818428bb46414882444e51d@dmarc-reports.cloudflare.net\"",
        opts=resource_opts(
            import_id="981bc8749d817cd910da39e8a8aefd7f/cfb7832b471c31cc911490aca76c401f",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-laurensbosscher-nl-a-direct-laurensbosscher-nl-491104b4"] = cloudflare.DnsRecord(
        "dns-laurensbosscher-nl-a-direct-laurensbosscher-nl-491104b4",
        zone_id=zone_ids["laurensbosscher.nl"],
        name="direct.laurensbosscher.nl",
        type="A",
        ttl=CLOUDFLARE_AUTO,
        content="198.23.133.157",
        proxied=True,
        opts=resource_opts(
            import_id="80109e07e6038846aa25d17367211948/491104b44d496505b5774256373855c9",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-laurensbosscher-nl-a-star-laurensbosscher-nl-898bd583"] = cloudflare.DnsRecord(
        "dns-laurensbosscher-nl-a-star-laurensbosscher-nl-898bd583",
        zone_id=zone_ids["laurensbosscher.nl"],
        name="*.laurensbosscher.nl",
        type="A",
        ttl=CLOUDFLARE_AUTO,
        content="198.23.133.157",
        proxied=True,
        opts=resource_opts(
            import_id="80109e07e6038846aa25d17367211948/898bd583a712696ddab09021283dfe05",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-laurensbosscher-nl-a-laurensbosscher-nl-e02c392e"] = cloudflare.DnsRecord(
        "dns-laurensbosscher-nl-a-laurensbosscher-nl-e02c392e",
        zone_id=zone_ids["laurensbosscher.nl"],
        name="laurensbosscher.nl",
        type="A",
        ttl=CLOUDFLARE_AUTO,
        content="75.2.60.5",
        proxied=True,
        opts=resource_opts(
            import_id="80109e07e6038846aa25d17367211948/e02c392e6182e9130962b19670dbf877",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-laurensbosscher-nl-a-www-laurensbosscher-nl-b450e8e7"] = cloudflare.DnsRecord(
        "dns-laurensbosscher-nl-a-www-laurensbosscher-nl-b450e8e7",
        zone_id=zone_ids["laurensbosscher.nl"],
        name="www.laurensbosscher.nl",
        type="A",
        ttl=CLOUDFLARE_AUTO,
        content="75.2.60.5",
        proxied=True,
        opts=resource_opts(
            import_id="80109e07e6038846aa25d17367211948/b450e8e7c902e8c91d99bb2c1c15eb9c",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-laurensbosscher-nl-mx-laurensbosscher-nl-7a467b7c"] = cloudflare.DnsRecord(
        "dns-laurensbosscher-nl-mx-laurensbosscher-nl-7a467b7c",
        zone_id=zone_ids["laurensbosscher.nl"],
        name="laurensbosscher.nl",
        type="MX",
        ttl=CLOUDFLARE_AUTO,
        content="aspmx3.googlemail.com",
        priority=10,
        opts=resource_opts(
            import_id="80109e07e6038846aa25d17367211948/7a467b7cae8d0ff17391cb9cf4b86eeb",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-laurensbosscher-nl-mx-laurensbosscher-nl-1758d655"] = cloudflare.DnsRecord(
        "dns-laurensbosscher-nl-mx-laurensbosscher-nl-1758d655",
        zone_id=zone_ids["laurensbosscher.nl"],
        name="laurensbosscher.nl",
        type="MX",
        ttl=CLOUDFLARE_AUTO,
        content="aspmx2.googlemail.com",
        priority=10,
        opts=resource_opts(
            import_id="80109e07e6038846aa25d17367211948/1758d655268afd0642269c86ff4834b3",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-laurensbosscher-nl-mx-laurensbosscher-nl-83de0cfc"] = cloudflare.DnsRecord(
        "dns-laurensbosscher-nl-mx-laurensbosscher-nl-83de0cfc",
        zone_id=zone_ids["laurensbosscher.nl"],
        name="laurensbosscher.nl",
        type="MX",
        ttl=CLOUDFLARE_AUTO,
        content="aspmx.l.google.com",
        priority=1,
        opts=resource_opts(
            import_id="80109e07e6038846aa25d17367211948/83de0cfc7c71a2116367ccde866b59e8",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-laurensbosscher-nl-mx-laurensbosscher-nl-dfb84fdf"] = cloudflare.DnsRecord(
        "dns-laurensbosscher-nl-mx-laurensbosscher-nl-dfb84fdf",
        zone_id=zone_ids["laurensbosscher.nl"],
        name="laurensbosscher.nl",
        type="MX",
        ttl=CLOUDFLARE_AUTO,
        content="alt2.aspmx.l.google.com",
        priority=5,
        opts=resource_opts(
            import_id="80109e07e6038846aa25d17367211948/dfb84fdf08ae22517eeca68e58bf5dbb",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-laurensbosscher-nl-mx-laurensbosscher-nl-87ffd52e"] = cloudflare.DnsRecord(
        "dns-laurensbosscher-nl-mx-laurensbosscher-nl-87ffd52e",
        zone_id=zone_ids["laurensbosscher.nl"],
        name="laurensbosscher.nl",
        type="MX",
        ttl=CLOUDFLARE_AUTO,
        content="alt1.aspmx.l.google.com",
        priority=5,
        opts=resource_opts(
            import_id="80109e07e6038846aa25d17367211948/87ffd52e09f3efd84aa6d01a77f87b9b",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-laurensbosscher-nl-txt-dmarc-laurensbosscher-nl-e20753b3"] = cloudflare.DnsRecord(
        "dns-laurensbosscher-nl-txt-dmarc-laurensbosscher-nl-e20753b3",
        zone_id=zone_ids["laurensbosscher.nl"],
        name="_dmarc.laurensbosscher.nl",
        type="TXT",
        ttl=CLOUDFLARE_AUTO,
        content="v=DMARC1; p=reject; adkim=s; aspf=s; pct=100",
        opts=resource_opts(
            import_id="80109e07e6038846aa25d17367211948/e20753b3d67d812937df0aa32733a757",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-laurensbosscher-nl-txt-google-domainkey-laurensbosscher-nl-4e94351d"] = cloudflare.DnsRecord(
        "dns-laurensbosscher-nl-txt-google-domainkey-laurensbosscher-nl-4e94351d",
        zone_id=zone_ids["laurensbosscher.nl"],
        name="google._domainkey.laurensbosscher.nl",
        type="TXT",
        ttl=CLOUDFLARE_AUTO,
        content="v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDBtbbVYxKj9ItpoiTeA2RfyJaRyo1UayyfKG3zkPe8xM8U120d+JYA5Oid8wsnG7H5e/pwzq4OcJqvAn/kIsIeP9InrQevX08jnNmziXoLNcQAv0F7jrnaucXXNExMVknhayvhPiRscrDr+Q2cYSmBnbXRLmclpuzB4fwsTzsPGwIDAQAB",
        opts=resource_opts(
            import_id="80109e07e6038846aa25d17367211948/4e94351d5d9f8fcf5efaec1af28b8988",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    by_logical["dns-laurensbosscher-nl-txt-laurensbosscher-nl-0efa3ed1"] = cloudflare.DnsRecord(
        "dns-laurensbosscher-nl-txt-laurensbosscher-nl-0efa3ed1",
        zone_id=zone_ids["laurensbosscher.nl"],
        name="laurensbosscher.nl",
        type="TXT",
        ttl=CLOUDFLARE_AUTO,
        content="v=spf1 include:_spf.google.com -all",
        opts=resource_opts(
            import_id="80109e07e6038846aa25d17367211948/0efa3ed1932b9134204d16c0be9ca8bb",
            ignore_changes=["tags", "meta", "proxiable"],
        ),
    )

    return DnsRecords(by_logical_name=by_logical)


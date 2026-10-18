from __future__ import annotations

from dataclasses import dataclass

import pulumi
import pulumi_cloudflare as cloudflare

from homelab_cloudflare.helpers import account_id, resource_opts

_ACCOUNT_ID = "1ce5b40c4616a803216dff853ef6bc81"


@dataclass(frozen=True, slots=True)
class R2Buckets:
    by_name: dict[str, cloudflare.R2Bucket]


def _bucket(name: str) -> cloudflare.R2Bucket:
    return cloudflare.R2Bucket(
        f"r2-{name}",
        account_id=account_id(),
        name=name,
        location="eeur",
        jurisdiction="default",
        storage_class="Standard",
        opts=resource_opts(
            protect=True,
            import_id=f"{_ACCOUNT_ID}/{name}/default",
        ),
    )


def create_r2_buckets() -> R2Buckets:
    """Adopt live buckets. Object contents stay outside this stack."""
    by_name = {
        "k3s-etcd": _bucket("k3s-etcd"),
        "k3s-longhorn": _bucket("k3s-longhorn"),
        "save-games": _bucket("save-games"),
    }
    pulumi.export("r2_bucket_names", sorted(by_name))
    return R2Buckets(by_name=by_name)

from __future__ import annotations

from dataclasses import dataclass

import pulumi
import pulumi_cloudflare as cloudflare

from homelab_cloudflare.helpers import account_id, resource_opts

_ACCOUNT_ID = "1ce5b40c4616a803216dff853ef6bc81"


@dataclass(frozen=True, slots=True)
class R2Buckets:
    by_name: dict[str, cloudflare.R2Bucket]


def _bucket(name: str, *, adopt: bool) -> cloudflare.R2Bucket:
    return cloudflare.R2Bucket(
        f"r2-{name}",
        account_id=account_id(),
        name=name,
        location="eeur",
        jurisdiction="default",
        storage_class="Standard",
        opts=resource_opts(
            protect=True,
            import_id=f"{_ACCOUNT_ID}/{name}/default" if adopt else None,
        ),
    )


def create_r2_buckets() -> R2Buckets:
    """Adopt live buckets. Object contents stay outside this stack."""
    by_name = {
        "r2-explorer": _bucket("r2-explorer", adopt=False),
        "save-games": _bucket("save-games", adopt=True),
    }
    pulumi.export("r2_bucket_names", sorted(by_name))
    return R2Buckets(by_name=by_name)

"""Delete Cloudflare DNS records without failing when they are already gone.

pulumi-cloudflare treats DELETE 404 (error 81044, "Record does not exist.") as a
failed delete, which leaves the record in state. The before-delete hook performs
the API delete and accepts that 404. ``retain_on_delete`` then skips the provider
delete that would fail. The live record is still removed when it exists.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pulumi
from pulumi.runtime.sync_await import _sync_await

from homelab_cloudflare.cloudflare_api import DnsDeleteOutcome, delete_dns_record

_DNS_RECORD = "cloudflare:index/dnsRecord:DnsRecord"
_HOOK_NAME = "cloudflare-dns-delete-missing-ok"

_installed = False
_hook: pulumi.ResourceHook | None = None


def install_dns_delete_workaround() -> None:
    """Attach the missing-record delete hook to every DNS record registered after this.

    The hook is registered even when this run creates no DNS records, so a delete
    can still find it. ``pulumi destroy`` does not run the program unless passed
    ``--run-program``; without that flag the hook is absent and ``retain_on_delete``
    would leave the live records in place.
    """
    global _installed
    if _installed:
        return
    hook = _delete_hook()
    # Finish registration before the program returns, including a run that deletes every record.
    _sync_await(hook._registered)
    pulumi.runtime.register_resource_transform(_dns_record_transform)
    _installed = True


def dns_delete_target(
    resource_id: str,
    old_inputs: Mapping[str, Any] | None,
    old_outputs: Mapping[str, Any] | None,
) -> tuple[str, str]:
    zone_id = _field(old_outputs, "zoneId", "zone_id") or _field(old_inputs, "zoneId", "zone_id")
    record_id = resource_id.strip() or _field(old_outputs, "id") or _field(old_inputs, "id")
    if not zone_id or not record_id:
        msg = "cannot delete DNS record: missing zone id or record id"
        raise RuntimeError(msg)
    return zone_id, record_id


def _dns_record_transform(
    args: pulumi.ResourceTransformArgs,
) -> pulumi.ResourceTransformResult | None:
    if args.type_ != _DNS_RECORD:
        return None
    return pulumi.ResourceTransformResult(
        props=args.props,
        opts=pulumi.ResourceOptions.merge(
            args.opts,
            pulumi.ResourceOptions(
                # Provider Delete stays skipped. The hook owns the API call.
                retain_on_delete=True,
                hooks=pulumi.ResourceHookBinding(before_delete=[_delete_hook()]),
            ),
        ),
    )


def _delete_hook() -> pulumi.ResourceHook:
    global _hook
    if _hook is None:
        _hook = pulumi.ResourceHook(_HOOK_NAME, _delete_dns_record)
    return _hook


def _delete_dns_record(args: pulumi.ResourceHookArgs) -> None:
    zone_id, record_id = dns_delete_target(args.id, args.old_inputs, args.old_outputs)
    outcome = delete_dns_record(zone_id, record_id)
    if outcome is DnsDeleteOutcome.ALREADY_GONE:
        pulumi.log.info(
            f"DNS record {record_id} in zone {zone_id} is already gone; treating delete as success"
        )


def _field(mapping: Mapping[str, Any] | None, *keys: str) -> str:
    if mapping is None:
        return ""
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""

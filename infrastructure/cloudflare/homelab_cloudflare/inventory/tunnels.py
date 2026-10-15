from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TunnelRef:
    name: str
    tunnel_id: str
    resource_name: str

    def import_id(self, account_id: str) -> str:
        return f"{account_id}/{self.tunnel_id}"


k8s_tunnel = TunnelRef(
    name="k8s-tunnel",
    tunnel_id="74c090cd-5046-4cb3-9b9f-43f013822d1c",
    resource_name="tunnel-k8s-tunnel",
)

openstick = TunnelRef(
    name="openstick",
    tunnel_id="9ec2e211-3f7b-4664-b720-29d02010af13",
    resource_name="tunnel-openstick",
)

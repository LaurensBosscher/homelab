# qbittorrent (+ Privado OpenVPN via Gluetun)

Gluetun sidecar uses Privado’s **native OpenVPN** provider (`VPN_SERVICE_PROVIDER=privado`).

## Secret

Cluster secret `qbittorrent/gluetun-secrets` (not in git):

| Key | Value |
|---|---|
| `openvpn-user` | Privado VPN username |
| `openvpn-password` | Privado VPN password |

```bash
kubectl -n qbittorrent create secret generic gluetun-secrets \
  --from-literal=openvpn-user='…' \
  --from-literal=openvpn-password='…' \
  --dry-run=client -o yaml | kubectl apply -f -
```

## Why WireGuard failed before

An earlier attempt used custom WireGuard, but `gluetun-secrets` had the **server** peer values in the client fields (`wireguard-private-key` = server public key, `wireguard-addresses` = endpoint IP). Gluetun’s Privado provider is OpenVPN-only; WireGuard would need `VPN_SERVICE_PROVIDER=custom` + a real client `wg0.conf`.

## Notes

- `FIREWALL_OUTBOUND_SUBNETS` keeps cluster pod/service CIDRs (`10.42.0.0/16`,`10.43.0.0/16`) reachable for Prowlarr while the kill-switch is on.
- Privado does not support port forwarding → `VPN_PORT_FORWARDING=off`.
- `SERVER_COUNTRIES` defaults to Switzerland in the Deployment.

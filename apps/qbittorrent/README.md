# qbittorrent (+ Privado WireGuard via Gluetun)

Gluetun sidecar uses **custom WireGuard** with a mounted Privado `wg0.conf`.
(Gluetun’s native `privado` provider is OpenVPN-only; account OpenVPN auth failed with `AUTH_FAILED`.)

## Secret

Cluster secret `qbittorrent/gluetun-secrets` (not in git), key `wg0.conf`:

```bash
kubectl -n qbittorrent create secret generic gluetun-secrets \
  --from-file=wg0.conf=./wg0.conf \
  --dry-run=client -o yaml | kubectl apply -f -
```

Generate the file in the Privado dashboard  
([manual setup KB](https://support.privadovpn.com/kb/article/1130-how-to-generate-a-wireguard-or-openvpn-configuration-file-for-manual-setups/)).

Expected shape:

```ini
[Interface]
PrivateKey = <client private key>
Address = 100.64.x.x/32
DNS = 198.18.0.1,198.18.0.2

[Peer]
PublicKey = <server public key>
AllowedIPs = 0.0.0.0/0
Endpoint = <server-ip>:51820
```

## Why it failed before

`gluetun-secrets` had the **server** peer values stuffed into the client fields:

| Old key | Was | Must be |
|---|---|---|
| `wireguard-private-key` | Privado server public key | Interface `PrivateKey` |
| `wireguard-addresses` | Endpoint IP | Interface `Address` (`100.64.x.x/32`) |

Also: do not set `runAsUser: 1000` on the linuxserver qBittorrent container — s6 needs to start as root and drop via `PUID`/`PGID`.

## Notes

- `FIREWALL_OUTBOUND_SUBNETS` keeps cluster pod/service CIDRs (`10.42.0.0/16`,`10.43.0.0/16`) reachable for Prowlarr while the kill-switch is on.
- Privado does not support port forwarding → `VPN_PORT_FORWARDING=off`.

# qbittorrent (+ Privado WireGuard via Gluetun)

Gluetun sidecar uses **custom WireGuard** with a mounted Privado `wg0.conf`.

## Why WireGuard (not OpenVPN)

Account is Newshosting-bundled PrivadoVPN (`nhwfrjwgmyjr`). Support recommended:

1. OpenVPN TCP port 443 (+ Scramble if available)
2. Else OpenVPN UDP port 8080
3. Zurich / try Frankfurt or Paris

Retested in-cluster with Gluetun `VPN_SERVICE_PROVIDER=privado` (2026-11-20):

| Attempt | Result |
|---|---|
| TCP/443 + Switzerland (or any country) | Gluetun server DB has **no Privado TCP endpoints** → `no server found` |
| UDP/8080 → `zrh-010.vpn.privado.io` | Peer connects, then **`AUTH_FAILED`** |
| UDP/1194 (Gluetun default) | Same **`AUTH_FAILED`** after peer connect |
| Scramble | Not supported by Gluetun |

Website username/password confirmed; WireGuard `wg0.conf` from the Privado dashboard works (exit IP in Privado pool). Keep OpenVPN offline until Privado issues working OpenVPN credentials or a TCP `.ovpn` we can mount as custom config.

## Secret

Cluster secret `qbittorrent/gluetun-secrets` (not in git):

| Key | Purpose |
|---|---|
| `wg0.conf` | Active WireGuard config (required) |
| `openvpn-user` / `openvpn-password` | Kept for retries; unused by current Deployment |

```bash
kubectl -n qbittorrent create secret generic gluetun-secrets \
  --from-file=wg0.conf=./wg0.conf \
  --dry-run=client -o yaml | kubectl apply -f -
```

Generate WireGuard in the Privado dashboard  
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

## Why WireGuard failed before

`gluetun-secrets` had the **server** peer values stuffed into the client fields:

| Old key | Was | Must be |
|---|---|---|
| `wireguard-private-key` | Privado server public key | Interface `PrivateKey` |
| `wireguard-addresses` | Endpoint IP | Interface `Address` (`100.64.x.x/32`) |

Also: do not set `runAsUser: 1000` on the linuxserver qBittorrent container — s6 needs to start as root and drop via `PUID`/`PGID`.

## Notes

- `FIREWALL_OUTBOUND_SUBNETS` keeps cluster pod/service CIDRs (`10.42.0.0/16`,`10.43.0.0/16`) reachable for Prowlarr while the kill-switch is on.
- Privado does not support port forwarding → `VPN_PORT_FORWARDING=off`.
- WebUI credentials: secret `qbittorrent-webui` (`admin` + password).

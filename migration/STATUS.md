# Migration status (2026-10-14)

## V2 cluster
- **bazzite** control-plane SQLite Ready (Tailscale IP / LAN `192.168.1.104`)
- **k3s-london-1**, **k3s-london-3** agents Ready
- Disk: `/var/mnt/data/{downloads,local-path,migrate}`
- local-path → `/var/mnt/data/local-path` (verified)
- Sealed Secrets: 10 old keys registered
- Reloader installed
- ArgoCD core installed; ApplicationSets on **`v2`** branch (manual sync)

## Git
- Branch `v2`: Cloudflare `--protocol http2` (QUIC blocked)

## PVC restore
### Tier0 DONE (verified sizes)
| PVC | Size |
|---|---|
| qbittorrent-config | 14M |
| sabnzbd-config | 15M |
| prowlarr-config | 29M |
| radarr-config | 82M |
| sonarr-config | 37M |
| rdt-client-data | 248K |
| audiobookshelf-config | 684K (re-fixed) |
| audiobookshelf-metadata | 216K |
| calibre-web-config | 439M (re-fixed) |
| calibre-web-library | 204M (re-fixed) |
| openclaw-pvc | 5.1G |

### Bug fixed
`restic snapshots --tag A --tag B` is **OR**, not AND. `restore-pvc.sh` now uses unique `pvc:NAME` tag.

### In progress
- Tier1 restore log: `/var/mnt/data/migrate/logs/restore-tier1.log`

## Cloudflare BLOCKED
Needs fresh tunnel token (`migration` note on bazzite: `/var/mnt/data/migrate/CLOUDFLARE_BLOCKED.txt`).
Old tunnel IDs deleted; openclaw API token lacks Tunnel:Edit.

## Next
1. Fresh `cloudflared-token` secret
2. Finish Tier1 + sync remaining apps
3. Smoke + soak

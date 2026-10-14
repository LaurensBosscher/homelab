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
- `277c0f8` books PVC accessMode/size aligned to bound claims

## PVC restore
### Tier0 DONE
| PVC | Size |
|---|---|
| qbittorrent-config | 14M |
| sabnzbd-config | 15M |
| prowlarr-config | 29M |
| radarr-config | 82M |
| sonarr-config | 37M |
| rdt-client-data | 248K |
| audiobookshelf-config | 684K |
| audiobookshelf-metadata | 216K |
| calibre-web-config | 439M |
| calibre-web-library | 204M |
| openclaw-pvc | 5.1G |

### Tier1 DONE (`TIER1_RESTORE_OK`)
books ingest/stacks, obsidian couchdb×2, linkwarden-data, wanderer×3, aiostreams, fusion, listenarr×2, nanobot, mydia, questarr×2, shiori, bookshelf, stremio, playarr, shelfarr, termix.

### Bug fixed
`restic snapshots --tag A --tag B` is **OR**, not AND. `restore-pvc.sh` uses unique `pvc:NAME` tag.

## Secrets restored
From amsterdam etcd snaptemp + aescbc key (`encryption-config.json`):
- `openclaw/openclaw-secret` (gateway token refreshed from restored `openclaw.json`)
- `linkwarden/linkwarden-secrets` + SQL import `migrate/db/linkwarden.sql.gz`
- `obsidian-live-sync/couchdb-secret`
- `cloudflare/cloudflared-token` (**stale** — tunnel deleted; still Unauthorized)

Helper: `/var/mnt/data/migrate/bin/apply-etcd-secrets.py`

## Cloudflare BLOCKED
Needs **fresh** tunnel token (Tunnel:Edit). Old token/tunnels deleted.
See `/var/mnt/data/migrate/CLOUDFLARE_BLOCKED.txt`.
http2 protocol path OK; registration fails: `Unauthorized: Tunnel not found`.

## Next
1. Fresh `cloudflared-token` + DNS to new tunnel
2. Sync leftovers / fix prometheus CRD order (`monitoring` helm before `prometheus` app)
3. Smoke + soak; then decommission old nodes

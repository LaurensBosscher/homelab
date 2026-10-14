# Migration status (2026-10-14)

## V2 cluster
- **bazzite** control-plane SQLite Ready (LAN `192.168.1.104`)
- **k3s-london-1**, **k3s-london-3** agents Ready
- Disk: `/var/mnt/data/{downloads,local-path,migrate}`
- local-path → `/var/mnt/data/local-path`
- Sealed Secrets + Reloader + ArgoCD on **`v2`** (manual sync)

## Git
- `277c0f8` books PVC accessMode/size aligned
- `0fbe6ef` STATUS
- aiostreams image → `v2.36.0` (restored DB at migration 27)

## PVC restore
- **Tier0 DONE**, **Tier1 DONE** (`TIER1_RESTORE_OK`)
- restic multi-`--tag` is OR → use unique `pvc:NAME`

## Secrets
Restored 29 secrets from amsterdam etcd snaptemp + aescbc key via  
`/var/mnt/data/migrate/bin/apply-all-etcd-secrets.py`  
(+ linkwarden SQL import).

## Cloudflare
**UP** — `cloudflared` registered over http2 (`Registered tunnel connection`).  
Origin errors for prometheus/alertmanager until those are healthy.

## Remaining
1. openclaw gateway startup probe / doctor hang
2. prometheus app CRDs (sync monitoring helm chart first)
3. qbittorrent/stacks `replicas: 0` intentional in git
4. Smoke + soak; decommission old nodes later

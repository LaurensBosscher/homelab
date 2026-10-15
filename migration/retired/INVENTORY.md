# V2 Migration Inventory

Captured: 2026-10-14 from live V1 cluster (via `k3s-london-1`).

## Cluster snapshot

| Item | Value |
|---|---|
| Nodes | bazzite (agent), london-1/3 (CP+etcd), london-2 **NotReady**, amsterdam SchedulingDisabled, california×2 |
| Total Longhorn actual used | **~23.4 GiB** |
| Largest volume | `openclaw/openclaw-pvc` ~17.3 GiB |
| Bazzite root (`nvme`) | ~237 GiB, ~82 GiB free; Longhorn dir ~22.5 GiB |
| Bazzite media | `/mnt/downloads` → `/var/mnt/downloads` on `/dev/sda` ~468 GiB, ~390 GiB free |
| Longhorn → B2 | `s3://longhorn-backups-ay76@s3.eu-central-003/` (nightly backups completing 2026-10-14) |
| Sealed Secrets | 10 keys exported offline (all labeled present in cluster) |

## Problem volumes (live attach broken / empty)

| NS/PVC | State | Notes |
|---|---|---|
| `your-spotify/your-spotify-mongo-data` | faulted / detaching, 0 used | Rely on Longhorn B2 backup or recreate |
| `linkwarden/linkwarden-meili-data` | faulted / detaching, 0 used | Search index — recreate OK |
| `norish/norish-{data,db-data,redis-data}` | detached / unknown, 0 used | App likely down; check Longhorn B2 |
| `termix/termix-tailscale-state` | detached | Tier 2 recreate |
| `shiori/shiori-data` | degraded but has data | Prefer live export soon |

## Classification (by used bytes)

### Tier 0 — must not lose

| NS | PVC | Used MiB | Cap MiB | Method |
|---|---|---:|---:|---|
| — | sealed-secrets keys | — | — | secret yaml export |
| openclaw | openclaw-pvc | 17729 | 20480 | A (scale 0 → restic) |
| books | calibre-web-config | 487 | 1024 | A |
| books | calibre-web-library | 351 | 5120 | A |
| books | calibre-web-ingest | 17 | 1024 | A |
| obsidian-live-sync | couchdb-data | 147 | 5120 | C (couch dump) + A |
| obsidian-live-sync | couchdb-config | 24 | 128 | A |
| linkwarden | linkwarden-postgres-data | 113 | 1024 | C `pg_dump` |
| linkwarden | linkwarden-data | 71 | 1024 | A |
| wanderer | wanderer-db-data | 312 | 2048 | C (engine dump) |
| wanderer | wanderer-data | 147 | 5120 | A |
| wanderer | wanderer-search-data | 99 | 2048 | A or recreate index |
| audiobookshelf | audiobookshelf-config | 49 | 1024 | A |
| audiobookshelf | audiobookshelf-metadata | 49 | 1024 | A |
| radarr | radarr-config | 420 | 1024 | A |
| sonarr | sonarr-config | 414 | 2048 | A |
| prowlarr | prowlarr-config | 171 | 1024 | A |
| qbittorrent | qbittorrent-config | 63 | 1024 | A |
| sabnzbd | sabnzbd-config | 65 | 1024 | A |
| rdt-client | rdt-client-data | 97 | 2048 | A |

### Tier 1 — migrate if easy

| NS | PVC | Used MiB | Method |
|---|---|---:|---|
| aiostreams | aiostreams-data | 594 | A |
| fusion | fusion-data-fusion-0 | 589 | A |
| listenarr | listenarr-config | 438 | A |
| listenarr | listenarr-data | 147 | A |
| nanobot | nanobot-data | 238 | A |
| mydia | mydia-config | 144 | A |
| questarr | questarr-postgres-data | 144 | C |
| questarr | questarr-data | 49 | A |
| shiori | shiori-data | 133 | A (degraded — priority) |
| bookshelf | bookshelf-config | 98 | A |
| stremio | stremio-data | 97 | A |
| playarr | playarr-config | 94 | A |
| shelfarr | shelfarr-config | 52 | A |
| termix | termix-data | 49 | A |
| books | stacks-config | 38 | A |

### Tier 2 — recreate empty

- `kite-data`, `gatus-data`, `beszel-data`
- `stacks-logs`, `termix-tailscale-state`
- `linkwarden-meili-data` (faulted/empty)
- norish\* if Longhorn backups empty / app abandoned
- `your-spotify-mongo-data` if B2 restore fails

### Tier 3 — no PVC migration

- `/mnt/downloads` on bazzite (path stable; optional restic later)

## Cutover constraint

No spare nodes: **export everything durable → stop V1 on retained nodes → rebuild V2 in place** (bazzite = SQLite server).

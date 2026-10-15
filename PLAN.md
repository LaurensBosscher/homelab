# Homelab V2 Plan

Goal: greatly reduce operational complexity while keeping the apps and GitOps workflow.
Downtime is acceptable.

## Decisions

| Topic | Choice | Why |
|---|---|---|
| Nodes | `bazzite` + 2 London workers | Enough capacity; drop multi-region cost/complexity |
| Control plane | Single K3s server on **bazzite** | Home node already holds media/`hostPath` data |
| Datastore | **SQLite** (K3s default) | Simplest and most performant locally |
| Storage | **local-path** on bazzite big disk (no Longhorn) | Remove CSI/replication overhead; NVMe too small for all PVCs |
| Media + PVC root | Rename `/mnt/downloads` → **`/mnt/data`** at cutover | Path will host media *and* local-path PVCs; name should not say downloads |
| Ingress | Cloudflare Tunnel for Internet → cluster only | Not used as node mesh |
| Node networking | Public WAN + tight nftables peer allowlist; keep Flannel `wireguard-native` for pod overlay | Simpler than multi-region mesh; overlay stays encrypted |
| GitOps / UX | Keep ArgoCD, Kite, Reloader, Sealed Secrets | High value, low complexity |
| Backups | restic (or similar) → Backblaze B2 | Covers SQLite DB + PVC data; etcd-snapshot does **not** apply to SQLite |
| Deferred | Kine T4 / R2 continuous CP backup | Interesting later; not needed for V2 day one |

### Explicit non-goals for V2

- Multi-region placement / storage classes (`europe` / `us` / `zurich`)
- Longhorn (replicas, rebuilds, CSI sidecars)
- Embedded etcd HA / etcd compaction automation
- T4 as primary datastore on day one
- Cloudflared as inter-node fabric

## Target architecture

```text
bazzite     = K3s server (SQLite) + ALL PVCs (local-path) + /mnt/data
london-1    = K3s agent (stateless / overflow)
london-2    = K3s agent (stateless / overflow)

/mnt/data/                 # former /mnt/downloads (big disk)
  downloads/               # media tree (*arr / SAB / ABS hostPaths)
  local-path/              # K3s local-path-provisioner root
  migrate/                 # cutover staging only; delete after soak

Ingress:    1× cloudflared (optional standby later)
CD:         ArgoCD
Secrets:    Sealed Secrets (key backed up)
Reload:     Reloader
Dash:       Kite
Backup:     restic → B2
  - /var/lib/rancher/k3s/server/db/
  - /var/lib/rancher/k3s/server/token
  - /mnt/data/local-path/  (PVC data)
  - optional: /mnt/data/downloads/
```

### Networking notes

- Keep Tailscale for SSH/admin only (not CNI underlay).
- Allow only peer node IPs for K3s/Flannel ports.
- Do not expose NodePorts / datastore ports to the world.
- Collapse regional cloudflared deployments unless a clear latency need remains.

### SQLite backup note

K3s built-in `etcd-snapshot` / S3 snapshotting is for **embedded etcd**, not SQLite.

SQLite backup/restore (official model):

1. Copy `/var/lib/rancher/k3s/server/db/`
2. Also copy `/var/lib/rancher/k3s/server/token` (required; encrypts sensitive DB contents)
3. Restore both, start K3s with the same token

Prefer a short K3s stop or `sqlite3 .backup` for consistent copies. Nightly restic of `db/` + `token` is enough for V2.

---

## Data migration approach

Do **not** try to convert Longhorn volumes in place.
Export from V1 → durable stage → wipe retained nodes → restore into V2 `local-path` PVCs.

### Constraint: no spare nodes

`bazzite` hosts **both** V1 (today) and V2 (after cutover). V1 and V2 cannot run usefully in parallel on the same host (API/CNI/kubelet conflict).

Cutover model: **export everything durable → stop V1 on retained nodes → rebuild V2 in place**.

```text
export → restic/B2 (+ staging under current /mnt/downloads/_migrate)
  → stop/uninstall K3s+Longhorn on bazzite + 2 Londons
  → rename disk layout to /mnt/data/{downloads,local-path,migrate}
  → install V2 SQLite server on bazzite, join 2 agents
  → restore into local-path on /mnt/data/local-path
```

Pre-cutover confidence comes from **restic restore drills**, not a second live cluster.

### Strategy (hybrid)

| Role | Option | Use |
|---|---|---|
| Primary filesystem export | Live PVC export via helper pods | Most config/data volumes |
| Primary DB export | App-native dumps | Postgres / Mongo / CouchDB |
| Bridge / durable staging | restic → B2 (+ `/mnt/downloads/_migrate` on bazzite) | Survives V1 wipe on shared hardware |
| Safety net | Existing Longhorn → B2 backups | Insurance / rescue before teardown |
| Skip | Recreate disposable volumes | Monitoring/cache/dashboard state |
| Last resort | Raw Longhorn replica copy from disk | Only if attach/export is broken |

### Why this hybrid

- Live export is simple while Longhorn is healthy.
- Logical DB dumps avoid dirty filesystem copies.
- restic is both migration transport and the V2 backup system.
- Local staging on the media disk survives K3s/Longhorn wipe on the NVMe.
- Longhorn B2 backups stay available if a live volume is unhealthy.
- Raw replica surgery is too fragile for the default path.

---

## Volume classification

Classify every PVC before export. Use **actual used bytes**, not requested Gi.

### Tier 0 — must not lose

- Sealed Secrets private key (`sealed-secrets-key`)
- `couchdb-data` / `couchdb-config` (Obsidian Live Sync)
- `calibre-web-library` + `calibre-web-config` (+ ingest if needed)
- `openclaw-pvc`
- DB volumes:
  - Linkwarden (`linkwarden-postgres-data`, plus app data)
  - Norish (`norish-db-data`, plus app/redis as needed)
  - Wanderer (`wanderer-db-data`, search/data)
  - `your-spotify-mongo-data`
- Core media-app configs: Audiobookshelf, Radarr, Sonarr, Prowlarr, qBittorrent, SABnzbd, RDT-Client

### Tier 1 — migrate if easy

- listenarr, shelfarr, playarr, stremio, shiori, termix, aiostreams, nanobot, mydia, bookshelf, questarr, stacks-config, fusion

### Tier 2 — recreate empty

- `kite-data`
- `gatus-data`
- `beszel-data`
- logs / caches / disposable state (e.g. `stacks-logs`, `termix-tailscale-state`)

### Tier 3 — no PVC migration (path rename only)

- Media stays on the same disk; at cutover rename `/mnt/downloads` → `/mnt/data/downloads` and update hostPath manifests
- Do **not** restic-copy the whole media tree as part of PVC migration

---

## Export methods

### A. Live PVC export (default for filesystem volumes)

1. Scale Deployment/StatefulSet to 0
2. Start a helper pod mounting the PVC read-only
3. `tar` / `restic backup` the mount
4. Verify size / file count / checksum
5. Mark volume exported

Notes:

- Prefer scaling to 0 over fighting RWO attach conflicts.
- If the Longhorn replica is not on bazzite, stream over SSH/WAN or push straight to B2.

### B. Longhorn B2 backup (safety net)

Existing target:

```text
s3://longhorn-backups-ay76@s3.eu-central-003/
```

1. Confirm/trigger backups for Tier 0 (+ Tier 1 if cheap)
2. Keep V1/Longhorn available until V2 is verified
3. If a live volume is bad, restore Longhorn backup to a temp volume, then export with method A

This is insurance, not the primary import path into `local-path`.

### C. App-native logical dumps (preferred for databases)

| App | Method |
|---|---|
| Linkwarden Postgres | `pg_dump` |
| Norish DB | engine-native dump |
| Wanderer DB | engine-native dump |
| your-spotify Mongo | `mongodump` |
| Obsidian CouchDB | couchbackup / replicate / `_all_dbs` export |
| SQLite-in-PVC apps | stop app, copy DB (+ WAL/SHM) or `sqlite3 .backup` |

Still export surrounding config/metadata dirs with method A when needed.

### D. Raw Longhorn replica copy (emergency only)

Copy replica data from node disk (e.g. under `/var/lib/longhorn/`) only if Kubernetes/CSI attach is broken and the volume is critical. High risk of selecting the wrong replica or inconsistent filesystem state.

### E. Recreate

For Tier 2 volumes: create empty PVC on V2 and accept lost history/settings.

### F. restic bridge (standard packaging)

Store all migration artifacts in one restic repo on B2, with optional local staging on bazzite:

```text
restic-homelab-migrate/
  secrets/sealed-secrets-key
  pvc/<namespace>/<pvc-name>/
  db/<app>.dump
  host/mnt-downloads/          # optional
  k3s/server-db/               # final V1 SQLite copy if useful
  k3s/server-token
```

V2 restore:

1. Create `local-path` PVC
2. Helper pod mounts PVC
3. `restic restore` into mount (or `pg_restore` / `mongorestore` for dumps)
4. Start app

---

## Consistency rules

| Data type | Quiesce / method |
|---|---|
| Config dirs / most app PVCs | scale to 0 → tar/restic |
| Postgres / Mongo | logical dump preferred |
| CouchDB | dump/replicate preferred |
| SQLite files in PVC | stop app → copy/backup |
| Media hostPath | no migration; optional backup |
| Sealed Secrets key | export before any cluster wipe |

Do not `tar` a live database volume while the app is writing.

---

## Migration phases

### Phase 0 — Inventory

- [ ] List all PVCs with **used** bytes (Longhorn UI and/or `du` in export pods)
- [ ] Fill classification table: MUST / NICE / RECREATE
- [x] Confirm media disk stays on bazzite; rename to `/mnt/data` at cutover
- [ ] Confirm B2 credentials work for restic (can reuse Longhorn B2 account with a new bucket/prefix)
- [ ] Document current Sealed Secrets key backup location

### Phase 1 — Freeze & export (V1 still up)

- [ ] Pause Renovate / risky Argo auto-sync if helpful
- [ ] Trigger Longhorn backups for Tier 0 (safety net)
- [ ] Export Sealed Secrets key
- [ ] Export Tier 0 filesystem volumes (method A → restic/local)
- [ ] Dump Tier 0 databases (method C → restic/local)
- [ ] Export Tier 1 volumes worth keeping
- [ ] Verify restores from restic for at least one filesystem PVC and one DB dump
- [ ] Keep V1 running until V2 is proven

### Phase 2 — Rebuild retained nodes in place

No parallel V2 cluster. After exports are verified:

- [ ] Final Tier 0 refresh export
- [x] Stop K3s on retained nodes (bazzite + london-1 + london-3)
- [x] Uninstall K3s; wipe `/var/lib/rancher/k3s` and `/var/lib/longhorn` (do **not** wipe the media disk)
- [x] On bazzite, restructure the big disk to `/mnt/data`:
  - move current media tree to `/mnt/data/downloads`
  - create `/mnt/data/local-path` and `/mnt/data/migrate`
  - keep migrate artifacts until restore completes
- [x] Install K3s single-server with SQLite on **bazzite**
- [x] Join 2 London agents (london-1 + london-3)
- [x] Join london-2 as third agent (2026-10-14 ~16:34Z; see STATUS)
- [x] Keep Flannel WireGuard native (via Tailscale iface)
- [ ] Install/bootstrap: local-path ✅, Sealed Secrets ✅; still need Reloader, ArgoCD, Kite
- [ ] Deploy restic backup CronJobs/scripts for SQLite `db/` + `token` and PVC data
- [ ] Collapse cloudflared to one tunnel deployment (plus optional standby later)

### Phase 3 — Git cutover (`v2` branch)

- [x] Change all retained PVCs to `storageClassName: local-path` (or equivalent single class)
- [x] Remove Longhorn Application and Longhorn storage classes
- [x] Replace geo affinity with stateful pin to bazzite (`nodeSelector` / hostname affinity)
- [x] Point media hostPaths at `/mnt/data/downloads/...`; local-path root `/mnt/data/local-path`
- [x] Simplify Cloudflare tunnel manifests (single `cloudflared` on bazzite)
- [x] Point ArgoCD at `v2` / updated paths (automated sync re-enabled 2026-10-15)

### Phase 4 — Restore apps

Order:

1. Sealed Secrets controller + restored sealing key
2. Reloader
3. Cloudflare tunnel
4. Tier 0 apps (restore data, then sync/start)
5. Tier 1 apps
6. Tier 2 apps (empty PVCs)

- [ ] Smoke-test: tunnel/DNS, one DB app, one media app, ArgoCD, Kite
- [ ] Confirm backups on V2 actually write to B2

### Phase 5 — Decommission V1

Only after V2 has been used successfully for a few days.

- [ ] Final optional Longhorn/V1 backup
- [ ] Destroy unused nodes (California / Amsterdam / extra London / etc.)
- [ ] Remove Longhorn and old inventory/firewall peer entries
- [x] Update README, Ansible `hosts.ini`, and docs for 4-node topology (bazzite + london-1/2/3)
- [ ] Cancel unused VPS subscriptions

---

## Restore patterns on V2

| Pattern | Use |
|---|---|
| Helper pod → `local-path` PVC | Default for filesystem volumes |
| App-native import (`pg_restore`, `mongorestore`, CouchDB replicate) | Databases |
| hostPath bind for selected big/simple data | Optional; more pet-server, less portable |
| Empty PVC | Tier 2 recreate |

Preferred default: helper-pod restore into `local-path` under `/mnt/data/local-path`, logical import for DBs, media via `/mnt/data/downloads` hostPaths.

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Losing Sealed Secrets key | Export/test restore before wipe; keep offline copy |
| Dirty DB copy | Prefer logical dumps; always scale to 0 for filesystem DB copies |
| Migrating requested size instead of used size | Measure used bytes in Phase 0 |
| Tearing down V1 too early | Keep V1 until V2 soak period ends |
| Assuming K3s SQLite has etcd-snapshot S3 | Use restic/file copy of `db/` + `token` |
| Forgetting PVC backups after cutover | Install restic jobs on V2 day one |
| Stateful pod scheduled off bazzite | Pin stateful apps to bazzite |

---

## Success criteria

- Three-node cluster healthy with SQLite on bazzite
- No Longhorn components remain
- Tier 0 apps restored and usable
- ArgoCD syncing from Git
- Sealed Secrets encrypt/decrypt works with restored key
- Nightly restic backups of SQLite + PVCs landing in B2
- Old multi-region nodes decommissioned

## Later experiments (out of scope for cutover)

- Single-node T4 + object store continuous CP backup (R2/S3 with conditional PUTs; not B2 for T4 coordination)
- Second control-plane server
- Prometheus trim vs Beszel/Gatus-only monitoring
- Further app decluttering

---

## Immediate next actions

1. ~~Produce PVC inventory~~ → see `migration/INVENTORY.md`
2. ~~Create restic repo on B2~~ → `longhorn-backups-ay76/restic-homelab-migrate`
3. ~~Export Sealed Secrets keys~~ → offline copy + restic snapshot `f75896fb`
4. Export remaining Tier 0/1 volumes + DB dumps; restore-drill
5. Prepare `v2` Git branch offline, then book cutover window for in-place rebuild

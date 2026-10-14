# Migration status (2026-10-14)

## V2 cluster
- **bazzite** control-plane SQLite Ready (LAN `192.168.1.104`)
- **k3s-london-1**, **k3s-london-3** agents Ready
- Disk: `/var/mnt/data/{downloads,local-path,migrate}`
- local-path → `/var/mnt/data/local-path`
- Sealed Secrets + Reloader + ArgoCD on **`v2`** (manual sync)

## Cutover progress
| Area | State |
|---|---|
| Tier0 + Tier1 PVC restore | **DONE** |
| App secrets (29 from etcd snaptemp) | **DONE** |
| linkwarden SQL import | **DONE** |
| Cloudflare tunnel (http2) | **UP** |
| openclaw gateway | **3/3 Ready** (`healthz` ok) |
| aiostreams | **Running** on `v2.36.0` |
| Media stack (sab/sonarr/radarr/prowlarr/rdt) | **Healthy** |
| prometheus stack | **Synced/Healthy** (CRDs SSA + admission webhooks disabled) |
| In-cluster smoke | **PASS** (see below) |

## Git on `v2`
- `22c9587` cloudflare yaml repair; prometheus admission TLS off
- `90722de` openclaw doctor `timeout` wrappers
- `11bc693` aiostreams `v2.36.0`

## Helpers on bazzite
- `/var/mnt/data/migrate/bin/restore-pvc.sh`, `restore-tier1.sh`
- `/var/mnt/data/migrate/bin/apply-all-etcd-secrets.py`
- `/var/mnt/data/migrate/tmp-crds/` (prometheus-operator v0.77.2 CRDs, SSA)

## Smoke (in-cluster)
| Target | Result |
|---|---|
| sabnzbd / sonarr / radarr / prowlarr / rdt-client | OK |
| linkwarden / fusion / shiori / audiobookshelf | OK |
| openclaw `/healthz` | 200 |
| aiostreams / gatus / calibre-web | OK |
| prometheus `/-/ready` / grafana `/login` | OK |
| alertmanager `/-/ready` | OK (from prometheus pod) |
| homepage | 400 without Host (expected) |
| kite | Running in **kube-system** (`kite.kube-system.svc`) |

## Known / intentional
1. `qbittorrent` / `stacks` / `norish` / `termix` **`replicas: 0`** in git → Pending WaitForFirstConsumer PVCs → Argo **Progressing** (or qbittorrent **OutOfSync** sidecar drift). Leave until needed.
2. ArgoCD uses **core-install** (no `argocd-server` Deploy/Service). CF/homepage/gatus URLs to `argocd-server.argocd.svc` will fail until UI is added or tunnel paths updated.
3. london-1 kubelet `:10250` sometimes returns **502** via apiserver proxy (exec/logs flaky); workloads still schedule/run.

## Remaining
1. Soak (watch CF tunnel, media downloads, openclaw, prometheus rules)
2. Decommission old nodes after soak

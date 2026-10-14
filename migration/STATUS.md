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
3. Flannel on **`tailscale0`** + API via Tailscale: london-1 briefly **NotReady** (TLS/API dial flaps). Fixed with `systemctl restart k3s-agent` on london-1; all 3 nodes Ready again. Watch Tailscale direct vs DERP during soak.

## Soak
- **Started:** `2026-10-14T12:16:11Z` (`/var/mnt/data/migrate/SOAK_START.txt`)
- **Post-cutover check (12:24Z):** all 3 nodes Ready; no CrashLoop/Pending app pods; media smoke OK; prometheus+alertmanager `/-/ready` = 200
- Watch: CF tunnel, media downloads, openclaw, prometheus/alertmanager, **london-1 Tailscale↔API stability**
- **Do not** decommission old nodes until soak is clean

## Soak notes (2026-10-14 ~12:24Z)
1. **london-1 flaps** — agent briefly `FAILED`/`RECOVERING` on dial to `100.81.190.71:6443` (TLS handshake timeouts on local LB `:6444`). Recovers to Ready without reboot. london-3 had **0** flaps in same window.
2. Alertmanager runs on london-1 → CF briefly sees `connection refused` on `:9093` during flaps; in-cluster ready probes OK when node is Ready.
3. ICMP to london-1 Tailscale IP can fail while `tailscale ping` / TCP :10250 work (path: direct `46.33.10.93:41641`). Prefer Tailscale/TCP checks over ICMP.
4. `argocd-server` still absent (core-install) → CF/homepage lookups for it will keep failing (expected).
5. `books` Argo **Progressing** because `stacks-logs` PVC Pending (`WaitForFirstConsumer`, stacks `replicas: 0`).

## Remaining
1. Complete soak window (watch london-1 Tailscale↔API flaps)
2. Decommission old nodes after soak

## Soak mitigation (2026-10-14 ~12:30Z)
- **Pinned** `alertmanager` + `metrics-server` to **`bazzite`** (helm values + live patch) — london-1 still flapping `FAILED`/`RECOVERING` on API dial; AM on london-1 caused CF `:9093` connection refused during flaps.

# Migration status (2026-10-14)

## V2 cluster
- **bazzite** control-plane SQLite Ready (LAN `192.168.1.104`)
- **k3s-london-1**, **k3s-london-3** agents Ready
- **k3s-london-2** intended **worker** (same role as london-1) — **not** decommissioned; join blocked on SSH (see below)
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
- `44cb946` pin alertmanager + metrics-server to bazzite
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
3. ~~Flannel on `tailscale0` caused london-1 API flaps~~ → **fixed 12:54Z** (Flannel moved to public WAN; Tailscale = admin/API only). See soak note below.

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

## Soak mitigation (2026-10-14 ~12:30Z)
- **Pinned** `alertmanager` + `metrics-server` to **`bazzite`** (helm values + live patch) — london-1 still flapping `FAILED`/`RECOVERING` on API dial; AM on london-1 caused CF `:9093` connection refused during flaps.

## Soak check (2026-10-14 ~12:35Z)
- Pin **verified live**: AM `alertmanager-…-0` and `prometheus-metrics-server` both on **bazzite**; Argo `prometheus` **Synced/Healthy**.
- All 3 nodes Ready; **0** non-Running/non-Succeeded pods.
- CF tunnel up (http2). Post-pin CF logs: no further `:9093` refused; remaining `argocd-server` DNS misses are **expected** (core-install).
- **london-1** still flapping: Ready `lastTransitionTime` advanced again at `12:23:10Z` and `12:33:09Z`. london-3 stable.
- Interrupted in-cluster smoke at 12:28 (timeout); re-running AM/prom/sab/sonarr ready checks.

## Soak check (2026-10-14 ~12:38Z) — resumed after bg_62 timeout
- AM endpoints `10.42.0.196:9093/8080` on **bazzite**; in-pod `/-/ready` → **OK** (AM + Prometheus).
- In-cluster HTTP smoke: sonarr/prowlarr/rdt **200**, radarr **302**, prom/AM `/-/ready` **200**, openclaw `/healthz` **200** (`{"ok":true}`). sabnzbd is on **:8085** (not 8080).
- Argo: all apps **Synced**; Health **Healthy** except intentional Progressing (`books`/`norish`/`termix` replicas:0) and `qbittorrent` OutOfSync/Healthy.
- CF logs since AM pin (~12:30): **no** further `:9093` refused; only expected `argocd-server` DNS misses.
- **london-1** still flapping: `NodeNotReady` ~12:34Z → Ready again `12:35:01Z`. london-3 stable. Soak continues; do **not** decommission legacy nodes yet.

## london-1 flap RCA + fix (2026-10-14 ~12:54Z)
**Root cause:** cutover drift put Flannel `wireguard-native` on **`tailscale0`** (bazzite + london-1). That nested WG-in-WG and flooded Tailscale (~**500 MiB/10s**, **~16k tx_drops/s** on bazzite), which starved the same Tailscale path used for agent→API (`100.81.190.71:6443`) → TLS handshake timeouts / `ACTIVE↔FAILED` thrash. london-3 was stable because it still used **public WAN** for Flannel (PLAN-aligned).

**PLAN intent:** Tailscale = SSH/admin only; Flannel over public WAN + nftables peer allowlist.

**Live fix applied:**
- `bazzite`: `flannel-iface=enp2s0`, `node-ip=192.168.1.104`, `node-external-ip=84.226.17.204`, `flannel-external-ip=true` (backup `config.yaml.bak.*`)
- `k3s-london-1`: `flannel-iface=ens3`, `node-ip/external=46.33.10.93`
- `k3s-london-3`: `flannel-iface=eth0`, `node-ip/external=85.121.120.36`
- Restarted `k3s` / `k3s-agent`

**Post-fix checks:**
- WG peers on public WAN (`46.33.10.93` / `85.121.120.36` / `84.226.17.204`); flannel MTU **1420** (was 1200 nested)
- Tailscale tx_drops **0**/10–15s; TS bytes ~**40–600 KiB/15s** (was hundreds of MiB/10s)
- london-1 API dial 15/15 OK ~110ms; **0** `ACTIVE→FAILED` in post-restart window
- Smoke: alertmanager `/-/ready` OK; sonarr **200**
- Keep watching through soak; still **do not** decommission legacy nodes yet.

## Soak check (2026-10-14 ~12:58Z) — post Flannel→WAN
- All 3 nodes **Ready** with public/LAN InternalIPs (london-1=`46.33.10.93`, london-3=`85.121.120.36`, bazzite=`192.168.1.104`)
- WG endpoints confirmed public WAN on all nodes (no `100.x` Flannel peers)
- Tailscale drops **0**/20s; AM + metrics-server still on **bazzite** and Ready
- london-1: **0** `ACTIVE→FAILED` in last 3m; API dials ~110ms stable
- Ansible hardened so cutover drift cannot return: physical NIC preference + assert against `tailscale0`, `cluster_wan_ip` → `node-external-ip`, agent/server templates match live configs

## zswap migration (2026-10-14 ~13:45Z) — verified 15:46Z
Replaced **zram** with **zswap + disk swap** (Chris Down guidance). Never run zram alongside disk swap (LRU inversion).

| Node | Swap backing | zswap | oomd |
|---|---|---|---|
| bazzite | `/var/swapfile` 8G (btrfs NOCOW `C`) | Y zstd/zsmalloc/shrinker | active (bundled in systemd) |
| london-1 | `/swapfile` 2.4G | Y zstd/zsmalloc/shrinker | active (`systemd-oomd` rpm) |
| london-3 | `/swapfile` 3.7G | Y zstd/zsmalloc/shrinker | active (`systemd-oomd` rpm; was zram+disk) |

- **No zram swap** on any node; `vm.swappiness=100`, `vm.page-cluster=1`
- Persist: `zswap-enable.service` + fstab + `/etc/modprobe.d/zswap.conf`
- Ansible: `roles/zswap` (btrfs-aware), `zram` retired/fails closed, `apply-zswap.yml`
- Note: first Alma apply hung on `dnf install systemd-oomd` (~3m); role now uses async + earlyoom fallback

## Soak passed — short window (2026-10-14 ~13:50Z)
Criteria: flap-free after Flannel→WAN fix (`12:54:41Z`).
- london-1 Ready continuously since **12:54:41Z** (~56m+); **0** `ACTIVE→FAILED` since fix / last 60m
- API dials ~110ms stable; Tailscale tx_drops **0**/15s; WG peers on public WAN
- Smoke: sonarr **200**, alertmanager ready **200**, cloudflared Running; **0** non-Running pods
- PLAN Phase 5 still says “a few days” before **destroying** VPS — short soak is enough to soft-decommission

## Soft-decommission legacy V1 (2026-10-14 ~13:52Z, verified ~14:00Z)
| Host | Result |
|---|---|
| amsterdam | **k3s inactive, bins/data gone, sshd active** (brief SSH outage after `k3s-killall` iptables flush; recovered) |
| california | **k3s inactive, bins/data gone, sshd active** (safe clean without killall) |
| california-2 | **k3s inactive, bins/data gone, sshd active** |
| london-2 | **KEEP as V2 worker** — Tailscale up; SSH broken; join pending console |

- `servers/ansible/hosts.ini` → V2-only (retired hosts commented)
- `hosts.v2.ini` synced to same
- README updated for 3-node V2 topology
- **Do not cancel VPS billing yet** — wait multi-day soak per PLAN, then destroy amsterdam/california×2 at the providers + remove from Tailscale
- **london-2 stays** — join as fourth node once SSH/console works

## SELinux / k3s fix (2026-10-14 ~16:50Z)
Root cause was **config + labels**, not missing k3s SELinux support (`k3s-selinux` was already installed).

| Host | OS SELinux | k3s `selinux` | k3s domain |
|---|---|---|---|
| bazzite | Permissive | **true** | `container_runtime_t` |
| london-1 | Enforcing | **true** | `container_runtime_t` |
| london-3 | **Disabled** | true (config only) | n/a until OS SELinux enabled |

Fixes applied:
- `selinux: true` in `/etc/rancher/k3s/config.yaml` on all 3 nodes
- Relabeled `/usr/local/bin/k3s` → `container_runtime_exec_t` (was `user_tmp_t` on bazzite; local `bin_t` override on london-1)
- Custom fcontexts: `/run/k3s` → `container_var_run_t`, `/etc/rancher` → `container_config_t`, `/mnt/data/local-path` → `container_file_t` (Bazzite `/var/mnt` ≡ `/mnt`)
- `restorecon` on rancher/kubelet/local-path trees; `container_manage_cgroup` on
- Recycled bazzite pods so shims leave leftover `init_t` (k3s `KillMode=process` keeps old shims across service restarts)
- Masked `setroubleshootd` on bazzite (was ~100% CPU replaying AVC backlog; live AVC rate ~0 after domain fix)

Ansible: `k3s_selinux_enabled: true` (host_vars + inventory defaults); `k3s-common` now installs/labels fcontexts + `restorecon` after upgrades.

Still Permissive on bazzite — flip to Enforcing after multi-day soak if AVC stays quiet. london-3 needs OS SELinux enable + reboot before k3s SELinux is meaningful there.

### Side-effect fixed during SELinux work
Pod recycle + k3s restarts made Tailscale pick Flannel (`10.42.x:41641`) as “direct” paths → agent→API TLS blackhole (first ClientHello segment lost). Mitigations on all 3 nodes:
- `block-tailscale-on-flannel.service` — DROP udp/41641 on `flannel-wg`/`cni0`
- `fix-overlay-mss.sh` — `tailscale0` MTU 1200 + TCPMSS 1100 on `tailscale0`/`flannel-wg`
- Tailscale endpoints back on public WAN (`46.33.10.93` / `85.121.120.36`)

### Verified (2026-10-14 ~17:07Z)
- All 3 nodes **Ready**; **54 Running** pods; **0** CrashLoop/Pending apps
- bazzite load ~1.85 (was ~setroubleshoot-dominated); AVC k3s since boot **0**; `setroubleshootd` **masked**
- `block-tailscale-on-flannel` **active** on all 3; `tailscale0` MTU **1200** everywhere
- london-1 Enforcing + `container_runtime_exec_t`; agent→API returns **401** (TLS path healthy)
- Ansible: `roles/k3s-common` SELinux fcontexts; `roles/tailscale` Flannel block + MSS; `group_vars` `tailscale_mtu: 1200`

## london-2 join (blocked 2026-10-14 ~16:05Z; LAN probe ~16:07Z)
**Intent:** V2 worker alongside london-1/3 (stateless overflow). Inventory + `migration/join-london-2.sh` ready (`054398c`); **do not** cancel this VPS.

**Reachability (from london-1 /26):**
- ICMP OK (~0.24ms); ARP `52:54:00:32:58:50` on `ens3`
- LAN open: **only `:9100`** (node_exporter; often HTTP 503 concurrent-limit)
- LAN closed/timeout: `:22`, `:80`, `:443`, `:6443`, `:10250`, `:2379`, `:9099`, `:41641`
- Tailscale (`100.107.92.7`): `:22` TCP accepts then **empty banner / connection closed** (sshd wedged or filtered mid-handshake)
- No leftover k3s ports → not currently a cluster member

**Join path once SSH works:** CP already accepts `:6443` / UDP `:51820`; london-1 nftables still lists `46.33.10.90` as Flannel peer from V1.

**Blocker:** needs **provider console** (same /26 as london-1 → pandahost).

**Console checklist:**
1. `systemctl restart sshd && journalctl -u sshd -n 50` (disk full / MaxStartups / crowdsec / fail2ban)
2. Confirm key login from laptop via `100.107.92.7`
3. `K3S_TOKEN=$(ssh bazzite cat /var/lib/rancher/k3s/server/node-token) bash migration/join-london-2.sh` (or paste on console)
4. Ansible: `site.yml` limit `k3s-london-2` for zswap/firewall/tailscale harden

## Remaining
1. **Join london-2** as V2 agent (console → fix SSH → `join-london-2.sh`)
2. **Cancel VPS subscriptions** after multi-day soak — amsterdam / california / california-2 only
3. Optional: remove retired hosts from Tailscale
4. Optional: bazzite SELinux Enforcing (after quiet AVC soak)
5. Optional: enable OS SELinux on london-3 + reboot

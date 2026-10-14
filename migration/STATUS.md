# Migration status (2026-10-14)

## V2 cluster baseline — UP
- Nodes: **bazzite** (control-plane, SQLite) + **k3s-london-1** + **k3s-london-3** — Ready
- Disk: `/var/mnt/data/{downloads,local-path,migrate}` (symlink `/var/mnt/downloads` → downloads)
- Networking: Tailscale as `node-ip` + `flannel-iface` (fixes ClusterIP hairpin)
- **local-path** → `/var/mnt/data/local-path` on bazzite (smoke PVC verified on `/dev/sda`)
- **Sealed Secrets** controller up; restored keys registered (`sealed-secrets-key*`)
- CoreDNS Ready

## Exports available
- 33 PVC restic snapshots + sealed-secrets in B2
- Offline: `~/dev/homelab-migration-secrets/`
- On disk: `/var/mnt/data/migrate/`

## Next
1. Install Reloader + Cloudflare tunnel + ArgoCD (point at `v2`)
2. Restore Tier0/Tier1 PVCs from restic into local-path
3. Sync apps; smoke-test
4. Decommission old V1 nodes after soak

## Kubeconfig
- On server: `/etc/rancher/k3s/k3s.yaml`
- Copy under `/var/mnt/data/migrate/k3s.yaml` (TS server URL)

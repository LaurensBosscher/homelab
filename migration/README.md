# Homelab V2 migration notes

Cutover is **complete**. Living status: [`STATUS.md`](STATUS.md). Plan/history: [`../PLAN.md`](../PLAN.md).

Retired V1 manifests (Longhorn storage classes, regional cloudflared) live under `retired/` for reference only — not applied by ArgoCD.

Secrets and restic helpers stay **outside** git (on bazzite under `/var/mnt/data/migrate/` and the offline secrets dir).

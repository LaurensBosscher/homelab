# Homelab V2 migration working dir

Operational notes for the in-place cutover. Secrets live **outside** git:

- Offline secrets: `~/dev/homelab-migration-secrets/`
- On `k3s-london-1`: `/root/homelab-migrate/`
- Local durable stage on bazzite media disk: `/mnt/downloads/_migrate/`
- Restic repo: `s3:https://s3.eu-central-003.backblazeb2.com/longhorn-backups-ay76/restic-homelab-migrate`

## Helpers on london-1

```bash
ssh -i ~/.ssh/id_rsa_kubernetes root@100.79.162.75
/root/homelab-migrate/bin/export-pvc.sh <ns> <pvc> [deploy-to-scale]
/root/homelab-migrate/bin/dump-postgres.sh <ns> <deploy> <db> <user> <tag>
```

`export-pvc.sh` scales the deploy down (optional), attaches the PVC on **bazzite**, writes `/mnt/downloads/_migrate/pvc/<ns>/<pvc>.tar`, and `restic backup`s the mount to B2, then scales back up.

## Status

See `INVENTORY.md` and `PLAN.md` at repo root.

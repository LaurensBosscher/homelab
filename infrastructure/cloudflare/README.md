# Homelab Cloudflare (Pulumi)

Python Pulumi project that **adopts the live personal Cloudflare account**
(`1ce5b40c4616a803216dff853ef6bc81`) so future zone / DNS / tunnel changes can
be reviewed with `pulumi preview` and applied with `pulumi up`.

Pattern mirrors Savex `infrastructure/cloudflare`: declarative inline resources
with per-resource `import_` IDs, plus **SOPS** for the API token.

## Live inventory (imported)

| Area | Notes |
|---|---|
| Account | Laurens@laurensbosscher.nl's Account |
| Zones | `bosscher.ch`, `bossscher.org`, `laurensbosscher.nl` |
| DNS | All live records (A/AAAA/CNAME/MX/TXT) under those zones |
| Tunnels | `k8s-tunnel`, `openstick` (tunnel objects only; ingress still driven by `cloudflare/tunnels/*.yml` + GH Actions for now) |

## Auth

1. API token lives in `secrets.enc.env` (SOPS; recipients = Laurens GitHub SSH keys in repo-root `.sops.yaml`).
2. `scripts/pulumi_run.py` decrypts via `sops -d` into process env only.
3. Optional override: `local_secrets.env` (gitignored) wins over encrypted values.

```bash
# Edit encrypted secrets (never writes plaintext to git):
sops --input-type dotenv --output-type dotenv infrastructure/cloudflare/secrets.enc.env

# Preview / apply:
cd infrastructure/cloudflare
./pulumi_preview.sh
./pulumi_up.sh
```

Required keys:

```dotenv
CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_ACCOUNT_ID=1ce5b40c4616a803216dff853ef6bc81
```

## State backend

Local file backend at `infrastructure/cloudflare/.pulumi-state/` (gitignored).
No AWS/S3 required for this personal stack.

## Layout

```
infrastructure/cloudflare/
  Pulumi.yaml
  Pulumi.homelab.yaml
  secrets.enc.env          # SOPS ciphertext (committed)
  local_secrets.env        # optional plaintext overlay (gitignored)
  __main__.py
  pulumi_preview.sh
  pulumi_up.sh
  scripts/
    infra_secrets.py
    pulumi_run.py
  homelab_cloudflare/
    helpers.py
    zones.py
    dns.py
    tunnels.py
    inventory/tunnels.py
```

## Notes

- First successful `pulumi up` **imports** live resources (no recreate) while
  `homelab-cloudflare:importExisting` is `true`.
- Tunnel **ingress / public hostnames** remain in `cloudflare/tunnels/config.yml`
  (+ OpenStick companion) until those are migrated into Pulumi configs.
- Do **not** commit `credentials.env` or decrypted dotenv files.

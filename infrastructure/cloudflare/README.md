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
| Zone settings | TLS 1.2 minimum, HTTPS redirect, Rocket Loader off. SSL mode stays live: `full` / `full` / `flexible` (strict breaks `www` and `direct`) |
| DNSSEC | On. `bossscher.org` and `laurensbosscher.nl` stay pending until the registrar publishes the DS |
| Precursor | `min-friction` on all three zones |
| Bot Management | AI bots blocked. Fight Mode only on `laurensbosscher.nl` (app/media zones stay off) |
| Tiered Cache | Smart Tiered Cache on for all three zones |
| Cache Rules | Static extensions cached. Video/HLS/DASH extensions explicitly bypassed (Free-plan ToS) |
| DMARC Management | On for all three zones. `_dmarc` TXT keeps the existing policy and adds the Cloudflare RUA |
| R2 | `k3s-etcd`, `k3s-longhorn`, `save-games` (objects not managed) |
| DNS | All live records (A/AAAA/CNAME/MX/TXT) under those zones |
| Tunnels | `k8s-tunnel`, `openstick` objects, plus health and create/delete email alerts. Ingress stays in `cloudflare/tunnels/*.yml` + GH Actions |
| Not in this stack | Entra, device posture, WARP, split tunnel, Gateway, Access for Infrastructure. The `alameda` Worker (D1/KV and secret bindings) stays dashboard-managed |

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
    cloudflare_api.py
    zones.py
    bot_management.py
    dmarc_management.py
    dns.py
    r2.py
    tunnels.py
    notifications.py
    inventory/tunnels.py
```

## Notes

- First successful `pulumi up` **imports** live resources (no recreate) while
  `homelab-cloudflare:importExisting` is `true`.
- Tunnel **ingress / public hostnames** remain in `cloudflare/tunnels/config.yml`
  (+ OpenStick companion). Pulumi does not also own `ZeroTrustTunnelCloudflaredConfig`,
  or it would fight the GitHub Action.
- Cache rules never cache video extensions (`mp4`, `mkv`, `webm`, HLS/DASH, and the
  rest of the list in `zones.py`). The Free plan is not Cloudflare Stream.
- Do **not** commit `credentials.env` or decrypted dotenv files.

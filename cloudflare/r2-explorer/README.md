# R2 Explorer

Read-write Cloudflare Worker for the `r2-explorer` bucket, served at
`https://files.bosscher.ch`.

Access is the Pulumi app `files.bosscher.ch`. That exact hostname overrides
`*.bosscher.ch` and allows only `ACCESS_EMAIL_LAURENS`. The Worker also checks
the Access JWT (`cfAccessTeamName = laurens-bosscher`). `workers.dev` is off.

There is no GitHub Action. Deploy from this directory after the bucket exists:

```bash
npm install
npx wrangler deploy
```

`wrangler deploy` uses `CLOUDFLARE_API_TOKEN` from the environment. The same
token as `infrastructure/cloudflare/secrets.enc.env` can deploy it. The custom
domain record is created by Wrangler and is not in the Pulumi DNS inventory.

Share links (`/share/*`) are not exempt from Access. Do not add a bypass for
that path.

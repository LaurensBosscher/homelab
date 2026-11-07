# blog.bosscher.ch

AstroPaper blog served as a Cloudflare Worker custom domain.

Theme: [satnaing/astro-paper](https://github.com/satnaing/astro-paper) (MIT).

## Local

```bash
cd cloudflare/blog
pnpm install
pnpm dev
```

## Deploy

Pushes that touch `cloudflare/blog/**` run `.github/workflows/deploy-blog.yml`.

The workflow uses environment `cloudflare update tunnels & dns` and the
account API token `Github CI/CD tunnels dns workers` (shared with tunnel
updates and `deploy-resume.yml`). That token needs **Workers Scripts Write**
/ **Workers Editor** plus tunnel/DNS/routes scopes, and must **not** be
IP-restricted (GitHub runners are not home). The Pulumi token in
`secrets.enc.env` is home-IP-only and cannot deploy from Actions.

Manual (from an allowed IP, e.g. home with the Pulumi token):

```bash
cd cloudflare/blog
pnpm install
pnpm build
CLOUDFLARE_API_TOKEN=... pnpm exec wrangler deploy
```

Wrangler creates the `blog.bosscher.ch` DNS record. Keep it out of Pulumi
`dns.py` (same pattern as `files.bosscher.ch`).

Access: exact hostname app `blog.bosscher.ch` with `Allow Everyone` so it is not behind `*.bosscher.ch` login.

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

Manual:

```bash
cd cloudflare/blog
pnpm install
pnpm build
CLOUDFLARE_API_TOKEN=... pnpm exec wrangler deploy
```

Wrangler creates the `blog.bosscher.ch` DNS record. Keep it out of Pulumi `dns.py` (same pattern as `files.bosscher.ch`).

Access: exact hostname app `blog.bosscher.ch` with `Allow Everyone` so it is not behind `*.bosscher.ch` login.

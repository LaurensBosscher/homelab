# Resume (bosscher.ch / laurensbosscher.nl)

Static HTML résumé served as a Cloudflare Worker with custom domains on:

- `bosscher.ch`
- `www.bosscher.ch`
- `laurensbosscher.nl`
- `www.laurensbosscher.nl`

Source lives in `public/` (HTML, CSS, photo, PDF).

## Local

```bash
cd cloudflare/resume
npm install
npm run dev
```

## Deploy

Pushes that touch `cloudflare/resume/**` run `.github/workflows/deploy-resume.yml`.

Manual:

```bash
cd cloudflare/resume
npm install
CLOUDFLARE_API_TOKEN=... npm run deploy
```

Wrangler owns the custom-domain DNS records. Keep those apex/`www` names out of Pulumi `dns.py` (same pattern as `blog.bosscher.ch` and `files.bosscher.ch`).

Access: the exact-hostname app `bosscher.ch` already uses `Allow Everyone` for the apex and `www` hosts on both zones, so the résumé stays public (not behind `*.bosscher.ch` login).

## Update content

Edit files under `cloudflare/resume/public/`, then push to `main` (or run the workflow / `npm run deploy`).

# OpenClaw image runtime policy

## Node.js version — do not pin in this repo

The Node runtime ships **inside the upstream base image** (`ghcr.io/openclaw/openclaw:<tag>`).
This repo pins **no Node version anywhere**, and that is intentional:

- The base image authors select a Node version that matches each OpenClaw release.
- Bumping the OpenClaw tag (the recurring three-site bump, see the
  `homelab-app-deploy` skill) automatically brings the right Node along.
- Manually overriding Node here would desync from the upstream image's
  SQLite/storage expectations and can cause silent data truncation.

**Compatibility floors (since OpenClaw 2026.9.3):** Node ≥ 24.16.0 on the 24.x
line, or ≥ 26.1.0 (26 recommended). Node 22, 25, and earlier 24.x/26.x builds
are unsupported. Current runtime in the deployed image: Node 24.19.0 — compliant.

**If a future release needs a newer Node than our deployed image provides:**
do not patch Node into this Dockerfile. Bump the `ghcr.io/openclaw/openclaw`
base tag (which carries the matching Node), then run the normal three-site bump:
Dockerfile `FROM`, `.github/workflows/build-openclaw.yml` metadata tag, and both
`image:` sites in `apps/openclaw/openclaw-deployment.yml`.

## Bun — installer only, never the runtime

Bun (`oven/bun`) is used in `openclaw/Dockerfile` solely as a **fast package
installer** for the bundled agent CLIs (`omp`, `opencode`, `wrangler`,
`agent-browser`, …). OpenClaw itself requires Node.js and cannot run on Bun.
Do not replace the Node runtime with Bun.

## Reference

- Node requirements: https://docs.openclaw.ai/install/node
- SQLite safety floors: https://docs.openclaw.ai/install/node-compatibility

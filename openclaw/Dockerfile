FROM ghcr.io/astral-sh/uv:0.11.28 AS uv
FROM oven/bun:1.3.14 AS bun

FROM ghcr.io/openclaw/openclaw:2026.6.11

USER root

COPY --from=uv /uv /uvx /usr/local/bin/
COPY --from=bun /usr/local/bin/bun /usr/local/bin/bun

RUN if command -v apk >/dev/null; then \
      apk add --no-cache bind-tools curl git github-cli jq kubectl openssh-client ripgrep; \
    elif command -v apt-get >/dev/null; then \
      apt-get update && \
      DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends curl dnsutils git jq kubernetes-client openssh-client ripgrep && \
      curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
      echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
      apt-get update && \
      apt-get install -y gh=2.96.0 && \
      rm -rf /var/lib/apt/lists/*; \
    else \
      echo "Unsupported package manager" >&2; \
      exit 1; \
    fi

ENV UV_TOOL_BIN_DIR=/usr/local/bin

RUN uv tool install ruff==0.15.21 && \
    uv tool install mypy==2.2.0 && \
    uv cache clean

WORKDIR /opt/openclaw-tools

RUN bun install opencode-ai@1.17.18 oh-my-opencode@4.16.3 @ast-grep/cli@0.44.1 wrangler@4.110.0 && \
    ln -s /opt/openclaw-tools/node_modules/.bin/opencode /usr/local/bin/opencode && \
    ln -s /opt/openclaw-tools/node_modules/.bin/oh-my-openagent /usr/local/bin/oh-my-openagent && \
    ln -s /opt/openclaw-tools/node_modules/.bin/sg /usr/local/bin/sg && \
    ln -s /opt/openclaw-tools/node_modules/.bin/ast-grep /usr/local/bin/ast-grep && \
    ln -s /opt/openclaw-tools/node_modules/.bin/wrangler /usr/local/bin/wrangler && \
    rm -rf /root/.bun/install/cache

ENV NODE_PATH=/opt/openclaw-tools/node_modules

USER node

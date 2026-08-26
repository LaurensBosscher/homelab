FROM ghcr.io/astral-sh/uv:0.12.6 AS uv
FROM oven/bun:1.4.0 AS bun

FROM ghcr.io/openclaw/openclaw:2026.7.1-2

USER root

COPY --from=uv /uv /uvx /usr/local/bin/
COPY --from=bun /usr/local/bin/bun /usr/local/bin/bun

RUN if command -v apk >/dev/null; then \
      apk add --no-cache bind-tools curl git github-cli jq kubectl openssh-client ripgrep; \
    elif command -v apt-get >/dev/null; then \
      apt-get update && \
      # Install gnupg first (needed for gpg --dearmor key imports)
      DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gnupg ca-certificates && \
      # Add Brave browser apt repo (ad-blocking, replaces chromium)
      curl -fsSL https://brave-browser-apt-release.s3.brave.com/brave-core.asc | gpg --dearmor -o /usr/share/keyrings/brave-browser-archive-keyring.gpg && \
      echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg] https://brave-browser-apt-release.s3.brave.com/ stable main" | tee /etc/apt/sources.list.d/brave-browser.list > /dev/null && \
      # Add GitHub CLI apt repo
      curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
      echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
      # Refresh package index with both new repos, then install everything
      apt-get update && \
      DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends brave-browser curl dnsutils ffmpeg git jq kubernetes-client openssh-client ripgrep gh=2.97.0 && \
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

# omp: 17.3.5 ships GLM-5.3 in the model catalog (z.AI provider,
# default model, 1M context, low/high/max reasoning ladder)
RUN bun install agent-browser opencode-ai@1.17.18 oh-my-opencode@4.16.3 @ast-grep/cli@0.44.1 wrangler@4.110.0 @googleworkspace/cli@0.8.0 @steipete/summarize@0.21.6 @oh-my-pi/pi-coding-agent@17.3.5 && \
    ln -s /opt/openclaw-tools/node_modules/.bin/opencode /usr/local/bin/opencode && \
    ln -s /opt/openclaw-tools/node_modules/.bin/oh-my-openagent /usr/local/bin/oh-my-openagent && \
    ln -s /opt/openclaw-tools/node_modules/.bin/sg /usr/local/bin/sg && \
    ln -s /opt/openclaw-tools/node_modules/.bin/ast-grep /usr/local/bin/ast-grep && \
    ln -s /opt/openclaw-tools/node_modules/.bin/wrangler /usr/local/bin/wrangler && \
    ln -s /opt/openclaw-tools/node_modules/.bin/gws /usr/local/bin/gog && \
    ln -s /opt/openclaw-tools/node_modules/.bin/summarize /usr/local/bin/summarize && \
    ln -s /opt/openclaw-tools/node_modules/.bin/agent-browser /usr/local/bin/agent-browser && \
    ln -s /opt/openclaw-tools/node_modules/.bin/omp /usr/local/bin/omp && \
    chmod +x /opt/openclaw-tools/node_modules/agent-browser/bin/agent-browser-linux-x64 && \
    rm -rf /root/.bun/install/cache /root/.npm /tmp/npm-*

# Remove QMD remnants from the base image (replaced by builtin sqlite-vec engine)
RUN rm -rf /home/node/node_modules/@tobilu/qmd \
        /home/node/node_modules/node-llama-cpp \
        /home/node/.config/qmd

# Copy Brave ad-block preferences script
COPY brave-preferences.sh /usr/local/bin/brave-preferences.sh
RUN chmod +x /usr/local/bin/brave-preferences.sh

# Pre-download Moonshine Voice tiny model for on-device ASR
# Tiny streaming: 34M params, 12% WER, ~69ms on Linux x86 — fast fallback, small footprint
# Model arch IDs: tiny_streaming=2, base_streaming=3, small_streaming=4, medium_streaming=5
RUN uv venv /tmp/moonshine-venv && \
    VIRTUAL_ENV=/tmp/moonshine-venv uv pip install moonshine-voice && \
    mkdir -p /opt/moonshine-models && \
    MOONSHINE_VOICE_CACHE=/opt/moonshine-models /tmp/moonshine-venv/bin/moonshine-voice download --stt --language en --model-arch 2 && \
    rm -rf /tmp/moonshine-venv && \
    uv cache clean

# Copy voice transcription CLI script
COPY scripts/transcribe.py /usr/local/bin/transcribe.py
RUN chmod +x /usr/local/bin/transcribe.py

ENV NODE_PATH=/opt/openclaw-tools/node_modules
ENV CHROME_PATH=/usr/bin/brave-browser
ENV MOONSHINE_VOICE_CACHE=/opt/moonshine-models

USER node

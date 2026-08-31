FROM ghcr.io/astral-sh/uv:0.12.7 AS uv

FROM python:3.13-slim

COPY --from=uv /uv /uvx /usr/local/bin/

# MUST precede `uv tool install` or the binary lands in root's ~/.local/bin
# and the container fails with "nanobot: executable file not found in $PATH".
ENV UV_TOOL_BIN_DIR=/usr/local/bin

# nanobot-ai from PyPI (stable track; update by bumping this install)
RUN uv tool install nanobot-ai \
    && useradd --create-home --uid 1000 nanobot

# State (config/sessions/memory/cron) lives in /home/nanobot/.nanobot on the PVC;
# workspace backup (claw-scripts) is restored manually into /home/nanobot/workspace.
USER nanobot
WORKDIR /home/nanobot
EXPOSE 8765

# Flags verified against `nanobot webui --help` (0.3.0): there is NO --host;
# --no-open (headless), --yes (apply safe defaults without prompting),
# -w pins the workspace for the manual claw-scripts restore.
# Docs: WebUI/WebSocket serves on :8765 (only the health port is loopback-only).
CMD ["nanobot", "webui", "--no-open", "--yes", "--port", "8765", "-w", "/home/nanobot/workspace"]

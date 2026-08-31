FROM ghcr.io/astral-sh/uv:0.12.7 AS uv

FROM python:3.13-slim

COPY --from=uv /uv /uvx /usr/local/bin/

# nanobot-ai from PyPI (stable track; update by bumping this install)
RUN uv tool install nanobot-ai \
    && useradd --create-home --uid 1000 nanobot

# State (config/sessions/memory/cron) lives in /home/nanobot/.nanobot on the PVC;
# workspace backup (claw-scripts) is restored manually into /home/nanobot/workspace.
ENV UV_TOOL_BIN_DIR=/usr/local/bin
USER nanobot
WORKDIR /home/nanobot
EXPOSE 8765

# WebUI on all interfaces for the Service; default port 8765 per nanobot docs.
# NOTE: if `nanobot webui` rejects these flags, check `nanobot webui --help`
# on the pod and adjust here (canary iteration expected).
CMD ["nanobot", "webui", "--host", "0.0.0.0", "--port", "8765"]

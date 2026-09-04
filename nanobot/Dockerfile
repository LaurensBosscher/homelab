FROM ghcr.io/astral-sh/uv:0.12.7 AS uv

FROM python:3.14-slim

COPY --from=uv /uv /uvx /usr/local/bin/

# MUST precede `uv tool install`:
# - UV_TOOL_BIN_DIR puts the executable shim on the default PATH
# - UV_TOOL_DIR keeps the venv OUT of /root: the shim is a python script whose
#   shebang points into the venv (verified: #!<UV_TOOL_DIR>/nanobot-ai/bin/python).
#   /root is mode 700, so a non-root runtime user cannot resolve an interpreter
#   under it -> runc fails with the SAME "executable file not found in $PATH"
#   as a missing binary (why 0.3.0-2 crashed despite the shim being on PATH).
ENV UV_TOOL_DIR=/opt/uv-tools \
    UV_TOOL_BIN_DIR=/usr/local/bin

# nanobot-ai from PyPI (stable track; update by bumping this install).
# Build-time guard: su-exec as the runtime user and run the binary — this
# class of bug now fails the CI build instead of shipping a crashloop.
RUN useradd --create-home --uid 1000 nanobot \
    && uv tool install nanobot-ai \
    && chmod -R a+rX /opt/uv-tools \
    && su nanobot -s /bin/sh -c 'nanobot --version'

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

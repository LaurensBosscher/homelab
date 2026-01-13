FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

FROM python:3.14-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends nmap && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 django && \
    mkdir -p /app /data && \
    chown -R django:django /app /data

WORKDIR /app

COPY --from=builder --chown=django:django /app/.venv /app/.venv

COPY --chown=django:django . .

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=portwatcher.settings

COPY --chown=django:django scripts/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

USER django

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "portwatcher.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]

FROM ghcr.io/astral-sh/uv:0.11.6 AS uv
FROM node:22-bookworm-slim AS node
FROM python:3.12-slim-bookworm
COPY --from=uv /uv /usr/local/bin/uv
COPY --from=node /usr/local/bin/node /usr/local/bin/node
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 10001 clipdock && mkdir -p /app/data && chown -R clipdock:clipdock /app
WORKDIR /app
COPY --chown=clipdock:clipdock pyproject.toml uv.lock ./
USER clipdock
RUN uv sync --frozen --no-dev
COPY --chown=clipdock:clipdock clipdock ./clipdock
COPY --chown=clipdock:clipdock main.py ./main.py
ENV CLIPDOCK_DATA_DIR=/app/data PYTHONUNBUFFERED=1 PATH=/app/.venv/bin:$PATH
EXPOSE 8000
# Exactly one process; the service also enforces a directory lock.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --no-access-log"]

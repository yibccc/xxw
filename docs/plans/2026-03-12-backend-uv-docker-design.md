# Backend UV Docker Design

**Date:** 2026-03-12

**Goal:** Switch `Dockerfile.backend` from `pip`-based installation to a standard single-stage `uv` deployment flow while preserving the existing startup sequence.

## Scope

- Keep the base image as `python:3.11-slim`
- Install `uv` by copying the binary from the official `uv` image
- Install production dependencies from `pyproject.toml` and `uv.lock`
- Preserve the startup flow: wait for MySQL, run Alembic migrations, then start Flask
- Keep `docker-compose.yml` unchanged

## Design

- Use a single-stage image to keep the Dockerfile straightforward
- Pin the `uv` image version used for binary copy
- Run `uv sync --locked --no-dev --no-install-project` so the lockfile remains the source of truth and dev dependencies stay out of the runtime image
- Add `/app/.venv/bin` to `PATH` so `uv run` and direct Python execution both resolve consistently
- Copy the files actually needed at runtime:
  - `pyproject.toml`
  - `uv.lock`
  - `src/`
  - `main.py`
  - `alembic.ini`
  - `alembic/`
  - `.env.production`

## Notes

- The previous Dockerfile did not copy `main.py` or `alembic/`, even though the container command depends on both. This change fixes that runtime gap as part of the `uv` migration.
- Healthcheck behavior stays the same.

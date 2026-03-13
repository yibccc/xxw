# Nginx Gunicorn Compose Design

**Date:** 2026-03-13

**Goal:** Replace the public Flask development server entrypoint in Docker Compose with an `nginx -> gunicorn -> Flask` chain while keeping the external access URL as `http://<host>:5000`.

## Scope

- Add an `nginx` service that listens on container port `5000`
- Keep external access on host port `5000`
- Stop exposing the backend container directly to the host
- Replace the backend runtime server from `app.run()` to `gunicorn`
- Preserve the existing startup flow: wait for MySQL, run Alembic migrations, then serve the Flask app
- Keep the backend app and API paths unchanged

## Design

- Docker Compose will have three services: `mysql`, `backend`, and `nginx`
- `nginx` will be the only public HTTP entrypoint and will publish `5000:5000`
- `backend` will remain on the internal Compose network and expose port `5000` only to peer containers
- `backend` will run `gunicorn` with a single worker and multiple threads so the current single-process runtime behavior is preserved for the scheduler and SSE background services
- A dedicated WSGI module will initialize the Flask app and runtime services for the gunicorn worker process
- `nginx` will proxy `/`, `/api/`, and `/health` to the backend and forward the standard proxy headers

## Key Constraints

- The current runtime bootstrap starts background services inside the application process. Running multiple gunicorn workers would duplicate these background services.
- Because of that, the initial deployment should use `--workers 1` and only scale after the runtime architecture is separated from the web worker lifecycle.
- External traffic remains plain HTTP on port `5000`; TLS termination is intentionally out of scope for this change.

## Files

- Modify: `docker-compose.yml`
- Modify: `Dockerfile.backend`
- Modify: `docker/backend-entrypoint.sh`
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Modify: `README.md`
- Create: `docker/nginx/default.conf`
- Create: `src/timerservice/wsgi.py`

## Verification

- `docker compose config` should succeed
- `docker compose build backend nginx` should succeed
- `docker compose up -d` should expose only the `nginx` service on host port `5000`
- `curl http://127.0.0.1:5000/health` should return `200`
- `docker compose logs nginx backend` should show requests flowing through `nginx` instead of the Flask development server

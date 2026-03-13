# Nginx Gunicorn Compose Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the direct public Flask container in Docker Compose with an `nginx -> gunicorn -> Flask` deployment that still serves the app on `http://<host>:5000`.

**Architecture:** Add an `nginx` service that is the only public listener on port `5000`, proxy requests to the backend over the internal Compose network, and switch the backend process from `uv run python main.py` to `gunicorn`. Keep gunicorn at one worker so runtime background services remain single-process.

**Tech Stack:** Docker Compose, nginx, gunicorn, Python 3.11, uv, Flask, Alembic

---

### Task 1: Add the reverse proxy layer

**Files:**
- Modify: `docker-compose.yml`
- Create: `docker/nginx/default.conf`

**Step 1: Write the failing test**

This is a container configuration change. Verification is a Compose config/render check rather than a unit test.

**Step 2: Run verification to confirm the current chain is wrong**

Run: `docker compose config`
Expected: The current rendered config shows `backend` publishing host port `5000` directly and no reverse proxy service exists.

**Step 3: Write minimal implementation**

- Remove the top-level obsolete `version` key
- Remove the host port mapping from `backend`
- Add `nginx` as a new service
- Publish only `nginx` host port `5000:5000`
- Add an nginx config that listens on `5000` and proxies to `backend:5000`

**Step 4: Run verification to confirm the Compose config is valid**

Run: `docker compose config`
Expected: Exit code `0` and only `nginx` publishes host port `5000`

### Task 2: Switch backend runtime to gunicorn

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Modify: `docker/backend-entrypoint.sh`
- Create: `src/timerservice/wsgi.py`

**Step 1: Write the failing test**

This is a runtime packaging change. Verification is a dependency lock update and container build check rather than a unit test.

**Step 2: Run verification to confirm the current runtime still uses the development server**

Run: inspect `docker/backend-entrypoint.sh` and `main.py`
Expected: startup ends with `uv run python main.py`, which uses Flask `app.run()`

**Step 3: Write minimal implementation**

- Add `gunicorn` to runtime dependencies
- Update `uv.lock`
- Create a WSGI module that exposes `app`
- Start runtime services from that module
- Change the backend entrypoint to execute gunicorn on `0.0.0.0:5000` with `--workers 1`

**Step 4: Run verification to confirm the backend image can be built**

Run: `docker compose build backend`
Expected: Exit code `0`

### Task 3: Update image wiring and docs

**Files:**
- Modify: `Dockerfile.backend`
- Modify: `README.md`

**Step 1: Write the failing test**

This is a documentation and image wiring change. Verification is a build and config review rather than a unit test.

**Step 2: Run verification to confirm the image and docs lag the new architecture**

Run: inspect `Dockerfile.backend` and `README.md`
Expected: backend image copies no nginx config and docs still describe direct Flask exposure

**Step 3: Write minimal implementation**

- Ensure the backend image still exposes container port `5000`
- Keep the healthcheck pointed at `http://localhost:5000/health`
- Update README deployment instructions to describe the new proxy chain and port exposure

**Step 4: Run verification to confirm docs and image align**

Run: `docker compose config`
Expected: README instructions match the rendered service topology

### Task 4: Verify the final deployment shape

**Files:**
- Modify: none

**Step 1: Run configuration verification**

Run: `docker compose config`
Expected: Exit code `0`

**Step 2: Run build verification**

Run: `docker compose build backend nginx`
Expected: Exit code `0`

**Step 3: Optional runtime verification**

Run: `docker compose up -d`
Expected: `nginx` is the only public port publisher on `5000`, and `curl http://127.0.0.1:5000/health` returns `200`

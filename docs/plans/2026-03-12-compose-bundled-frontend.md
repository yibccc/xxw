# Compose Bundled Frontend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the Docker Compose deployment chain by removing the standalone frontend service and baking the frontend build into the backend image.

**Architecture:** Build the Vue frontend in a Node stage inside `Dockerfile.backend`, copy the built assets into `src/timerservice/static`, and let Flask serve them from the backend container. Simplify `docker-compose.yml` to just `mysql` and `backend`, which removes the broken cross-container static file handoff.

**Tech Stack:** Docker Compose, Docker multi-stage builds, Node.js, Vite, Python 3.11, uv, Flask

---

### Task 1: Bundle frontend build into backend image

**Files:**
- Modify: `Dockerfile.backend`

**Step 1: Write the failing test**

This is a Docker configuration change. Verification is a build/config check rather than a unit test.

**Step 2: Run verification to confirm the old chain is invalid**

Run: inspect `Dockerfile.frontend`, `docker-compose.yml`, and `frontend/vite.config.js`
Expected: frontend output path, runtime copy path, and backend static mount do not align

**Step 3: Write minimal implementation**

- Add a Node build stage to `Dockerfile.backend`
- Install frontend deps with `npm ci`
- Build with an explicit `--outDir dist`
- Copy built assets into `./src/timerservice/static/` in the backend image

**Step 4: Run verification to confirm the new backend image definition is coherent**

Run: `git diff -- Dockerfile.backend`
Expected: frontend assets are built and copied within the backend image

**Step 5: Commit**

```bash
git add Dockerfile.backend docs/plans/2026-03-12-compose-bundled-frontend.md
git commit -m "build: bundle frontend into backend image"
```

### Task 2: Simplify Compose runtime graph

**Files:**
- Modify: `docker-compose.yml`
- Delete: `Dockerfile.frontend`

**Step 1: Write the failing test**

This is a Compose configuration change. Verification is a config diff/check rather than a unit test.

**Step 2: Run verification to confirm the old graph is broken**

Run: inspect `docker-compose.yml`
Expected: standalone `frontend` service writes to a different storage target than the backend reads

**Step 3: Write minimal implementation**

- Remove the `frontend` service
- Remove the `frontend_static` named volume and backend static mount
- Keep `mysql` and `backend` only
- Remove `Dockerfile.frontend` because it is no longer referenced

**Step 4: Run verification to confirm the graph is simplified**

Run: `git diff -- docker-compose.yml Dockerfile.frontend`
Expected: only `mysql` and `backend` remain

**Step 5: Commit**

```bash
git add docker-compose.yml Dockerfile.frontend docs/plans/2026-03-12-compose-bundled-frontend.md
git commit -m "chore: remove standalone frontend compose service"
```

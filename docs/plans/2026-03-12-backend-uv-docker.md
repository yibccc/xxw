# Backend UV Docker Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate the backend Docker image from `pip` installation to a standard single-stage `uv` workflow without changing runtime behavior.

**Architecture:** Keep `python:3.11-slim` as the runtime base image, copy in the `uv` binary from the official `uv` image, install locked production dependencies into the project virtual environment, then run the existing wait-for-MySQL and startup chain via `uv run`.

**Tech Stack:** Docker, Python 3.11, uv, Flask, Alembic

---

### Task 1: Update backend image build to use uv

**Files:**
- Modify: `Dockerfile.backend`

**Step 1: Write the failing test**

This is a Docker configuration change. Verification is a container build, not a unit test.

**Step 2: Run verification to confirm current behavior is broken or outdated**

Run: `docker build -f Dockerfile.backend .`
Expected: The old image still uses `pip`, and may fail at runtime because required runtime files are missing from the image.

**Step 3: Write minimal implementation**

- Copy `uv` into the image
- Copy `uv.lock`
- Replace `pip install -e .` with `uv sync --locked --no-dev --no-install-project`
- Copy runtime files required by the startup command
- Change Alembic and app startup commands to `uv run ...`

**Step 4: Run verification to confirm the build succeeds**

Run: `docker build -f Dockerfile.backend .`
Expected: Build exits with code `0`

**Step 5: Commit**

```bash
git add Dockerfile.backend docs/plans/2026-03-12-backend-uv-docker-design.md docs/plans/2026-03-12-backend-uv-docker.md
git commit -m "build: migrate backend Docker image to uv"
```

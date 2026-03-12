# UI And Runtime Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor backend runtime startup and frontend state/UI structure without changing database behavior.

**Architecture:** Backend side effects move out of `create_app()` into an explicit runtime bootstrap, while auth and SSE paths are tightened and covered with focused tests. Frontend state moves into singleton composables and reusable UI components so routing, notifications, unread counts, and SSE connection behavior are consistent across pages.

**Tech Stack:** Flask, pytest, Vue 3, Vue Router, Axios, Vite

---

### Task 1: Cover auth and SSE behavior with focused backend tests

**Files:**
- Modify: `tests/test_auth.py`
- Create: `tests/test_sse.py`

**Step 1: Write the failing test**

- Add a test proving `/api/auth/me` still works via the shared auth decorator path
- Add a test proving `/api/stream?token=...` is rejected

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_auth.py tests/test_sse.py -q`
Expected: at least the SSE query-token test fails against current behavior

**Step 3: Write minimal implementation**

- Reuse `@require_auth` in the auth route
- Remove query token fallback from the SSE route

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_auth.py tests/test_sse.py -q`
Expected: all selected tests pass

**Step 5: Commit**

```bash
git add tests/test_auth.py tests/test_sse.py src/timerservice/auth/routes.py src/timerservice/sse/routes.py
git commit -m "refactor: tighten auth and sse handling"
```

### Task 2: Remove backend startup side effects from app creation

**Files:**
- Modify: `src/timerservice/app.py`
- Create: `src/timerservice/runtime.py`
- Modify: `main.py`

**Step 1: Write the failing test**

Use the existing `create_app()` test entrypoint as the contract: app creation should remain usable for tests without starting runtime workers inside the factory.

**Step 2: Run verification to confirm current structure has startup side effects**

Run: inspect `src/timerservice/app.py`
Expected: scheduler and ping startup happen during `create_app()`

**Step 3: Write minimal implementation**

- Move scheduler and ping startup into `runtime.py`
- Call runtime bootstrap from `main.py`
- Keep runtime bootstrap idempotent

**Step 4: Run verification to confirm backend tests still pass**

Run: `uv run pytest tests/test_auth.py tests/test_events.py tests/test_timers.py -q`
Expected: selected backend tests pass

**Step 5: Commit**

```bash
git add src/timerservice/app.py src/timerservice/runtime.py main.py
git commit -m "refactor: isolate backend runtime startup"
```

### Task 3: Introduce lightweight frontend app state and reusable UI components

**Files:**
- Create: `frontend/src/composables/useSession.js`
- Create: `frontend/src/components/ui/AuthCard.vue`
- Create: `frontend/src/components/ui/PageHeader.vue`
- Create: `frontend/src/components/ui/BaseModal.vue`
- Create: `frontend/src/components/ui/ToastStack.vue`
- Modify: `frontend/src/components/SSEClient.js`
- Modify: `frontend/src/services/api.js`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/main.js`
- Modify: `frontend/src/router.js`

**Step 1: Write the failing test**

This frontend refactor is currently verified by build and behavioral checks because no frontend unit test harness exists in the repo.

**Step 2: Run verification to confirm current structure is page-local and duplicated**

Run: inspect `frontend/src/App.vue`, `frontend/src/views/Timers.vue`, `frontend/src/views/Login.vue`, `frontend/src/views/Register.vue`
Expected: SSE, unread count, auth display state, and repeated styles live in page components

**Step 3: Write minimal implementation**

- Add singleton session state and shared login/logout helpers
- Keep one SSE connection at the app shell level
- Add shared modal/toast/form-shell components
- Refine `401` handling in the API layer

**Step 4: Run verification to confirm the frontend still builds**

Run: `npm run build`
Workdir: `frontend`
Expected: build exits with code `0`

**Step 5: Commit**

```bash
git add frontend/src
git commit -m "refactor: centralize frontend session and ui state"
```

### Task 4: Rework page implementations to use the shared state and UI components

**Files:**
- Modify: `frontend/src/views/Login.vue`
- Modify: `frontend/src/views/Register.vue`
- Modify: `frontend/src/views/Timers.vue`
- Modify: `frontend/src/views/Events.vue`
- Modify: `frontend/src/style.css`

**Step 1: Write the failing test**

This task is also verified by build and targeted manual behavior checks because no frontend test runner exists in the repo.

**Step 2: Run verification to confirm current UX problems exist**

Run: inspect page components
Expected: raw `alert`/`confirm`, repeated card styles, and page-local unread state are still present

**Step 3: Write minimal implementation**

- Replace page-local auth actions with shared session helpers
- Replace `alert`/`confirm` with shared toast/modal UI
- Keep timers and events pages aligned to shared layout components
- Update the visual system in `style.css`

**Step 4: Run verification to confirm the frontend build still passes**

Run: `npm run build`
Workdir: `frontend`
Expected: build exits with code `0`

**Step 5: Commit**

```bash
git add frontend/src/views frontend/src/style.css
git commit -m "style: polish frontend pages and shared components"
```

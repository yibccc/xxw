# UI And Runtime Refactor Design

**Date:** 2026-03-13

**Goal:** Improve maintainability and UX across the Flask backend and Vue frontend without changing database models, migrations, or schema behavior.

## Scope

- Keep database tables, ORM models, and Alembic migrations unchanged
- Move backend runtime side effects out of Flask app creation
- Reuse the existing auth decorator for `/api/auth/me`
- Restrict SSE auth to the `Authorization` header
- Add a lightweight frontend app state layer for session, SSE, and unread events
- Replace ad-hoc `alert` and `confirm` flows with reusable UI components
- Unify page layout and visual styling without changing core routes

## Backend Design

- Remove scheduler and SSE ping startup from `create_app()`
- Add an explicit runtime bootstrap function invoked by `main.py`
- Keep test app creation side-effect free
- Reuse `@require_auth` for `/api/auth/me`
- Reject query-string tokens on `/api/stream`

## Frontend Design

- Add a singleton reactive session store for:
  - current user
  - token presence
  - unread event count
  - SSE connection state
  - toast notifications
- Keep a single SSE connection at the app shell level instead of page level
- Update the API layer so login failures stay page-local while expired sessions still log out globally
- Add reusable UI building blocks for:
  - auth card
  - page header
  - modal dialog
  - toast stack
- Refresh the global CSS variables and page styling for a more consistent interface

## Verification

- Run backend pytest coverage for changed auth and SSE behavior
- Run the frontend production build
- Report any gaps that could not be verified in the current environment

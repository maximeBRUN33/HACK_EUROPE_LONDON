# Legacy Atlas - Next Steps

## 1) Security hardening (immediate)

1. Rotate all keys currently present in local `.env` files (`CODEWORDS_API_KEY`, `GEMINI_API_KEY`, and any deprecated provider keys) and revoke old values.
2. Keep `.env` files out of git (already ignored) and run a secret scan before each push.
3. Set `LEGACY_ATLAS_CORS_ORIGINS` explicitly per environment (dev/staging/prod) instead of using permissive defaults.
4. Set TLS verification flags to secure values in production (`*_SSL_VERIFY=1`).

## 2) Production readiness

1. Add auth in front of `/api/repos/*`, `/api/runs/*`, and `/api/copilot/*` endpoints.
2. Add request rate limiting for copilot and scan routes.
3. Add structured audit logs for repo registration, scan starts, and copilot questions.
4. Add Sentry (or equivalent) for backend + frontend error monitoring.

## 3) Reliability and scaling

1. Move job execution from in-process workers to a queue (Celery/RQ/Arq) for stable concurrency.
2. Add retry/backoff policies for external providers (CodeWords, Gemini).
3. Add cleanup TTL for old run artifacts in `data/legacy_atlas.db`.
4. Add health probes for external dependency latency regression alerts.

## 4) Product quality

1. Add smoke E2E tests covering one full scan + graph + copilot flow from the web app.
2. Add visual regression checks for key panels (Process, Data, Risk, Copilot).
3. Improve empty/error states in UI for enrichment and web comparison panels.
4. Add benchmark fixtures for large repositories to track analysis duration and memory.

## 5) Documentation

1. Keep root `README.md` as the single source of truth for setup and architecture.
2. Keep this file as the single delivery follow-up checklist and update it as actions are completed.
3. Add an operations runbook (`apps/api/README.md`) for deploy/rollback/on-call procedures.

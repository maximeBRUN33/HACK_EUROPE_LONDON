# Legacy Atlas API

## Run

```bash
cd apps/api
cp .env.example .env
pip install -e .
uvicorn app.main:app --reload --port 8000
```

The API auto-loads variables from `apps/api/.env` at startup (existing shell env vars still take precedence).

## Endpoints

- `POST /api/repos/register`
- `POST /api/repos/{repo_id}/scan`
- `GET /api/repos/{repo_id}/runs/{run_id}`
- `GET /api/runs/{run_id}/workflow-graph`
- `GET /api/runs/{run_id}/lineage-graph`
- `GET /api/runs/{run_id}/risk-summary`
- `GET /api/runs/{run_id}/node/{node_id}/evidence`
- `GET /api/runs/{run_id}/enrichment`
- `POST /api/copilot/query`
- `GET /api/integrations/mcp/status`
- `POST /api/integrations/codewords/trigger`
- `GET /api/integrations/codewords/result/{request_id}`
- `GET /api/integrations/dust/status`

## Real AST mode

Set `local_path` when calling `POST /api/repos/register` to analyze a local Python clone.
If no local path is available, the API returns fallback synthetic artifacts.

## Async execution

- `POST /api/repos/{repo_id}/scan` queues work and returns immediately.
- Poll `GET /api/repos/{repo_id}/runs/{run_id}` until status reaches `completed` or `failed`.
- `AnalysisRun` includes `current_step`, `progress_pct`, and `error_message`.
- `AnalysisRun.summary` now includes additive sections:
  - `ontology` (entities, capability clusters, inbound/outbound integration counts)
  - `migration` (readiness score, extraction boundaries, impacted modules, rerouting risks)
  - required analysis counters (`analysis_mode`, `workflow_nodes`, `lineage_edges`, `risk_findings`, `files_scanned`, `functions_scanned`, `parse_errors`)
  - `codewords_runtime` (post-analysis workflow trigger/poll status)
- `GET /api/runs/{run_id}/enrichment` returns normalized CodeWords ontology/migration enrichment payload persisted as an artifact.

## Persistence

- Run and artifact data are stored in SQLite at `data/legacy_atlas.db`.

## Environment variables

- `LEGACY_ATLAS_REPO_CACHE`: repository clone cache path.
- `LEGACY_ATLAS_ENABLE_GIT_INGESTION`: `1` (default) to allow clone/fetch, `0` to disable.
- `LEGACY_ATLAS_SYNC_JOBS`: `1` to execute scans inline (test mode).
- `LEGACY_ATLAS_LOG_LEVEL`: runtime logging level (`DEBUG`, `INFO`, `WARNING`, ...).
- `LEGACY_ATLAS_AST_PROGRESS_EVERY`: log AST parser progress every N scanned Python files.
- `LEGACY_ATLAS_CODEWORDS_RUNTIME_HOOK`: `1` (default) to trigger/poll CodeWords runtime after analysis, `0` to disable.
- `CODEWORDS_RUNTIME_BASE_URL`: defaults to MCP CodeWords URL when available.
- `CODEWORDS_API_KEY`: overrides MCP token fallback.
- `CODEWORDS_RUNTIME_SERVICE_ID`: service id used by runtime hook (default `legacy_atlas_post_analysis_v1_8a477024`); this must be the runtime id, not the display title.
- `CODEWORDS_POLL_MAX_ATTEMPTS`: max poll attempts for async runtime job.
- `CODEWORDS_POLL_INTERVAL_SEC`: poll interval in seconds.
- `DUST_API_BASE_URL`: defaults to `https://dust.tt/api/v1`.
- `DUST_WORKSPACE_ID`: required for Dust semantic copilot mode.
- `DUST_API_KEY`: required for Dust semantic copilot mode.
- `DUST_ASSISTANT_CONFIGURATION_ID`: required Dust assistant id for mentions.

## Real-time logs

```bash
cd apps/api
LEGACY_ATLAS_LOG_LEVEL=DEBUG uvicorn app.main:app --reload --port 8000
```

This will print run lifecycle logs (ingestion, AST parsing, graph/risk build, artifact persistence, Dust/CodeWords calls) directly in terminal.

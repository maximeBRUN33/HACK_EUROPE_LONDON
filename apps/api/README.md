# Legacy Atlas API

## Run

```bash
cd apps/api
pip install -e .
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `POST /api/repos/register`
- `POST /api/repos/{repo_id}/scan`
- `GET /api/repos/{repo_id}/runs/{run_id}`
- `GET /api/runs/{run_id}/workflow-graph`
- `GET /api/runs/{run_id}/lineage-graph`
- `GET /api/runs/{run_id}/risk-summary`
- `GET /api/runs/{run_id}/node/{node_id}/evidence`
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

## Persistence

- Run and artifact data are stored in SQLite at `data/legacy_atlas.db`.

## Environment variables

- `LEGACY_ATLAS_REPO_CACHE`: repository clone cache path.
- `LEGACY_ATLAS_ENABLE_GIT_INGESTION`: `1` (default) to allow clone/fetch, `0` to disable.
- `LEGACY_ATLAS_SYNC_JOBS`: `1` to execute scans inline (test mode).
- `CODEWORDS_RUNTIME_BASE_URL`: defaults to MCP CodeWords URL when available.
- `CODEWORDS_API_KEY`: overrides MCP token fallback.
- `DUST_API_BASE_URL`: defaults to `https://dust.tt/api/v1`.
- `DUST_WORKSPACE_ID`: required for Dust semantic copilot mode.
- `DUST_API_KEY`: required for Dust semantic copilot mode.
- `DUST_ASSISTANT_CONFIGURATION_ID`: required Dust assistant id for mentions.

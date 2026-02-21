# Legacy Atlas

Legacy Atlas is an AI-powered legacy software comprehension platform.

This repository now contains the first implementation slice:

- `apps/api`: FastAPI backend with async ingestion/analysis jobs, SQLite-backed persistence, graph APIs, risk summary, and copilot endpoint.
- `apps/web`: React + Vite graph-first UI shell with run progress polling and node evidence drill-down.
- `legacy-atlas-plan`: planning package and execution playbooks.

## Quick start

### 0) Create env files

```bash
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env
```

### 1) Run API

```bash
cd apps/api
pip install -e .
uvicorn app.main:app --reload --port 8000
```

### 2) Run web app

```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) and trigger a repository scan from Mission Control.
For real AST analysis, provide `Local Repo Path` in the UI (pointing to a local clone).

Or use:

```bash
make api-install
make api-run
make web-install
make web-run
```

## Implemented endpoints

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

## Current analyzer modes

- `ast-local`: real Python AST analysis from a local repository path.
- `fallback`: placeholder analysis when no local path is resolvable.

## Async run lifecycle

- `POST /api/repos/{repo_id}/scan` queues a run and returns immediately.
- Frontend polls `GET /api/repos/{repo_id}/runs/{run_id}` for `status`, `current_step`, and `progress_pct`.
- Artifacts persist in SQLite at `data/legacy_atlas.db`.

## Optional env vars

- `LEGACY_ATLAS_REPO_CACHE`: local clone cache directory for Git-based ingestion.
- `LEGACY_ATLAS_ENABLE_GIT_INGESTION`: set to `0` to disable remote clone/fetch ingestion.
- `LEGACY_ATLAS_SYNC_JOBS`: set to `1` to run analysis inline (useful for tests).
- `CODEWORDS_RUNTIME_BASE_URL`: CodeWords runtime base URL.
- `CODEWORDS_API_KEY`: API key for CodeWords runtime.
- `DUST_API_BASE_URL`: Dust API base URL (default `https://dust.tt/api/v1`).
- `DUST_WORKSPACE_ID`: Dust workspace id.
- `DUST_API_KEY`: Dust API key.
- `DUST_ASSISTANT_CONFIGURATION_ID`: Dust assistant configuration id used for semantic copilot responses.

## Tests

```bash
cd apps/api
pip install -e .[dev]
pytest
```

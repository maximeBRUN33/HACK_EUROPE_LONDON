# Legacy Atlas Collaboration Build Guidelines

## 1) Where we are now

- End-to-end MVP is running: repo registration, async scan, workflow graph, lineage graph, risk summary, evidence drill-down, copilot.
- Logging is now in place for ingestion, parsing, analysis pipeline, and integrations.
- `.env` is now auto-loaded from `apps/api/.env` at API startup.
- Integration endpoints for CodeWords and Dust exist.
- Known immediate item: frontend build has an unused variable in `apps/web/src/components/GraphCanvas.tsx` (`NODE_WIDTH`), so frontend owner should clean this first.

## 2) Product pillars locked for this collaboration

Both roles must map every task to at least one pillar:

1. Ontological system understanding (primary focus):
   - entities, workflows, capability clusters, inbound/outbound integration ontology, multi-layer views
2. Migration intelligence:
   - readiness scoring, safe extraction boundaries, migration blueprint, integration rerouting risks
3. Developer enablement:
   - interactive exploration, impact simulation, decision support, guided refactoring, onboarding mode

## 3) Team split (2 roles)

### Role A: Platform + AI Integrations (Partner 1)

Owns:
- `apps/api/**`
- data contracts in `apps/api/app/models.py`
- integration reliability and backend tests

Primary goals:
- Harden ingestion and analysis reliability.
- Integrate CodeWords runtime into real pipeline behavior (not only standalone endpoint).
- Harden Dust semantic path and fallback behavior.
- Build ontology and migration intelligence artifacts in backend contracts.
- Prepare auth hardening plan (implementation can be after demo-critical tasks).

### Role B: Frontend + UX + Demo Experience (Partner 2)

Owns:
- `apps/web/**`
- visual UX quality, graph rendering, dashboard interactions, demo polish

Primary goals:
- Fix frontend build blocker and make graph rendering robust on large repos.
- Build multi-layer ontology UX and migration decision UX.
- Improve usability of pipeline tracker, risk panel, copilot references, and onboarding mode.
- Ensure responsive and presentation-grade demo flow.

## 4) API contract freeze (to avoid merge conflicts)

For this sprint, these endpoints are **frozen** and both roles should treat response fields as stable:

1. `POST /api/repos/register`
2. `POST /api/repos/{repo_id}/scan`
3. `GET /api/repos/{repo_id}/runs/{run_id}`
4. `GET /api/runs/{run_id}/workflow-graph`
5. `GET /api/runs/{run_id}/lineage-graph`
6. `GET /api/runs/{run_id}/risk-summary`
7. `GET /api/runs/{run_id}/node/{node_id}/evidence`
8. `GET /api/runs/{run_id}/enrichment`
9. `GET /api/runs/{run_id}/migration-blueprint`
10. `POST /api/copilot/query`
11. `GET /api/integrations/mcp/status`
12. `POST /api/integrations/codewords/trigger`
13. `GET /api/integrations/codewords/result/{request_id}`
14. `GET /api/integrations/dust/status`
15. `GET /api/integrations/readiness`

Contract rules:
- No renaming of existing keys in current payloads.
- No type changes for existing keys.
- Additive-only changes allowed (new optional keys).
- Any contract change must be done in one PR that updates both:
  - `apps/api/app/models.py`
  - `apps/web/src/lib/api.ts`

### Endpoint registry (clear owner and payload intent)

| Endpoint | Request Keys | Response Keys (minimum) | Owner | Frontend Usage |
|---|---|---|---|---|
| `POST /api/repos/register` | `repo_url`, `default_branch`, `local_path` | `id`, `owner`, `name`, `default_branch`, `repo_url`, `local_path` | Role A | Repo intake form |
| `POST /api/repos/{repo_id}/scan` | `commit_sha` | `id`, `status`, `current_step`, `progress_pct`, `summary` | Role A | Start run + polling bootstrap |
| `GET /api/repos/{repo_id}/runs/{run_id}` | path params | `status`, `current_step`, `progress_pct`, `error_message`, `summary` | Role A | Pipeline tracker |
| `GET /api/runs/{run_id}/workflow-graph` | path params | `run_id`, `nodes[]`, `edges[]` | Role A | Process ontology graph |
| `GET /api/runs/{run_id}/lineage-graph` | path params | `run_id`, `nodes[]`, `edges[]` | Role A | Data lineage and integration direction |
| `GET /api/runs/{run_id}/risk-summary` | path params | `run_id`, `overall_score`, `findings[]` | Role A | Risk and migration panel |
| `GET /api/runs/{run_id}/node/{node_id}/evidence` | path params | `run_id`, `node_id`, `files[]`, `symbols[]`, `explanation` | Role A | Evidence drawer |
| `GET /api/runs/{run_id}/enrichment` | path params | `run_id`, `provider`, `status`, `service_id`, `request_id`, `ontology_enrichment`, `migration_hints`, `quality_checks`, `raw` | Role A | Ontology/migration enrichment panel |
| `GET /api/runs/{run_id}/migration-blueprint` | path params | `run_id`, `readiness_score`, `readiness_band`, `entities`, `impacted_modules`, `extraction_boundaries`, `integration_routing`, `top_risks`, `recommendations`, `phased_plan` | Role A | Migration planning panel |
| `POST /api/copilot/query` | `run_id`, `question`, `focus_node_id?` | `answer`, `citations[]`, `risk_implications[]`, `related_nodes[]` | Role A | Developer enablement assistant |
| `GET /api/integrations/mcp/status` | none | `source`, `exists`, `servers` | Role A | Integration badges |
| `POST /api/integrations/codewords/trigger` | `service_id`, `inputs`, `async_mode` | `provider`, `service_id`, `status`, `request_id`, `raw` | Role A | Backend integration checks |
| `GET /api/integrations/codewords/result/{request_id}` | path params | `provider`, `request_id`, `status`, `raw` | Role A | Backend integration checks |
| `GET /api/integrations/dust/status` | none | `configured`, `workspace_id`, `configuration_id` | Role A | Integration badges |
| `GET /api/integrations/readiness` | none | `checked_at`, `codewords{configured,reachable,latency_ms,detail}`, `dust{...}`, `mcp{...}` | Role A | Integration health badges + debug panel |

Rules for avoiding merge issues:
- Role B can consume all endpoints but cannot change request/response shapes directly.
- Role A can add optional fields only; if required fields are needed, coordinate same-day with Role B.
- Endpoint docs in this table are the single source of truth for this sprint.

### Endpoint purpose map (why each endpoint exists, and when to call it)

1. `POST /api/repos/register`
- Purpose: create a canonical repository record and parsing context (owner/name/branch/local path).
- Use it when: user submits a repo in intake form.

2. `POST /api/repos/{repo_id}/scan`
- Purpose: create and queue an analysis run; start ingestion + AST + artifact generation.
- Use it when: user clicks Start Analysis.

3. `GET /api/repos/{repo_id}/runs/{run_id}`
- Purpose: track run lifecycle and progress telemetry.
- Use it when: polling run status until completed/failed.

4. `GET /api/runs/{run_id}/workflow-graph`
- Purpose: provide the process explorer graph (execution/control relationships).
- Use it when: rendering Process Atlas.

5. `GET /api/runs/{run_id}/lineage-graph`
- Purpose: provide the data lineage graph (entity transition relationships).
- Use it when: rendering Data Lineage Navigator.

6. `GET /api/runs/{run_id}/risk-summary`
- Purpose: provide prioritization data (overall score + findings + rationale + suggestions).
- Use it when: rendering Risk Observatory and migration urgency cues.

7. `GET /api/runs/{run_id}/node/{node_id}/evidence`
- Purpose: explain why a node exists using files/symbols/explanation traceability.
- Use it when: user selects a workflow or lineage node.

8. `GET /api/runs/{run_id}/enrichment`
- Purpose: return post-analysis semantic augmentation from CodeWords (ontology enrichment, migration hints, quality checks).
- Use it when: enriching interpretation panels beyond core static artifacts.

9. `GET /api/runs/{run_id}/migration-blueprint`
- Purpose: return an execution-ready migration plan synthesized from run summary + risk + lineage (+ enrichment if available).
- Use it when: user enters migration planning mode.

10. `POST /api/copilot/query`
- Purpose: provide developer Q/A grounded in run artifacts, evidence, risks, and optional Dust semantics.
- Use it when: user asks “what depends on this?”, “what breaks if I change X?”.

11. `GET /api/integrations/mcp/status`
- Purpose: show loaded MCP server config summary.
- Use it when: debugging tool connectivity and environment setup.

12. `POST /api/integrations/codewords/trigger`
- Purpose: manually trigger a specific CodeWords workflow for testing or ad-hoc enrichment.
- Use it when: integration validation and controlled workflow testing.

13. `GET /api/integrations/codewords/result/{request_id}`
- Purpose: poll status/result of a previously triggered CodeWords workflow.
- Use it when: async workflow monitoring.

14. `GET /api/integrations/dust/status`
- Purpose: indicate whether Dust workspace/config is present.
- Use it when: deciding Dust copilot availability UI state.

15. `GET /api/integrations/readiness`
- Purpose: provide health snapshot of integrations (`configured`, `reachable`, `latency_ms`, `detail`) to decide confidence and fallbacks.
- Use it when: showing integration health badges and operational diagnostics.

## 5) Parallel work boundaries

Allowed in parallel without coordination:
- Role A edits under `apps/api/**`.
- Role B edits under `apps/web/**` except `apps/web/src/lib/api.ts`.

Needs sync before merge:
- `apps/web/src/lib/api.ts`
- `README.md`
- `Makefile`
- any file under `legacy-atlas-plan/**`

## 6) Backlog by owner

### Role A backlog (Platform + Integrations)

P0:
1. Connect CodeWords runtime to a real analysis action path.
2. Add backend endpoint-level tests for CodeWords trigger/poll success and error branches.
3. Add Dust configured/unconfigured behavior tests with deterministic mocks.
4. Emit ontology-layer artifacts in run summary metadata:
   - entities extracted
   - workflow transitions
   - integration inbound/outbound counts
5. Add migration readiness score and boundary candidate list as additive fields.

P1:
1. Improve run telemetry fields (duration, ingestion mode, branch used) in run summary.
2. Add explicit endpoint for integration health readiness (`configured + reachable`).
3. Add migration blueprint payload generation (data models, APIs, impacted modules, phased steps).
4. Prepare auth design doc and middleware plan (token/JWT/API key strategy).

P2:
1. Add lightweight rate limiting and request-id logging correlation.
2. Add structured error codes for frontend-friendly handling.

### Role B backlog (Frontend + Demo UX)

P0:
1. Fix `GraphCanvas.tsx` build issue (`NODE_WIDTH` unused).
2. Improve graph viewport behavior for wide/complex graphs.
3. Build ontology navigation layers in UI:
   - business/process/code/integration/risk toggles
4. Surface inbound vs outbound integration directions clearly in graph and inspector.
5. Remove fallback-mode evidence 404 handling from UI (now backend returns evidence for fallback nodes, UI should assume data is available but still degrade gracefully).

P1:
1. Make citations interactive (jump/filter evidence panel by file/symbol).
2. Improve risk panel readability for migration suggestions, readiness, and severity sorting.
3. Add migration intelligence panel (readiness + extraction boundaries + rerouting risk notes).
4. Add clearer status banners for `fallback` vs `ast-local`.

P2:
1. Use `VITE_API_BASE_URL` instead of hardcoded backend URL.
2. Add onboarding mode panel with suggested reading order and key files.
3. Add a demo mode preset panel (pre-filled repo choices and questions).

## 7) Daily working protocol

1. Work on separate branches:
- `codex/backend-*` for Role A
- `codex/frontend-*` for Role B

2. Start of day:
- Rebase from `main`.
- Reconfirm endpoint freeze and open blockers.

3. During day:
- Keep PRs small and focused (one intent per PR).
- No cross-role refactors in the same PR.

4. End of day:
- Run tests/build before pushing:
  - Backend: `cd apps/api && pytest -q`
  - Frontend: `cd apps/web && npm run build`

## 8) Definition of done per task

- Code implemented.
- Local validation passed.
- No contract break against frozen endpoints.
- Logs are clear for new backend behaviors.
- UI states are handled for loading, success, and error.
- Pillar mapping is explicit in PR description (ontology, migration intelligence, developer enablement).

## 9) Immediate next steps (today)

1. Role B: fix frontend build blocker (`GraphCanvas.tsx`) and confirm `npm run build`.
2. Role A: implement first real CodeWords orchestration path (trigger + poll + attach result to run summary).
3. Role A: add additive ontology/migration summary fields without breaking endpoint contract.
4. Role B: build first ontology layer toggle UI with existing graph endpoints.
5. Sync once after these are done, then start P1 items in parallel.

## 10) Current checkpoint (updated)

Completed by Role A:
- CodeWords runtime hook is executed from the post-analysis path.
- Analysis summary contract is normalized before CodeWords calls (`analysis_mode`, graph/risk counters, scan counters).
- CodeWords enrichment is persisted as a dedicated artifact and exposed on `GET /api/runs/{run_id}/enrichment`.
- Ingestion now auto-resolves effective branch and surfaces `ingestion_branch` telemetry in run summary.
- Copilot remains Dust-first and now passes CodeWords enrichment context to improve grounded responses.
- Migration blueprint endpoint is available on `GET /api/runs/{run_id}/migration-blueprint`.
- Integration readiness endpoint is available on `GET /api/integrations/readiness`.
- Stable API error shape with additive `detail.detail_code` is in place for frontend handling.
- One-command backend smoke flow is available via `make api-smoke`.

Next for Role B:
- Consume `GET /api/runs/{run_id}/enrichment` and surface `ontology_enrichment`, `migration_hints`, and `quality_checks`.
- Keep endpoint usage additive-only per freeze rules.

## 11) Partner 2 Handoff (Start Here)

Use these backend endpoints as the immediate UI integration base:

1. `GET /api/runs/{run_id}/enrichment`
2. `GET /api/runs/{run_id}/migration-blueprint`
3. `GET /api/integrations/readiness`

Render and state-handling requirements:
- Enrichment panel: show `status`, `ontology_enrichment`, `migration_hints`, `quality_checks`.
- Migration panel: show `readiness_score`, `readiness_band`, `top_risks`, `phased_plan`.
- Integration badges: show `configured`, `reachable`, and optional `latency_ms`.

What each of these three means in product terms:

1. `GET /api/runs/{run_id}/enrichment`
- What it is: semantic augmentation generated after core analysis (usually via CodeWords).
- What it is for: make ontology and migration interpretation smarter than pure heuristics.
- Important behavior: this can be `not_configured`, `queued`, `running`, `completed`, `failed`, or `error`; UI must not block core graph views if enrichment is unavailable.

2. `GET /api/runs/{run_id}/migration-blueprint`
- What it is: a structured migration plan object built from existing analysis artifacts.
- What it is for: move from “understand system” to “execute migration safely.”
- Important behavior: this is decision support, not raw telemetry. It packages readiness, top risks, extraction boundaries, integration routing risks, and phased plan for action.

3. `GET /api/integrations/readiness`
- What it is: operational health and connectivity status of CodeWords, Dust, and MCP.
- What it is for: determine trust level of AI/enrichment outputs and show clear setup/debug states.
- Important behavior: readiness explains why features are degraded (not configured vs configured but unreachable), so UI should surface this before users assume backend bugs.

Recommended UI call timing:

1. On run completion:
- Fetch `workflow-graph`, `lineage-graph`, `risk-summary` in parallel (core required views).
- Fetch `enrichment` and `migration-blueprint` right after (advanced views).

2. On app/init or settings open:
- Fetch `integrations/readiness` to set integration banners and badges.

Error handling contract:
- API errors now include `detail.detail_code` and `detail.message`.
- UI should branch by `detail_code` for reliable messages and fallback UX.

Validation command before frontend PR:
- `make api-smoke` must pass on latest `main`.

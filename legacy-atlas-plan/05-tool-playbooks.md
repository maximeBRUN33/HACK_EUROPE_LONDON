# Tool Playbooks and MCP Guide

## 1) MCP Configuration Review

Current file:

- `dust-integration/references/mcp-config.json`

Doc-grounded constraints applied in this plan:

1. CodeWords supports direct workflow calls with synchronous and asynchronous endpoints.
2. Dust `run_agent` has recursion and execution limits that should shape agent fan-out.
3. Lovable Plan mode persists planning artifacts and Browser Testing supports scripted journey checks.

What is good:

1. Dust MCP endpoint is configured.
2. CodeWords runtime MCP endpoint is configured.
3. Lovable MCP server command is declared.

What must be fixed before production:

1. Lovable project path is placeholder (`/absolute/path/to/lovable/project`).
2. CodeWords bearer token is hardcoded in plaintext.
3. Secrets need rotation if this file has ever been shared/committed.

Recommended secure pattern:

1. Keep config shape in repo.
2. Inject secrets from environment or secret manager at runtime.
3. Rotate tokens and limit scope to minimum permissions.

## 2) Tool Responsibility Matrix

CodeWords:

- Orchestration, schedules, triggers, webhooks, deterministic workflow runs.

Dust:

- Multi-agent reasoning, RAG grounding, semantic labeling, copilot answer generation.

Lovable:

- Planning UX, accelerated frontend generation, browser journey validation.

## 3) CodeWords Playbook

Target workflows:

1. `repo_intake_radar`
   - Trigger: GitHub webhook or manual run
   - Action: register repo, fetch metadata, queue scan
   - Output: repository intake report

2. `analysis_pipeline_run`
   - Trigger: schedule and on-demand
   - Action: invoke ingestion -> static analysis -> risk scoring -> Dust enrichment
   - Output: analysis run status and summary

3. `delta_watchdog`
   - Trigger: nightly schedule
   - Action: compare latest run with prior run
   - Output: topology/risk drift summary

4. `demo_snapshot_refresh`
   - Trigger: manual before pitch
   - Action: precompute graph payloads and cache copilot context
   - Output: stable snapshot for live demo

Implementation notes:

- Prefer asynchronous execution endpoints for long jobs.
- Persist run IDs and statuses for UI progress indicators.
- Attach webhook retry and dead-letter behavior for reliability.

## 4) Dust Playbook

Agent set:

1. `workflow_mapper_agent`
   - Input: symbols, call graph, entities
   - Output: business workflow labels + confidence

2. `lineage_interpreter_agent`
   - Input: lineage edges and ORM evidence
   - Output: human-readable data flow narrative

3. `risk_analyst_agent`
   - Input: metrics + dependency patterns
   - Output: ranked risk findings and mitigations

4. `copilot_orchestrator_agent`
   - Input: user query + run context
   - Output: cited answer and impact analysis

Operational constraints to respect:

1. Keep response schemas strict JSON for downstream rendering.
2. Limit recursive delegation depth to avoid runaway chains.
3. Keep each answer grounded with citations to symbols/files.

## 5) Lovable Playbook

Process:

1. Plan mode:
   Define route map, data contracts, and design system tokens.
2. Build mode:
   Generate initial screens and component skeletons.
3. Refine:
   Replace generic graph widgets with custom interaction components.
4. Validate:
   Use browser testing for smoke journeys and regression checks.

Critical prompt constraints:

1. Demand graph-first layout with evidence drawer and copilot side panel.
2. Demand explicit motion specs and performance constraints.
3. Demand semantic color mapping tied to risk severity.

## 6) Cross-Tool Integration Contracts

Contract A: CodeWords -> Analyzer API

- Payload includes `repo_url`, `commit_sha`, `run_id`, and `priority`.

Contract B: Analyzer -> Dust

- Payload includes summarized structural artifacts and a pointer to detailed evidence.

Contract C: UI -> CodeWords

- UI can trigger on-demand scan and poll run status.

Contract D: UI -> Copilot API (Dust-backed)

- Query plus scoped context returns cited answer and related nodes.

## 7) Failure and Fallback Runbook

If Dust is unavailable:

- Show deterministic analyzer output and disable semantic labels with clear badge.

If CodeWords trigger fails:

- Provide manual run endpoint in backend and log correlation IDs.

If Lovable generation lags:

- Freeze current UI and continue polish manually in React codebase.

## 8) Security Checklist

1. Rotate existing CodeWords token.
2. Move all secrets out of repo files.
3. Use least-privilege tokens for each environment.
4. Redact secrets from logs and screenshots.
5. Add pre-commit secret scanning.

## 9) Suggested Prompt Templates

CodeWords workflow planner prompt:

```text
Create a robust workflow for repository analysis.
Inputs: repo_url, commit_sha, run_id.
Steps: ingestion, static analysis, risk scoring, Dust enrichment.
Return strict JSON with step statuses, retries, and terminal output pointers.
```

Dust workflow mapping prompt:

```text
You are mapping ERP business workflows from code structure.
Use only provided evidence. Do not invent modules.
Output JSON: workflow_nodes, workflow_edges, confidence, citations.
Each node requires at least one code citation.
```

Lovable UI generation prompt:

```text
Build a graph-first engineering intelligence app with routes:
/repos, /atlas/:runId, /lineage/:runId, /risk/:runId.
Use Space Grotesk + IBM Plex Sans + JetBrains Mono.
Add evidence drawer, risk heat overlays, and keyboard navigation.
Design for premium dark theme with cyan/amber/coral accents.
```

## 10) Primary Documentation Links

CodeWords:

- https://docs.codewords.ai/core-concepts/introduction-to-cody
- https://docs.codewords.ai/core-concepts/schedules-and-triggers
- https://docs.codewords.ai/apps-and-integrations/calling-codewords-workflows
- https://docs.codewords.ai/apps-and-integrations/webhooks
- https://docs.codewords.ai/resources/codewords-on-ide/codewords-mcp-agent-your-ai-development-toolkit

Dust:

- https://docs.dust.tt/docs/remote-model-context-protocol-mcp
- https://docs.dust.tt/docs/run-agent
- https://docs.dust.tt/docs/triggers
- https://docs.dust.tt/reference/developer-platform-overview

Lovable:

- https://docs.lovable.dev/features/plan-mode
- https://docs.lovable.dev/features/browser-testing
- https://docs.lovable.dev/integrations/introduction

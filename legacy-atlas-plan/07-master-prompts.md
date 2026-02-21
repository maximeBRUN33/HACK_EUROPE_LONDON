# Master Prompts for Execution

## 1) Codex Implementation Prompt

```text
You are implementing Legacy Atlas MVP.
Goal: ingest ERPNext and Odoo subset, build workflow graph, lineage graph, risk dashboard, and cited copilot.

Constraints:
- Python-first parser.
- Deterministic extraction before semantic enrichment.
- Every semantic claim must cite code evidence.
- Frontend must support graph drill-down, risk overlays, and copilot.

Required outputs:
1) component modules and APIs
2) extractor implementation
3) workflow and lineage algorithms
4) risk scoring pipeline
5) UI graph + dashboard + copilot integration
6) tests and smoke scripts

Deliver incrementally with runnable checkpoints every phase.
```

## 2) Dust Agent Orchestrator Prompt

```text
Act as the Legacy Atlas semantic orchestrator.
Input includes symbols, graph edges, entities, lineage edges, and risk metrics.
Tasks:
1) map workflow clusters to business labels
2) summarize high-risk modules with rationale
3) generate cited answers for user copilot questions

Output strict JSON:
{
  "workflow_nodes": [],
  "workflow_edges": [],
  "risk_annotations": [],
  "copilot_answer": "",
  "citations": []
}

Rules:
- do not hallucinate files, functions, or modules
- require citation for every risk claim
- if evidence is insufficient, say so explicitly
```

## 3) Lovable Product Prompt

```text
Build a premium graph-first web app named Legacy Atlas.

Routes:
- /repos
- /atlas/:runId
- /lineage/:runId
- /risk/:runId

Core UI modules:
- interactive workflow graph canvas
- lineage flow canvas
- risk dashboard panels
- copilot panel with citations and linked evidence

Design:
- typography: Space Grotesk, IBM Plex Sans, JetBrains Mono
- palette: deep navy with cyan/amber/coral accents
- motion: staggered graph reveal, evidence drawer transitions, risk heat interpolation
- keyboard support and reduced motion mode

Performance:
- graph interactions under 120ms
- first meaningful paint under 1.8s
```

## 4) CodeWords Workflow Prompt

```text
Create a workflow named analysis_pipeline_run for Legacy Atlas.

Inputs:
- repo_url
- commit_sha
- run_id

Steps:
1) invoke ingestion endpoint
2) poll until ingestion complete
3) invoke static analyzer
4) invoke risk engine
5) invoke Dust semantic enrichment
6) persist summary and emit completion event

Requirements:
- retry transient failures with capped backoff
- structured logs with correlation ids
- return final JSON status report with step durations
```


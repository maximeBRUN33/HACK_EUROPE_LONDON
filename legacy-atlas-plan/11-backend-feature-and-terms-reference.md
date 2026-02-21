# Legacy Atlas Backend Feature and Terms Reference

## 1) What the software currently does

Legacy Atlas takes a repository, runs static analysis on Python code, and produces a set of run-scoped artifacts that the UI can explore:

- a process map of execution hotspots
- a data lineage map of core entities
- a risk analysis summary with migration-oriented suggestions
- node-level evidence (files, symbols, explanation)
- optional semantic enrichment from CodeWords
- optional grounded copilot answers from Dust
- a migration blueprint assembled from risk, lineage, and enrichment

Everything is tied to one analysis run. The run is the anchor object for process, lineage, risk, evidence, enrichment, and migration outputs.

## 2) Feature catalog (backend behavior)

### Repository intake and run orchestration

- Register a repository URL and branch.
- Start a scan run for a commit label.
- Track run status, current step, and progress percentage until completion or failure.

Primary endpoints:

- `POST /api/repos/register`
- `POST /api/repos/{repo_id}/scan`
- `GET /api/repos/{repo_id}/runs/{run_id}`

### Source resolution and ingestion

- The analyzer tries to resolve a local repository path (explicit local path first, then configured root folders).
- If clone or local resolution fails, the system still completes with fallback artifacts so the UI remains usable.

### AST-based structural analysis

- The analyzer parses Python files into an Abstract Syntax Tree (AST).
- It extracts functions, call signals, complexity signals, entity signals, and CRUD-like operation hints.
- It builds an approximate call graph used by workflow and risk generation.

### Process Explorer (UI title: Process Atlas)

- Builds a workflow graph from selected high-signal functions.
- Returns nodes and control-flow edges.
- Adds a risk hub node connected to the highest-risk workflow area.

Primary endpoint:

- `GET /api/runs/{run_id}/workflow-graph`

### Data lineage explorer (UI title: Data Lineage Navigator)

- Builds entity-centric graph nodes from inferred business entities.
- Builds directed data edges from observed entity sequences in function bodies.
- Focuses on movement and ordering of business data concepts.

Primary endpoint:

- `GET /api/runs/{run_id}/lineage-graph`

### Risk analysis (UI title: Risk Observatory)

- Produces an overall risk score and structured findings.
- Categories are: complexity, coupling, dead code, and test gap.
- Every finding includes severity, rationale, affected symbol, and migration suggestions.

Primary endpoint:

- `GET /api/runs/{run_id}/risk-summary`

### Node evidence drill-down

- Returns the explainability payload for one selected node.
- Includes supporting files, symbols, and plain-language explanation.

Primary endpoint:

- `GET /api/runs/{run_id}/node/{node_id}/evidence`

### Ontology and migration summaries inside run output

The run summary embeds:

- ontology snapshot (top entities, domain clusters, inbound/outbound integration signals)
- migration snapshot (readiness score, extraction boundaries, impacted modules, rerouting risks)

This data is consumed by migration blueprint generation and can also feed agent workflows.

### Migration intelligence blueprint

- Builds a phased migration plan from run summary + risk + lineage (+ optional enrichment).
- Returns readiness band, extraction boundaries, integration routing risks, recommendations, and phased execution steps.

Primary endpoint:

- `GET /api/runs/{run_id}/migration-blueprint`

### CodeWords enrichment integration

- After analysis, the backend can trigger a CodeWords workflow asynchronously.
- It polls for completion and stores normalized enrichment as a run artifact.
- Enrichment is exposed as ontology enrichment, migration hints, quality checks, and raw response metadata.

Primary endpoints:

- `POST /api/integrations/codewords/trigger`
- `GET /api/integrations/codewords/result/{request_id}`
- `GET /api/runs/{run_id}/enrichment`

### Dust-powered developer copilot

- Copilot builds a context from workflow graph, risk findings, and node evidence.
- If Dust is configured, the question is routed to Dust for grounded semantic output.
- If Dust is unavailable, the backend returns a deterministic local fallback answer.

Primary endpoint:

- `POST /api/copilot/query`

### Integration readiness and MCP visibility

- Exposes readiness of CodeWords, Dust, and MCP configuration/reachability.

Primary endpoints:

- `GET /api/integrations/readiness`
- `GET /api/integrations/mcp/status`
- `GET /api/integrations/dust/status`

## 3) Core terms and definitions

### AST

AST means Abstract Syntax Tree. It is a structural representation of source code used to inspect functions, calls, and logic shape without executing the code.

### Entity

An entity is a business data concept inferred from code signals, such as Customer, Order, Invoice, Payment, Stock, or Ledger.

### Ontology

Ontology is the semantic map of the system: entities, process signals, capability clusters, and integration touchpoints that describe what the system is responsible for.

### Workflow (business sense)

A workflow is a business process progression, such as Lead to Quote to Order to Invoice.

### Workflow (code sense)

A workflow is a connected chain of meaningful functions inferred from call and complexity signals that represent execution progression in the codebase.

### Workflow node

A workflow node is one selected function judged to be operationally important for process understanding. It is not every function in the repository.

### Process node

A process node is a workflow node labeled as a normal process step (`node_type = process`) rather than a high-risk hotspot.

### Risk node

A risk node is either a workflow hotspot with high risk score or the dedicated risk hub that aggregates risk attention in the process graph.

### Lineage

Lineage is the inferred directional movement of business entities through code operations, showing how data concepts transition across execution steps.

### Node

A node is a graph vertex. In Legacy Atlas, nodes can represent process steps, data entities, or risk anchors.

### Edge

An edge is a directed relationship between nodes. Edge types are:

- control: execution/control relationship
- data: data/entity transition
- risk: risk linkage

### Evidence

Evidence is the trace payload attached to a node: supporting files, related symbols, and explanation text.

### Capability cluster

A capability cluster is a grouped business domain signal inferred from code surface terms, such as CRM, Billing, Inventory, and Reporting.

### Integration touchpoints

Integration touchpoints are inferred inbound and outbound external connection signals found in code behavior and naming.

### Migration readiness score

Migration readiness is a computed signal that combines risk pressure and integration exposure to estimate how safely a subsystem can be extracted or migrated.

### Extraction boundary

An extraction boundary is a candidate migration cut-line anchored on risky or central symbols plus required entities that must move together.

## 4) Node relationship logic (how nodes are connected)

### Run-scoped relationship model

- One run owns one workflow graph, one lineage graph, one risk summary, and zero or one enrichment payload.
- One run owns many node evidence records.
- Evidence is keyed by run plus node id, so the same node id in different runs is treated independently.

### Workflow graph relationship rules

- Candidate functions are ranked by a weighted signal: complexity, outbound call degree, entrypoint-like naming, entity signals, and CRUD signals.
- The top ranked functions become workflow nodes.
- Workflow edges are created when selected functions call each other.
- If no call edges are available, the system links selected nodes in sequence as a fallback topology.
- A risk hub node is appended and linked from the highest-risk workflow node.

### Lineage graph relationship rules

- Entity nodes are chosen from the most frequent inferred entities.
- For each function, entity mentions are read as an ordered sequence.
- Repeated adjacent entities are compressed.
- Transitions between consecutive entities create directed lineage edges.
- Edge confidence increases with repeated transition evidence.

### Risk-to-node relationship rules

- Risk findings point to a symbol (anchor function/module signal).
- The process graph includes a dedicated risk hub to make risk visible in process context.
- Evidence for risk hub summarizes the top findings and their anchors.

### Evidence relationship rules

- Workflow node evidence points to the function file and symbol(s) that produced that node.
- Lineage node evidence points to representative functions that contributed to entity inference.
- Evidence exists to support explainability for graph inspection and copilot grounding.

## 5) Process Explorer vs Risk Analysis

Process Explorer and Risk Analysis answer different questions and intentionally return different payloads.

### Process Explorer

Question answered:

- How does behavior flow through the system?

Primary data endpoint:

- `GET /api/runs/{run_id}/workflow-graph`

Returned data:

- `run_id`
- `nodes[]` with `id`, `label`, `node_type`, `risk_score`
- `edges[]` with `source`, `target`, `edge_type`, `confidence`

Supporting endpoint:

- `GET /api/runs/{run_id}/node/{node_id}/evidence`

Why it exists:

- To navigate structure and execution relationships.
- To let users click a step and inspect source-backed evidence.

### Risk Analysis

Question answered:

- Where is change most dangerous, and why?

Primary data endpoint:

- `GET /api/runs/{run_id}/risk-summary`

Returned data:

- `run_id`
- `overall_score`
- `findings[]` with `id`, `category`, `severity`, `score`, `title`, `rationale`, `symbol`, `migration_suggestions[]`

Why it exists:

- To prioritize engineering attention by impact and failure likelihood.
- To provide migration-oriented recommendations, not graph topology.

### Practical difference

- Process Explorer is topology-first and navigation-first.
- Risk Analysis is prioritization-first and decision-first.
- They are complementary: graph tells where things connect, risk tells where to act first.

## 6) What workflow nodes are in this analyzer

In this backend, workflow nodes are selected function-level execution anchors.

They are:

- inferred from static analysis, not manually defined BPMN tasks
- selected from top-ranked functions, not all functions
- shaped for comprehension and impact analysis, not for runtime orchestration
- represented as process or risk typed graph nodes with a risk score

In short, a workflow node is the analyzer's best candidate for a meaningful business-relevant step in code execution.

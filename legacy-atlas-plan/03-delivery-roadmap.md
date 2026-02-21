# Legacy Atlas Delivery Roadmap

## 1) Delivery Strategy

Use a layered delivery model:

1. Ship deterministic extraction first.
2. Add semantic enrichment second.
3. Add visual excellence and copilot third.
4. Harden demo path last.

This sequence minimizes integration risk and maximizes visible progress every few hours.

## 2) Hackathon Timeline (48 Hours)

## Phase 0: Foundation (Hours 0-4)

Goals:

- Freeze architecture and contracts.
- Validate MCP and API access for all tools.

Tasks:

1. Initialize service skeletons and shared schema.
2. Finalize repo list and pin commit SHAs.
3. Configure CodeWords workflows and Dust agents.
4. Generate first Lovable UI shell from plan.

Definition of done:

- One command or workflow can trigger a full run stub end to end.

## Phase 1: Deterministic Analyzer Core (Hours 4-16)

Goals:

- Produce reliable symbol graph and basic risks.

Tasks:

1. Python AST parser and symbol extraction.
2. Import and call edge extraction.
3. ORM model/entity extraction.
4. Complexity and coupling metrics.

Definition of done:

- For ERPNext sample module, graph renders modules/classes/functions and risk scores.

## Phase 2: Workflow and Lineage Intelligence (Hours 16-28)

Goals:

- Produce business-relevant workflow and data flow views.

Tasks:

1. Entry-point detection and bounded call tracing.
2. CRUD operation extraction and lineage edges.
3. Dust semantic labeling over clusters.
4. Evidence linking from workflow nodes to code.

Definition of done:

- Query "sales order to invoice flow" returns usable graph path and evidence.

## Phase 3: Copilot and UI Excellence (Hours 28-40)

Goals:

- Deliver premium interaction quality.

Tasks:

1. Build graph-first explorer and risk dashboard in Lovable-generated React app.
2. Add copilot panel with citations and risk impact sections.
3. Add motion and visual hierarchy polish.
4. Validate key journeys via browser testing.

Definition of done:

- Three polished flows are demo-ready without manual patching.

## Phase 4: Hardening and Demo Story (Hours 40-48)

Goals:

- Reduce failure risk and optimize storytelling.

Tasks:

1. Add smoke tests and fallback UI states.
2. Cache expensive graph and copilot requests.
3. Build demo script with deterministic data snapshots.
4. Run two full dry runs with timing.

Definition of done:

- Demo runs start to finish twice with no blockers.

## 3) Workstream Breakdown by Owner Type

Backend lead:

- ingestion, analyzer, metrics, APIs

AI lead:

- Dust agents, prompt contracts, evidence grounding

Product/UI lead:

- Lovable plan and build cycles, visual system, interaction polish

Ops lead:

- CodeWords workflows, triggers, run observability

## 4) Prioritized Backlog (MVP First)

P0 items:

1. Repository ingestion and run tracking
2. Python symbol graph extraction
3. Workflow graph generation (heuristic + semantic)
4. Data lineage for at least three entities
5. Risk summary endpoint
6. Frontend graph navigation
7. Copilot with citations

P1 items:

1. Revision diff graph
2. Migration readiness index
3. Hotspot trend chart across runs

P2 items:

1. PHP adapter prototype
2. Advanced what-if simulation

## 5) Quality Gates

Gate A (Hour 16):

- Analyzer output correctness spot-check on 20 symbols and 20 edges.

Gate B (Hour 28):

- Workflow and lineage output validated by two scenario queries.

Gate C (Hour 40):

- UI flows complete and copilot responses citation-grounded.

Gate D (Hour 46):

- Full demo rehearsal passes with stable timings.

## 6) Risk Register and Mitigations

Risk: call graph quality is noisy in dynamic Python.

- Mitigation: confidence scoring + fallback to import and naming-based adjacency.

Risk: semantic labels become generic.

- Mitigation: constrain Dust prompts with ERP ontology and strict output schema.

Risk: UI performance drops on large graphs.

- Mitigation: graph paging, neighborhood expansion, server-side filtering.

Risk: orchestration failures near demo.

- Mitigation: snapshot fallback mode with precomputed artifacts.

## 7) Demo-First Acceptance Checklist

1. "Where is sales confirmation logic?" shows exact nodes and files.
2. "Impact of changing lead assignment?" shows affected workflow path and risks.
3. Risk dashboard highlights top hotspots with clickable evidence.
4. Visual style is consistent, fast, and clearly premium.


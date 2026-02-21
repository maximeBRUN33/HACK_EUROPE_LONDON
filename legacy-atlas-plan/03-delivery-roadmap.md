# Legacy Atlas Delivery Roadmap

## 1) Delivery Strategy

Use a layered delivery model:

1. Ship ontology-grade deterministic extraction first.
2. Add migration intelligence second.
3. Add developer enablement workflows third.
4. Add visual excellence and demo hardening last.

This sequence minimizes integration risk and maximizes visible progress every few hours.

## 2) Pillar Coverage Map

Pillar to phase mapping:

1. Ontological System Understanding:
   - Phases 1 and 2
2. Migration Intelligence:
   - Phases 2 and 4
3. Developer Enablement:
   - Phases 3 and 4

## 3) Hackathon Timeline (48 Hours)

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

- Produce reliable ontology primitives and basic risks.

Tasks:

1. Python AST parser and symbol extraction.
2. Import and call edge extraction.
3. ORM model/entity extraction.
4. Complexity and coupling metrics.
5. Integration surface extraction (inbound and outbound interface candidates).
6. Domain capability clustering candidates (CRM, Billing, Inventory, Reporting).

Definition of done:

- For ERPNext sample module, graph renders entities, workflows, integration directions, and risk scores.

## Phase 2: Workflow and Lineage Intelligence (Hours 16-28)

Goals:

- Produce business-relevant workflow and migration-relevant data flow views.

Tasks:

1. Entry-point detection and bounded call tracing.
2. CRUD operation extraction and lineage edges.
3. Dust semantic labeling over clusters.
4. Evidence linking from workflow nodes to code.
5. Inbound/outbound routing map generation for integration ontology.
6. Migration readiness scoring and safe extraction boundary candidate generation.

Definition of done:

- Query "sales order to invoice flow" returns usable graph path and evidence.

## Phase 3: Developer Enablement and UI Excellence (Hours 28-40)

Goals:

- Deliver premium interaction quality.

Tasks:

1. Build graph-first explorer with multi-layer ontology navigation.
2. Add copilot panel with citations, impact simulation, and extraction decision support.
3. Add motion and visual hierarchy polish.
4. Add onboarding mode: flow explanation + critical files + reading order.
5. Validate key journeys via browser testing.

Definition of done:

- Three polished flows are demo-ready without manual patching.

## Phase 4: Hardening and Demo Story (Hours 40-48)

Goals:

- Reduce failure risk and optimize storytelling.

Tasks:

1. Add smoke tests and fallback UI states.
2. Cache expensive graph and copilot requests.
3. Build demo script with deterministic data snapshots.
4. Add exportable migration blueprint output for one reference flow.
5. Run two full dry runs with timing.

Definition of done:

- Demo runs start to finish twice with no blockers.

## 4) Workstream Breakdown by Owner Type

Backend lead:

- ingestion, analyzer, metrics, APIs

AI lead:

- Dust agents, prompt contracts, evidence grounding

Product/UI lead:

- Lovable plan and build cycles, visual system, interaction polish

Ops lead:

- CodeWords workflows, triggers, run observability

## 5) Prioritized Backlog (MVP First)

P0 items:

1. Repository ingestion and run tracking
2. Python symbol graph extraction
3. Workflow graph generation (heuristic + semantic)
4. Data lineage for at least three entities
5. Integration ontology extraction (inbound/outbound + direction)
6. Risk summary endpoint
7. Frontend graph navigation
8. Copilot with citations

P1 items:

1. Migration readiness index
2. Safe extraction boundary detector
3. Migration blueprint export payload
4. Impact simulation view in copilot
5. Revision diff graph
6. Hotspot trend chart across runs

P2 items:

1. PHP adapter prototype
2. Advanced what-if simulation
3. Onboarding mode auto-briefing for first-time contributors

## 6) Quality Gates

Gate A (Hour 16):

- Analyzer output correctness spot-check on 20 symbols and 20 edges.

Gate B (Hour 28):

- Workflow, lineage, and integration direction output validated by two scenario queries.

Gate C (Hour 40):

- UI flows complete and copilot responses citation-grounded with impact support.

Gate D (Hour 46):

- Full demo rehearsal passes with stable timings and migration blueprint walkthrough.

## 7) Risk Register and Mitigations

Risk: call graph quality is noisy in dynamic Python.

- Mitigation: confidence scoring + fallback to import and naming-based adjacency.

Risk: semantic labels become generic.

- Mitigation: constrain Dust prompts with ERP ontology and strict output schema.

Risk: migration recommendations are too abstract.

- Mitigation: always bind migration guidance to explicit entities, symbols, and integration edges.

Risk: UI performance drops on large graphs.

- Mitigation: graph paging, neighborhood expansion, server-side filtering.

Risk: orchestration failures near demo.

- Mitigation: snapshot fallback mode with precomputed artifacts.

## 8) Demo-First Acceptance Checklist

1. "Where is sales confirmation logic?" shows exact nodes and files.
2. "Impact of changing lead assignment?" shows affected workflow path and risks.
3. Risk dashboard highlights top hotspots with clickable evidence.
4. Migration screen shows readiness, safe boundary candidates, and integration rerouting impact.
5. Visual style is consistent, fast, and clearly premium.

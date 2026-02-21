# Legacy Atlas Strategy and Decisions

## 1) Mission and Success Criteria

Legacy Atlas is an AI-powered system that turns large ERP/CRM codebases into:

- Process maps
- Data lineage graphs
- Risk dashboards
- Developer copilots

Success for hackathon MVP:

1. Ingest at least two Python-heavy repos (ERPNext and Odoo module subset).
2. Generate actionable graph outputs (not only text summaries).
3. Answer grounded copilot questions with traceability to code locations.
4. Show one compelling UI walkthrough from workflow to risk to code evidence.

## 2) Product Positioning

Most tools either:

- Index code for chat only, or
- Visualize static architecture only.

Legacy Atlas differentiates by combining:

1. Static program analysis (deterministic)
2. Agentic interpretation (semantic)
3. Interactive visual graph UX (navigable evidence)

This hybrid is the core intellectual move: deterministic extraction for trust, LLM interpretation for speed, and visual narrative for comprehension.

## 3) Core Principles

1. Evidence-first AI: every summary and risk claim links to files, symbols, and edges.
2. Python-first scope: optimize early wins on Odoo/ERPNext before PHP expansion.
3. Incremental semantics: ship useful process maps from heuristics, then refine.
4. Visual primacy: UI is not a wrapper; it is a comprehension instrument.
5. Low-latency feedback loops: ingestion and analysis should stream intermediate output.

## 4) Strategic Role of Each Tool

### CodeWords

Best use: deterministic automation and system glue.

- Trigger repo scans from webhooks/schedules.
- Run repeatable extraction jobs.
- Store short-term run memory and deltas.
- Expose workflow endpoints for UI demo integration.

Why this is the best move:

- Hackathons fail when orchestration is ad hoc.
- CodeWords gives repeatability and event-driven control quickly.

### Dust

Best use: multi-agent reasoning and grounded semantic interpretation.

- Agent council for architecture and risk interpretation.
- RAG grounding over extracted artifacts.
- Trigger-based autonomous updates.

Why this is the best move:

- Dust handles orchestration of reasoning tasks better than forcing all logic into single prompts.
- `run_agent` lets you delegate deep analysis while keeping output composable.

### Lovable

Best use: high-velocity UI strategy and implementation acceleration.

- Plan mode for product-level UX and screen architecture.
- Rapid frontend generation and iteration.
- Browser testing for journey validation before demo.

Why this is the best move:

- The hackathon winner often has both technical depth and presentation quality.
- Lovable shortens time to polished interaction design.

## 5) Decision Review (Choice, Alternatives, Tradeoffs)

### Decision A: Start with Python repos before PHP/JS

Options considered:

- Analyze mixed-language repos from day one.
- Python-first for first milestones.

Choice:

- Python-first (ERPNext, Odoo subset).

Why best:

- Higher tool maturity for Python AST and call graph extraction.
- Lower complexity under hackathon time constraints.

Tradeoff:

- Reduced language coverage early.

Mitigation:

- Define language adapter contracts now; implement PHP adapter after MVP.

### Decision B: Hybrid extraction pipeline (deterministic + agentic)

Options considered:

- LLM-only extraction
- Static-only extraction
- Hybrid approach

Choice:

- Hybrid extraction.

Why best:

- Static analysis gives trustworthy structure.
- Agentic layer maps structure to business semantics.

Tradeoff:

- More components to integrate.

Mitigation:

- Strict API boundary between analyzer output and semantic layer.

### Decision C: Graph-centric backend model

Options considered:

- Flat relational-only
- Graph-only
- Relational + graph projection

Choice:

- Relational source of truth + graph projection tables/APIs.

Why best:

- Keeps implementation simple while enabling fast UI graph traversal.

Tradeoff:

- Need projection refresh logic.

Mitigation:

- Event-based projection updates on each completed analysis run.

### Decision D: Use CodeWords as pipeline orchestrator

Options considered:

- Build custom queue orchestration in app code
- Use CodeWords workflows and triggers

Choice:

- CodeWords workflows for orchestration.

Why best:

- Faster path to reliable scheduling, webhooks, and observability.

Tradeoff:

- Dependency on external workflow platform.

Mitigation:

- Keep worker logic in standalone services; CodeWords only orchestrates calls.

### Decision E: Use Dust for semantic labeling and risk reasoning

Options considered:

- All semantics in local rules
- All semantics in direct single LLM calls
- Dust multi-agent + RAG

Choice:

- Dust multi-agent + RAG for semantic interpretation.

Why best:

- Better separation between extraction and reasoning.
- Better grounding and explainability through knowledge attachments.

Tradeoff:

- Prompt and agent tuning overhead.

Mitigation:

- Start with two specialized agents, then expand.

### Decision F: Lovable-driven UI acceleration

Options considered:

- Build entire UI manually from scratch
- Use Lovable for quick generation and polish manually

Choice:

- Lovable for generation and test acceleration, manual polish for signature interactions.

Why best:

- Speed without sacrificing distinctiveness.

Tradeoff:

- Generated code can be generic if prompts are weak.

Mitigation:

- Use strict visual language and motion specs from `04-ui-excellence-system.md`.

## 6) Signature Moves (High-Impact Differentiators)

1. Evidence Trace Rail:
   Every node click reveals exact files, symbols, and reasoning steps.
2. Bidirectional Time-Travel Graph:
   Visualize before/after topology for repo revisions.
3. Risk Constellation Overlay:
   Overlay cyclomatic complexity, change frequency, and test coverage as one visual heat field.
4. What-if Copilot:
   Query impact paths before code changes (example: lead assignment modification blast radius).

These are intentionally judge-visible features that combine intelligence and visual elegance.

## 7) Scope Guardrails

Do now:

- Python parsing
- Core workflow extraction
- CRUD lineage on 3-5 entities
- Risk dashboard and copilot Q and A

Defer:

- Full PHP and JS coverage
- Full symbolic execution
- Runtime tracing instrumentation

## 8) Exit Criteria for Planning Phase

Planning phase is complete when:

1. Architecture boundaries are fixed.
2. Data contracts are fixed.
3. 48-hour execution plan is accepted.
4. UI direction and motion language are fixed.
5. Tool responsibilities (CodeWords, Dust, Lovable) are fixed.

## 9) References Used for Design Confidence

- CodeWords docs: core concepts, schedules/triggers, workflows API, webhooks, integrations.
- Dust docs: run_agent, triggers, developer platform, MCP docs integration patterns.
- Lovable docs: plan mode, integrations, browser testing.


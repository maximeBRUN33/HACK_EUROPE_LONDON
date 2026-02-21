# Testing Strategy and Demo Narrative

## 1) Test Philosophy

Legacy Atlas combines deterministic analysis and AI interpretation.
Testing must therefore validate:

1. Structural correctness
2. Semantic usefulness
3. UX reliability under demo conditions

## 2) Test Pyramid

Unit tests:

- AST parsers
- edge builders
- metric calculators
- schema validators

Integration tests:

- ingestion -> analyzer -> storage pipeline
- analyzer -> Dust enrichment contract
- graph API responses on real repo fixtures

UI smoke tests:

- graph load and drill-down
- risk filter interactions
- copilot question/answer with citations

System tests:

- full run from webhook trigger to UI rendering

## 3) Dataset for Validation

Use controlled fixture set:

1. ERPNext module subset (sales, accounts)
2. Odoo module subset (crm, stock)
3. One moderate-size CRM repo for stress profile

For each fixture:

- Maintain expected key workflows.
- Maintain expected core lineage chains.
- Track top risk files as baseline.

## 4) Objective Quality Metrics

Extraction metrics:

1. Symbol extraction recall on labeled sample (> 0.9 target)
2. Call edge precision on labeled sample (> 0.85 target)
3. Entity extraction precision (> 0.9 target)

Semantic metrics:

1. Workflow label relevance (human review score >= 4/5)
2. Citation validity rate (>= 0.98)

UX metrics:

1. Graph initial render time (< 2.0s)
2. Node expansion latency (< 120ms)
3. Copilot first token latency (< 2.5s median)

## 5) Non-Functional Validation

1. Load test graph APIs with 10 concurrent users.
2. Verify no secrets in logs.
3. Verify graceful degradation if Dust or CodeWords unavailable.
4. Verify retry behavior for webhook and workflow failures.

## 6) Demo Script (7-8 Minutes)

Minute 0-1: Problem framing

- Legacy ERP codebases are hard to comprehend and risky to modify.

Minute 1-3: Process Atlas

- Open sales workflow map.
- Click Sales Confirmation node.
- Show direct links to code evidence.

Minute 3-5: Data lineage and risk

- Show Customer -> Order -> Invoice pathway.
- Overlay risk heat and identify top hotspot.

Minute 5-6: Copilot impact reasoning

- Ask "What happens if lead assignment logic changes?"
- Show cited impact chain and risk implications.

Minute 6-7: Operational credibility

- Show automated run triggered by CodeWords.
- Show Dust semantic layer output with traceability.

Minute 7-8: Vision extension

- Show planned language expansion and migration readiness module.

## 7) Judge-Facing Narrative Anchors

1. "Trustworthy AI": deterministic extraction + cited semantic layer.
2. "Beautiful intelligence": premium interaction design with useful motion.
3. "Operationally real": event-driven workflows, not a toy script.
4. "Enterprise relevance": immediate value on ERP/CRM modernization.

## 8) Go/No-Go Checklist (1 Hour Before Pitch)

1. All demo routes preloaded and tested.
2. Fallback snapshot ready if live scan fails.
3. Copilot has at least three rehearsed deterministic questions.
4. Metrics and architecture slide aligned with live product behavior.
5. Team speaking order and handoff cues rehearsed twice.

## 9) Post-Hackathon Continuation Path

1. Add PHP parser adapter.
2. Add revision diff engine for architecture drift timeline.
3. Add migration assistant module for framework upgrades.
4. Pilot with one internal legacy system for validation.


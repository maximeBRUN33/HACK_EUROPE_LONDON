# Legacy Atlas: Software Overview and Technical Documentation

## 1) What the Software Does

Legacy Atlas helps developers understand legacy ERP/CRM systems by turning source code into:
- a **process view** (how business operations are executed),
- a **data movement view** (how business data travels),
- a **risk view** (what is fragile or costly to change),
- and a **developer assistant view** (answers with evidence and impact context).

The goal is to move teams from "we don't understand this code" to "we know what it does, where risks are, and how to migrate safely."

## 2) UI Language (As Seen in the Product)

This documentation uses the same terms users see in the interface:
- `Repository Mission Control`
- `Process Atlas`
- `Data Lineage Navigator`
- `Risk Observatory`
- `Developer Copilot`

Pipeline words shown in UI:
- `Ingesting`
- `Parsing AST`
- `Building Graphs`
- `Persisting`
- `Completed`

## 3) Core Concepts (Plain Definitions)

### AST
**AST** means **Abstract Syntax Tree**.
It is a structured representation of code (functions, classes, calls, control blocks) built by parsing source files.

Why it matters:
- It lets Legacy Atlas reason about code structure reliably.
- It is the base layer before semantic interpretation.

### Entity
An **entity** is a business object represented in code and/or data models.
Examples: `Customer`, `Lead`, `Order`, `Invoice`, `Payment`.

Why it matters:
- Entities are the anchors for data lineage and migration boundaries.

### Workflow (Code Sense)
A **workflow in code** is an execution chain:
entry point -> function calls -> validations -> persistence/integration actions.

### Workflow (Business Sense)
A **workflow in business terms** is an operational process:
for example, `Lead -> Quote -> Order -> Invoice`.

Why both matter:
- The software maps low-level code chains to business-meaningful process steps.

### Process Node
A **process node** is a graph node representing a meaningful step in execution.
It usually corresponds to an extracted function/symbol cluster that participates in a business process.

### Node
A **node** is a point in a graph.
In this product, nodes can represent:
- process steps,
- data entities,
- or risk aggregation points.

### Edge
An **edge** is a connection between nodes.
In this product, edges represent relationships such as:
- control flow (execution relation),
- data flow (entity movement relation),
- risk linkage.

### Lineage
**Lineage** describes how data moves and transforms across steps and modules.
It shows "where a data object comes from, where it goes, and through which logic."

### Evidence
**Evidence** is the traceability layer: files, symbols, and explanations attached to a node.
It is what turns a visual claim into something verifiable in code.

## 4) Workflow Graph: What It Is and What It Shows

The **Workflow Graph** (`Process Atlas` in UI) is a process-centric map of system behavior.

It answers:
- What are the main business process steps?
- How do process steps call or trigger each other?
- Where are risky execution hotspots?

Key elements in this graph:
- **Process nodes**: extracted execution steps.
- **Risk nodes**: high-risk aggregation or hotspots.
- **Control edges**: execution relationships.
- **Risk edges**: risk linkage to key process areas.

Business value:
- Speeds up understanding of "how this system works end-to-end."
- Supports impact reasoning before code changes.

## 5) Lineage Graph: What It Is and What It Shows

The **Lineage Graph** (`Data Lineage Navigator` in UI) is a data-centric map.

It answers:
- How does a business entity move through the system?
- Which entities are linked in operational flow?
- Where are sensitive handoffs between modules?

Key elements in this graph:
- **Entity nodes**: business data objects.
- **Data edges**: inferred transitions/transformations between entities.

Business value:
- Makes integration and migration planning concrete.
- Reveals high-impact data pathways that must be preserved.

## 6) How Legacy Atlas Builds Meaning from Code

1. **Source Resolution**
- Uses local repository source when available.
- Otherwise resolves source from remote clone and branch logic.

2. **Structural Extraction (AST Layer)**
- Parses code into syntax trees.
- Extracts symbols, call relations, complexity/coupling signals, and entity hints.

3. **Graph Construction**
- Builds workflow graph (process behavior).
- Builds lineage graph (entity/data movement).

4. **Risk Construction**
- Scores risk dimensions such as complexity, coupling, dead-code likelihood, and test-gap signals.

5. **Semantic Enrichment**
- Uses AI enrichment to improve business-level interpretation and migration hints.
- Keeps deterministic fallback behavior to remain robust when external enrichment is unavailable.

6. **Migration Intelligence**
- Computes readiness posture.
- Proposes extraction boundaries.
- Produces phased migration guidance.

## 7) Current Capability Maturity

Strong today:
- Deterministic structural analysis.
- Process and lineage graph generation.
- Risk and evidence layer.
- Migration guidance baseline (readiness + boundaries + phased plan).
- Copilot with grounded fallback behavior.

Still evolving:
- Deeper impact simulation ("what breaks if I change X?").
- Richer migration export artifacts and scenario simulation.
- Full UI coverage for all backend-produced intelligence surfaces.

## 8) Practical Interpretation Guide

When reading outputs:
- Start with `Repository Mission Control` to confirm run status and analysis mode.
- Use `Process Atlas` to understand behavior sequences.
- Use `Data Lineage Navigator` to understand entity movement and integration pressure points.
- Use `Risk Observatory` to prioritize safe change order.
- Use `Developer Copilot` to turn findings into concrete engineering decisions.

## 9) Glossary Summary (Quick Reference)

- **AST**: parsed structural representation of source code.
- **Entity**: business object represented in code/data.
- **Workflow**: execution chain in code; business process in product language.
- **Node**: graph point representing process/data/risk unit.
- **Edge**: relationship between nodes (control/data/risk).
- **Lineage**: path of data movement and transformation.
- **Evidence**: code references supporting a graph claim.

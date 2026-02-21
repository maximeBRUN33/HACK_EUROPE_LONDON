from __future__ import annotations

import os
from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone
from hashlib import sha1, sha256
from pathlib import Path

from app.models import AnalysisRun, Edge, EvidencePayload, GraphPayload, Node, Repository, RiskFinding, RiskSummaryPayload, RunStatus
from app.services.python_ast import (
    ParsedFunction,
    ParsedRepository,
    analyze_python_repository,
    build_call_graph,
    compute_degrees,
    count_entities,
)
from app.services.semantic import SemanticEnricher
from app.store import store

ENTRYPOINT_HINTS = ("confirm", "submit", "process", "assign", "post", "create", "run", "execute")

MIGRATION_SUGGESTIONS: dict[str, list[str]] = {
    "complexity": [
        "Refactor into smaller functions with single responsibility",
        "Extract service layer to isolate business logic",
    ],
    "coupling": [
        "Introduce interface boundary between modules",
        "Apply dependency injection to decouple components",
    ],
    "dead_code": [
        "Safe to remove after verifying no runtime references",
        "Archive and monitor for regression",
    ],
    "test_gap": [
        "Add unit tests for critical business logic paths",
        "Prioritize integration tests for high-risk flows",
    ],
}


def _entity_from_repo_name(name: str) -> str:
    normalized = name.lower()
    if "erp" in normalized:
        return "Order"
    if "crm" in normalized:
        return "Lead"
    return "Document"


def _hash_to_score(*values: str, min_value: float, max_value: float) -> float:
    digest = sha256("::".join(values).encode("utf-8")).hexdigest()
    ratio = int(digest[:8], 16) / 0xFFFFFFFF
    return round(min_value + (max_value - min_value) * ratio, 2)


def _slug(text: str) -> str:
    chars = [char.lower() if char.isalnum() else "-" for char in text]
    normalized = "".join(chars)
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    return normalized.strip("-") or "node"


def _node_id(prefix: str, value: str) -> str:
    digest = sha1(value.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{digest}"


def _severity(score: float) -> str:
    if score >= 85:
        return "critical"
    if score >= 70:
        return "high"
    if score >= 50:
        return "medium"
    return "low"


def _resolve_repo_root(repo: Repository) -> Path | None:
    candidates: list[Path] = []
    if repo.local_path:
        candidates.append(Path(repo.local_path).expanduser())

    roots = os.getenv("LEGACY_ATLAS_REPO_ROOTS", "")
    for root in (item for item in roots.split(os.pathsep) if item.strip()):
        root_path = Path(root).expanduser()
        candidates.append(root_path / repo.name)
        candidates.append(root_path / repo.owner / repo.name)

    for candidate in candidates:
        if candidate.is_dir() and any(candidate.rglob("*.py")):
            return candidate
    return None


def _workflow_rank(function: ParsedFunction, out_degree: dict[str, int]) -> float:
    bonus = 0.0
    lowered = function.short_name.lower()
    if any(token in lowered for token in ENTRYPOINT_HINTS):
        bonus += 6.0
    bonus += len(function.entities) * 1.5
    bonus += len(function.crud_ops) * 1.0
    return function.complexity * 2.4 + out_degree.get(function.qname, 0) * 1.8 + bonus


def _select_workflow_functions(
    parsed: ParsedRepository,
    out_degree: dict[str, int],
    max_count: int = 8,
) -> list[ParsedFunction]:
    ranked = sorted(parsed.functions, key=lambda fn: _workflow_rank(fn, out_degree), reverse=True)
    return ranked[: max_count if len(ranked) >= max_count else len(ranked)]


def _build_workflow_graph_from_ast(
    run: AnalysisRun,
    parsed: ParsedRepository,
    call_edges: list[tuple[str, str]],
    out_degree: dict[str, int],
) -> tuple[GraphPayload, dict[str, ParsedFunction]]:
    selected = _select_workflow_functions(parsed, out_degree)
    if not selected:
        return GraphPayload(run_id=run.id, nodes=[], edges=[]), {}

    node_map: dict[str, ParsedFunction] = {}
    qname_to_id: dict[str, str] = {}
    nodes: list[Node] = []

    for function in selected:
        node_id = _node_id("wf", function.qname)
        score = round(min(95.0, 15 + function.complexity * 4 + out_degree.get(function.qname, 0) * 3), 2)
        qname_to_id[function.qname] = node_id
        node_map[node_id] = function
        nodes.append(
            Node(
                id=node_id,
                label=function.short_name.replace("_", " ").title(),
                node_type="risk" if score >= 75 else "process",
                risk_score=score,
            )
        )

    edges: list[Edge] = []
    for source, target in call_edges:
        if source in qname_to_id and target in qname_to_id and source != target:
            edges.append(
                Edge(
                    source=qname_to_id[source],
                    target=qname_to_id[target],
                    edge_type="control",
                    confidence=0.88,
                )
            )

    if not edges and len(nodes) > 1:
        for first, second in zip(nodes, nodes[1:], strict=False):
            edges.append(Edge(source=first.id, target=second.id, edge_type="control", confidence=0.62))

    return GraphPayload(run_id=run.id, nodes=nodes, edges=edges), node_map


def _build_lineage_graph_from_ast(run: AnalysisRun, parsed: ParsedRepository) -> tuple[GraphPayload, dict[str, list[ParsedFunction]]]:
    entity_counts = count_entities(parsed.functions)
    if not entity_counts:
        default = _entity_from_repo_name(parsed.root_path.name)
        entity_counts = Counter({"Customer": 2, default: 2, "Invoice": 1})

    top_entities = [entity for entity, _count in entity_counts.most_common(6)]
    node_ids = {entity: f"entity-{_slug(entity)}" for entity in top_entities}

    entity_functions: dict[str, list[ParsedFunction]] = {entity: [] for entity in top_entities}
    for function in parsed.functions:
        for entity in function.entities:
            if entity in entity_functions:
                entity_functions[entity].append(function)

    nodes = [
        Node(
            id=node_ids[entity],
            label=entity,
            node_type="data",
            risk_score=round(min(70.0, 8 + entity_counts[entity] * 9), 2),
        )
        for entity in top_entities
    ]

    transitions: Counter[tuple[str, str]] = Counter()
    for function in parsed.functions:
        sequence = [entity for entity in function.entity_sequence if entity in node_ids]
        compressed: list[str] = []
        for entity in sequence:
            if not compressed or compressed[-1] != entity:
                compressed.append(entity)

        for source, target in zip(compressed, compressed[1:], strict=False):
            if source != target:
                transitions[(source, target)] += 1

    edges: list[Edge] = []
    if transitions:
        for (source, target), weight in transitions.most_common(12):
            confidence = round(min(0.98, 0.55 + weight * 0.08), 2)
            edges.append(
                Edge(
                    source=node_ids[source],
                    target=node_ids[target],
                    edge_type="data",
                    confidence=confidence,
                )
            )
    elif len(nodes) > 1:
        for first, second in zip(nodes, nodes[1:], strict=False):
            edges.append(Edge(source=first.id, target=second.id, edge_type="data", confidence=0.6))

    return GraphPayload(run_id=run.id, nodes=nodes, edges=edges), entity_functions


def _build_risk_summary_from_ast(
    run: AnalysisRun,
    parsed: ParsedRepository,
    call_edges: list[tuple[str, str]],
) -> RiskSummaryPayload:
    out_degree, in_degree = compute_degrees(call_edges)
    findings: list[RiskFinding] = []

    most_complex = sorted(parsed.functions, key=lambda function: function.complexity, reverse=True)[:3]
    for index, function in enumerate(most_complex, start=1):
        score = round(min(98.0, 20 + function.complexity * 5 + out_degree.get(function.qname, 0) * 2), 2)
        findings.append(
            RiskFinding(
                id=f"complexity-{index}",
                category="complexity",
                severity=_severity(score),
                score=score,
                title=f"High complexity in {function.short_name}",
                rationale=(
                    f"Cyclomatic estimate {function.complexity} with outbound dependency count "
                    f"{out_degree.get(function.qname, 0)}."
                ),
                symbol=function.qname,
                migration_suggestions=MIGRATION_SUGGESTIONS["complexity"],
            )
        )

    if parsed.functions:
        most_coupled = max(parsed.functions, key=lambda function: out_degree.get(function.qname, 0) + in_degree.get(function.qname, 0))
        coupling_score = round(min(95.0, 35 + (out_degree.get(most_coupled.qname, 0) + in_degree.get(most_coupled.qname, 0)) * 7), 2)
        findings.append(
            RiskFinding(
                id="coupling-1",
                category="coupling",
                severity=_severity(coupling_score),
                score=coupling_score,
                title="Coupling hotspot across modules",
                rationale=(
                    f"Function has in/out call degree {in_degree.get(most_coupled.qname, 0)}/"
                    f"{out_degree.get(most_coupled.qname, 0)}."
                ),
                symbol=most_coupled.qname,
                migration_suggestions=MIGRATION_SUGGESTIONS["coupling"],
            )
        )

    dead_candidates = [
        function
        for function in parsed.functions
        if in_degree.get(function.qname, 0) == 0
        and out_degree.get(function.qname, 0) == 0
        and function.complexity >= 3
        and not any(token in function.short_name.lower() for token in ENTRYPOINT_HINTS)
    ]
    if dead_candidates:
        dead = dead_candidates[0]
        dead_score = round(min(88.0, 28 + dead.complexity * 6), 2)
        findings.append(
            RiskFinding(
                id="dead-code-1",
                category="dead_code",
                severity=_severity(dead_score),
                score=dead_score,
                title="Potential dead code path",
                rationale="No inbound and outbound calls observed in static call graph approximation.",
                symbol=dead.qname,
                migration_suggestions=MIGRATION_SUGGESTIONS["dead_code"],
            )
        )

    has_tests = any("test" in function.file_path.lower() for function in parsed.functions)
    if not has_tests and most_complex:
        gap = most_complex[0]
        gap_score = round(min(94.0, 55 + gap.complexity * 3), 2)
        findings.append(
            RiskFinding(
                id="test-gap-1",
                category="test_gap",
                severity=_severity(gap_score),
                score=gap_score,
                title="Limited test coverage signals",
                rationale="No test files detected in scanned Python paths while critical logic is complex.",
                symbol=gap.qname,
                migration_suggestions=MIGRATION_SUGGESTIONS["test_gap"],
            )
        )

    if not findings:
        findings = [
            RiskFinding(
                id="complexity-fallback",
                category="complexity",
                severity="low",
                score=20.0,
                title="Low confidence risk snapshot",
                rationale="Repository contained too few Python symbols for robust risk scoring.",
                symbol="n/a",
                migration_suggestions=MIGRATION_SUGGESTIONS["complexity"],
            )
        ]

    overall_score = round(sum(item.score for item in findings) / len(findings), 2)
    return RiskSummaryPayload(run_id=run.id, overall_score=overall_score, findings=findings)


def _build_evidence_from_ast(
    run: AnalysisRun,
    workflow_node_map: dict[str, ParsedFunction],
    entity_functions: dict[str, list[ParsedFunction]],
    risk_summary: RiskSummaryPayload,
) -> dict[str, EvidencePayload]:
    evidences: dict[str, EvidencePayload] = {}

    for node_id, function in workflow_node_map.items():
        evidences[node_id] = EvidencePayload(
            run_id=run.id,
            node_id=node_id,
            files=[function.file_path],
            symbols=[function.qname, *function.calls[:2]],
            explanation=(
                f"Workflow node extracted from function `{function.qname}` with complexity {function.complexity} "
                f"and {len(function.calls)} detected calls."
            ),
        )

    for entity, functions in entity_functions.items():
        node_id = f"entity-{_slug(entity)}"
        if not functions:
            continue
        evidences[node_id] = EvidencePayload(
            run_id=run.id,
            node_id=node_id,
            files=sorted({function.file_path for function in functions[:5]}),
            symbols=[function.qname for function in functions[:3]],
            explanation=(
                f"Entity `{entity}` inferred from symbols that include entity tokens and CRUD operations "
                f"({', '.join(sorted(functions[0].crud_ops)) or 'no explicit CRUD token'})."
            ),
        )

    top = max(risk_summary.findings, key=lambda finding: finding.score)
    evidences["risk-hub"] = EvidencePayload(
        run_id=run.id,
        node_id="risk-hub",
        files=[top.symbol.split(".")[0] + ".py" if "." in top.symbol else "unknown.py"],
        symbols=[finding.symbol for finding in risk_summary.findings[:3]],
        explanation="Risk hub combines complexity, coupling, dead-code and test-gap signals from static analysis.",
    )

    return evidences


def _build_fallback_workflow(run: AnalysisRun, repo: Repository) -> GraphPayload:
    core_entity = _entity_from_repo_name(repo.name)
    return GraphPayload(
        run_id=run.id,
        nodes=[
            Node(id="ingest", label="Repository Ingestion", node_type="process", risk_score=8.0),
            Node(id="parse", label="Python AST Parse", node_type="process", risk_score=12.0),
            Node(id="workflow", label=f"{core_entity} Workflow Mapper", node_type="process", risk_score=24.0),
            Node(id="risk-hub", label="Risk Aggregator", node_type="risk", risk_score=31.0),
        ],
        edges=[
            Edge(source="ingest", target="parse", edge_type="control", confidence=0.98),
            Edge(source="parse", target="workflow", edge_type="control", confidence=0.92),
            Edge(source="workflow", target="risk-hub", edge_type="risk", confidence=0.86),
        ],
    )


def _build_fallback_lineage(run: AnalysisRun, repo: Repository) -> GraphPayload:
    core = _entity_from_repo_name(repo.name)
    return GraphPayload(
        run_id=run.id,
        nodes=[
            Node(id="entity-customer", label="Customer", node_type="data", risk_score=14.0),
            Node(id=f"entity-{_slug(core)}", label=core, node_type="data", risk_score=22.0),
            Node(id="entity-invoice", label="Invoice", node_type="data", risk_score=18.0),
        ],
        edges=[
            Edge(source="entity-customer", target=f"entity-{_slug(core)}", edge_type="data", confidence=0.93),
            Edge(source=f"entity-{_slug(core)}", target="entity-invoice", edge_type="data", confidence=0.9),
        ],
    )


def _build_fallback_risk(run: AnalysisRun, repo: Repository) -> RiskSummaryPayload:
    findings = [
        RiskFinding(
            id="rf-1",
            category="complexity",
            severity="high",
            score=_hash_to_score(repo.name, "complexity", min_value=60.0, max_value=88.0),
            title="Static analysis fallback risk",
            rationale="Local repository path not available, so risk score is estimated from metadata heuristics.",
            symbol=f"{repo.name}.fallback",
            migration_suggestions=MIGRATION_SUGGESTIONS["complexity"],
        )
    ]
    return RiskSummaryPayload(run_id=run.id, overall_score=findings[0].score, findings=findings)


def run_static_analysis(
    run: AnalysisRun,
    repo: Repository,
    progress_cb: Callable[[str, float], None] | None = None,
) -> AnalysisRun:
    def update_progress(step: str, pct: float) -> None:
        if progress_cb is not None:
            progress_cb(step, pct)

    run.status = RunStatus.running
    run.started_at = run.started_at or datetime.now(timezone.utc)
    run.current_step = "resolving-source"
    run.progress_pct = 15.0
    update_progress("resolving-source", 15.0)

    repo_root = _resolve_repo_root(repo)
    if repo_root:
        run.current_step = "parsing-python-ast"
        run.progress_pct = 35.0
        update_progress("parsing-python-ast", 35.0)
        parsed = analyze_python_repository(repo_root)
        call_edges = build_call_graph(parsed.functions)
        out_degree, _in_degree = compute_degrees(call_edges)

        run.current_step = "building-graphs"
        run.progress_pct = 62.0
        update_progress("building-graphs", 62.0)
        workflow_graph, workflow_node_map = _build_workflow_graph_from_ast(run, parsed, call_edges, out_degree)
        lineage_graph, entity_functions = _build_lineage_graph_from_ast(run, parsed)
        risk_summary = _build_risk_summary_from_ast(run, parsed, call_edges)

        if workflow_graph.nodes:
            workflow_graph.nodes.append(Node(id="risk-hub", label="Risk Aggregator", node_type="risk", risk_score=risk_summary.overall_score))
            if workflow_graph.nodes:
                highest = max((node for node in workflow_graph.nodes if node.id != "risk-hub"), key=lambda item: item.risk_score, default=None)
                if highest is not None:
                    workflow_graph.edges.append(Edge(source=highest.id, target="risk-hub", edge_type="risk", confidence=0.84))

        evidences = _build_evidence_from_ast(run, workflow_node_map, entity_functions, risk_summary)
        mode = "ast-local"

        run.summary = {
            "workflow_nodes": len(workflow_graph.nodes),
            "lineage_edges": len(lineage_graph.edges),
            "risk_findings": len(risk_summary.findings),
            "files_scanned": parsed.files_scanned,
            "functions_scanned": len(parsed.functions),
            "parse_errors": len(parsed.parse_errors),
            "analysis_mode": mode,
            "repo_root": str(repo_root),
        }
    else:
        run.current_step = "fallback-analysis"
        run.progress_pct = 55.0
        update_progress("fallback-analysis", 55.0)
        workflow_graph = _build_fallback_workflow(run, repo)
        lineage_graph = _build_fallback_lineage(run, repo)
        risk_summary = _build_fallback_risk(run, repo)

        evidences = {
            "workflow": EvidencePayload(
                run_id=run.id,
                node_id="workflow",
                files=["n/a"],
                symbols=["n/a"],
                explanation="Fallback evidence. Provide local_path on repository registration for real AST-backed evidence.",
            ),
            "risk-hub": EvidencePayload(
                run_id=run.id,
                node_id="risk-hub",
                files=["n/a"],
                symbols=["n/a"],
                explanation="Fallback risk evidence. Real scoring requires scanning a local Python repository clone.",
            ),
        }

        run.summary = {
            "workflow_nodes": len(workflow_graph.nodes),
            "lineage_edges": len(lineage_graph.edges),
            "risk_findings": len(risk_summary.findings),
            "analysis_mode": "fallback",
            "note": "No local repository path resolved. Register repository with local_path or set LEGACY_ATLAS_REPO_ROOTS.",
        }

    run.current_step = "persisting-artifacts"
    run.progress_pct = 85.0
    update_progress("persisting-artifacts", 85.0)

    store.save_workflow_graph(run.id, workflow_graph)
    store.save_lineage_graph(run.id, lineage_graph)
    store.save_risk_summary(run.id, risk_summary)

    for node_id, payload in evidences.items():
        store.save_evidence(run.id, node_id, payload)

    if repo_root:
        enricher = SemanticEnricher()
        if enricher.is_available():
            run.current_step = "semantic-enrichment"
            run.progress_pct = 90.0
            update_progress("semantic-enrichment", 90.0)

            enricher.enrich_workflow_graph(run, workflow_graph, workflow_node_map)
            enricher.enrich_risk_summary(run, risk_summary)

    run.status = RunStatus.completed
    run.current_step = "completed"
    run.progress_pct = 100.0
    run.finished_at = run.finished_at or datetime.now(timezone.utc)
    store.save_run(run)
    update_progress("completed", 100.0)
    return run


def create_placeholder_summary(repo: Repository, commit_sha: str) -> dict[str, str]:
    return {
        "repo": repo.name,
        "commit_sha": commit_sha,
        "status": "queued",
        "note": "Run created. Analyzer will use AST mode when local repository path is available.",
    }

from __future__ import annotations

from app.models import (
    AnalysisRun,
    EnrichmentPayload,
    GraphPayload,
    MigrationBlueprintPayload,
    MigrationBlueprintPhase,
    RiskSummaryPayload,
)


def build_migration_blueprint(
    run: AnalysisRun,
    risk_summary: RiskSummaryPayload,
    lineage_graph: GraphPayload,
    enrichment: EnrichmentPayload | None,
) -> MigrationBlueprintPayload:
    summary = run.summary if isinstance(run.summary, dict) else {}
    migration = summary.get("migration") if isinstance(summary.get("migration"), dict) else {}
    ontology = summary.get("ontology") if isinstance(summary.get("ontology"), dict) else {}

    readiness_score = _coerce_float(migration.get("readiness_score"), default=max(0.0, 100.0 - risk_summary.overall_score))
    readiness_band = _readiness_band(readiness_score)

    entities = _coerce_string_list(ontology.get("top_entities"))
    impacted_modules = _coerce_string_list(migration.get("impacted_modules"))
    extraction_boundaries = _coerce_dict_list(migration.get("extraction_boundaries"))
    rerouting_risks = _coerce_string_list(migration.get("rerouting_risks"))

    inbound_count = _coerce_int(ontology.get("integration_inbound_count"), 0)
    outbound_count = _coerce_int(ontology.get("integration_outbound_count"), 0)
    integration_routing = {
        "inbound_touchpoints": inbound_count,
        "outbound_touchpoints": outbound_count,
        "lineage_edges": len(lineage_graph.edges),
        "rerouting_risks": rerouting_risks,
    }

    top_risks = _top_risks(risk_summary)
    recommendations = _collect_recommendations(risk_summary, rerouting_risks)
    phased_plan = _build_phases(
        impacted_modules=impacted_modules,
        extraction_boundaries=extraction_boundaries,
        rerouting_risks=rerouting_risks,
        recommendations=recommendations,
        enrichment=enrichment,
    )

    return MigrationBlueprintPayload(
        run_id=run.id,
        analysis_mode=str(summary.get("analysis_mode") or "unknown"),
        readiness_score=round(readiness_score, 2),
        readiness_band=readiness_band,
        entities=entities,
        impacted_modules=impacted_modules,
        extraction_boundaries=extraction_boundaries,
        integration_routing=integration_routing,
        top_risks=top_risks,
        recommendations=recommendations,
        phased_plan=phased_plan,
        enrichment_status=enrichment.status if enrichment else None,
    )


def _build_phases(
    *,
    impacted_modules: list[str],
    extraction_boundaries: list[dict],
    rerouting_risks: list[str],
    recommendations: list[str],
    enrichment: EnrichmentPayload | None,
) -> list[MigrationBlueprintPhase]:
    boundary_priority = []
    if enrichment and isinstance(enrichment.migration_hints, dict):
        boundary_priority = _coerce_string_list(enrichment.migration_hints.get("boundary_priority"))

    phase_1 = MigrationBlueprintPhase(
        phase_id="phase-1",
        title="Stabilize and Scope",
        objective="Lock current behavior and scope the extraction surface.",
        actions=[
            "Freeze contracts on inbound and outbound integrations.",
            "Capture baseline metrics and representative regression tests.",
            "Confirm candidate modules and ownership boundaries.",
        ],
        success_criteria=[
            "Baseline test suite and telemetry are green.",
            "Migration scope is approved by owners.",
        ],
        impacted_modules=impacted_modules[:6],
        risk_watch=rerouting_risks[:2],
    )

    boundary_actions = [
        f"Extract boundary anchor `{item.get('anchor_symbol', 'unknown')}` with explicit interface."
        for item in extraction_boundaries[:3]
    ]
    if boundary_priority:
        boundary_actions.append(f"Follow boundary priority order: {', '.join(boundary_priority[:4])}.")

    phase_2 = MigrationBlueprintPhase(
        phase_id="phase-2",
        title="Extract and Adapt",
        objective="Move bounded modules behind adapters and preserve integration contracts.",
        actions=boundary_actions or ["Extract first bounded context and introduce adapter layer."],
        success_criteria=[
            "Primary boundary extracted with backward-compatible adapter.",
            "Critical integration paths pass smoke tests.",
        ],
        impacted_modules=impacted_modules[:8],
        risk_watch=rerouting_risks[:3],
    )

    phase_3 = MigrationBlueprintPhase(
        phase_id="phase-3",
        title="Cutover and Harden",
        objective="Switch production traffic safely and decommission legacy paths incrementally.",
        actions=[
            "Perform staged traffic cutover with rollback guardrails.",
            "Retire deprecated paths after post-cutover validation.",
            "Track residual risks and schedule follow-up refactors.",
        ],
        success_criteria=[
            "Cutover completed with no high-severity regressions.",
            "Legacy pathways are decommissioned or isolated.",
        ],
        impacted_modules=impacted_modules[:10],
        risk_watch=recommendations[:3],
    )

    return [phase_1, phase_2, phase_3]


def _collect_recommendations(risk_summary: RiskSummaryPayload, rerouting_risks: list[str]) -> list[str]:
    recommendations: list[str] = []
    for finding in risk_summary.findings:
        for suggestion in finding.migration_suggestions[:2]:
            if suggestion not in recommendations:
                recommendations.append(suggestion)

    for risk in rerouting_risks:
        if risk not in recommendations:
            recommendations.append(risk)

    return recommendations[:12]


def _top_risks(risk_summary: RiskSummaryPayload) -> list[dict]:
    sorted_findings = sorted(risk_summary.findings, key=lambda item: item.score, reverse=True)
    top: list[dict] = []
    for finding in sorted_findings[:5]:
        top.append(
            {
                "id": finding.id,
                "category": finding.category,
                "severity": finding.severity,
                "score": finding.score,
                "title": finding.title,
                "symbol": finding.symbol,
            }
        )
    return top


def _readiness_band(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def _coerce_float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_int(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            result.append(text)
    return result


def _coerce_dict_list(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]

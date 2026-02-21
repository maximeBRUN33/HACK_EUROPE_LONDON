from fastapi import APIRouter

from app.errors import api_error
from app.models import EnrichmentPayload, EvidencePayload, GraphPayload, MigrationBlueprintPayload, RiskSummaryPayload
from app.services.migration_blueprint import build_migration_blueprint
from app.store import store

router = APIRouter(prefix="/api/runs", tags=["graphs"])


@router.get("/{run_id}/workflow-graph", response_model=GraphPayload)
def get_workflow_graph(run_id: str) -> GraphPayload:
    graph = store.get_workflow_graph(run_id)
    if graph is None:
        raise api_error(status_code=404, detail_code="WORKFLOW_GRAPH_NOT_FOUND", message="Workflow graph not found")
    return graph


@router.get("/{run_id}/lineage-graph", response_model=GraphPayload)
def get_lineage_graph(run_id: str) -> GraphPayload:
    graph = store.get_lineage_graph(run_id)
    if graph is None:
        raise api_error(status_code=404, detail_code="LINEAGE_GRAPH_NOT_FOUND", message="Lineage graph not found")
    return graph


@router.get("/{run_id}/risk-summary", response_model=RiskSummaryPayload)
def get_risk_summary(run_id: str) -> RiskSummaryPayload:
    summary = store.get_risk_summary(run_id)
    if summary is None:
        raise api_error(status_code=404, detail_code="RISK_SUMMARY_NOT_FOUND", message="Risk summary not found")
    return summary


@router.get("/{run_id}/node/{node_id}/evidence", response_model=EvidencePayload)
def get_node_evidence(run_id: str, node_id: str) -> EvidencePayload:
    run = store.get_run(run_id)
    if run is None:
        raise api_error(status_code=404, detail_code="RUN_NOT_FOUND", message="Run not found")

    payload = store.get_evidence(run_id, node_id)
    if payload is None:
        raise api_error(status_code=404, detail_code="EVIDENCE_NOT_FOUND", message="Evidence not found for node")
    return payload


@router.get("/{run_id}/enrichment", response_model=EnrichmentPayload)
def get_run_enrichment(run_id: str) -> EnrichmentPayload:
    run = store.get_run(run_id)
    if run is None:
        raise api_error(status_code=404, detail_code="RUN_NOT_FOUND", message="Run not found")

    payload = store.get_enrichment(run_id)
    if payload is None:
        raise api_error(status_code=404, detail_code="ENRICHMENT_NOT_FOUND", message="Enrichment not found")
    return payload


@router.get("/{run_id}/migration-blueprint", response_model=MigrationBlueprintPayload)
def get_migration_blueprint(run_id: str) -> MigrationBlueprintPayload:
    run = store.get_run(run_id)
    if run is None:
        raise api_error(status_code=404, detail_code="RUN_NOT_FOUND", message="Run not found")

    risk = store.get_risk_summary(run_id)
    lineage = store.get_lineage_graph(run_id)
    if risk is None or lineage is None:
        raise api_error(
            status_code=400,
            detail_code="MIGRATION_ARTIFACTS_NOT_READY",
            message="Run exists but migration artifacts are not ready",
        )

    enrichment = store.get_enrichment(run_id)
    return build_migration_blueprint(run=run, risk_summary=risk, lineage_graph=lineage, enrichment=enrichment)

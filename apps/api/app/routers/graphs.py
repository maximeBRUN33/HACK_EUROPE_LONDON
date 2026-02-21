from fastapi import APIRouter, HTTPException

from app.models import EvidencePayload, GraphPayload, RiskSummaryPayload
from app.store import store

router = APIRouter(prefix="/api/runs", tags=["graphs"])


@router.get("/{run_id}/workflow-graph", response_model=GraphPayload)
def get_workflow_graph(run_id: str) -> GraphPayload:
    graph = store.get_workflow_graph(run_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Workflow graph not found")
    return graph


@router.get("/{run_id}/lineage-graph", response_model=GraphPayload)
def get_lineage_graph(run_id: str) -> GraphPayload:
    graph = store.get_lineage_graph(run_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Lineage graph not found")
    return graph


@router.get("/{run_id}/risk-summary", response_model=RiskSummaryPayload)
def get_risk_summary(run_id: str) -> RiskSummaryPayload:
    summary = store.get_risk_summary(run_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Risk summary not found")
    return summary


@router.get("/{run_id}/node/{node_id}/evidence", response_model=EvidencePayload)
def get_node_evidence(run_id: str, node_id: str) -> EvidencePayload:
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    payload = store.get_evidence(run_id, node_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Evidence not found for node")
    return payload

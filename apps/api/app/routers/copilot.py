import logging

from fastapi import APIRouter, HTTPException

from app.models import CopilotCitation, CopilotRequest, CopilotResponse
from app.services.dust_client import DustClient
from app.store import store

router = APIRouter(prefix="/api/copilot", tags=["copilot"])
logger = logging.getLogger(__name__)


@router.post("/query", response_model=CopilotResponse)
def query_copilot(payload: CopilotRequest) -> CopilotResponse:
    logger.info("Copilot query received run_id=%s focus_node=%s", payload.run_id, payload.focus_node_id or "auto")
    run = store.get_run(str(payload.run_id))
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    risk = store.get_risk_summary(str(payload.run_id))
    graph = store.get_workflow_graph(str(payload.run_id))
    enrichment = store.get_enrichment(str(payload.run_id))

    if risk is None or graph is None:
        raise HTTPException(status_code=400, detail="Run exists but semantic artifacts are not ready")
    if not graph.nodes:
        raise HTTPException(status_code=400, detail="Graph is empty for this run")

    focus = payload.focus_node_id or graph.nodes[0].id
    focus_evidence = store.get_evidence(str(payload.run_id), focus)

    context = {
        "run": {
            "id": str(run.id),
            "status": run.status.value,
            "summary": run.summary,
        },
        "question": payload.question,
        "focus_node_id": focus,
        "workflow_nodes": [node.model_dump() for node in graph.nodes[:12]],
        "workflow_edges": [edge.model_dump() for edge in graph.edges[:20]],
        "risk_findings": [finding.model_dump() for finding in risk.findings[:8]],
        "focus_evidence": focus_evidence.model_dump() if focus_evidence else None,
        "codewords_enrichment": enrichment.model_dump() if enrichment else None,
    }

    node_evidence_map = []
    for node in graph.nodes[:12]:
        ev = store.get_evidence(str(payload.run_id), node.id)
        if ev:
            node_evidence_map.append({
                "node_id": node.id,
                "label": node.label,
                "files": ev.files,
                "symbols": ev.symbols,
                "explanation": ev.explanation,
            })
    context["node_evidence"] = node_evidence_map

    dust = DustClient()
    if dust.is_configured():
        try:
            logger.info("Routing copilot query to Dust run_id=%s", payload.run_id)
            semantic = dust.semantic_copilot(question=payload.question, context=context)
            citations = [
                CopilotCitation(
                    file_path=item["file_path"],
                    symbol=item["symbol"],
                    reason=item["reason"],
                    line_start=item.get("line_start"),
                    line_end=item.get("line_end"),
                )
                for item in semantic.citations
            ]

            if not citations and focus_evidence:
                citations = [
                    CopilotCitation(file_path=file_path, symbol=symbol, reason="Focused evidence from analysis artifact")
                    for file_path, symbol in zip(focus_evidence.files[:3], focus_evidence.symbols[:3], strict=False)
                ]

            if not semantic.answer.strip():
                raise RuntimeError("Dust semantic answer was empty")

            return CopilotResponse(
                answer=semantic.answer,
                citations=citations,
                risk_implications=semantic.risk_implications or ["Dust returned no explicit implications"],
                related_nodes=semantic.related_nodes or [node.id for node in graph.nodes[:5]],
            )
        except RuntimeError as exc:
            # Fall through to local fallback when Dust is temporarily unavailable.
            logger.warning("Dust semantic copilot unavailable; using local fallback run_id=%s error=%s", payload.run_id, exc)
            pass

    top_risk = max(risk.findings, key=lambda finding: finding.score)
    citations: list[CopilotCitation] = []

    if focus_evidence:
        for file_path, symbol in zip(focus_evidence.files[:3], focus_evidence.symbols[:3], strict=False):
            citations.append(
                CopilotCitation(
                    file_path=file_path,
                    symbol=symbol,
                    reason=f"Evidence linked to focused node `{focus}`.",
                )
            )

    if not citations:
        citations.append(
            CopilotCitation(
                file_path=top_risk.symbol.split(".")[0] + ".py" if "." in top_risk.symbol else "unknown.py",
                symbol=top_risk.symbol,
                reason="Highest risk symbol in this run.",
            )
        )

    answer = (
        f"Primary impact area is `{top_risk.symbol}` ({top_risk.severity}, score {top_risk.score}). "
        f"For change around `{focus}`, prioritize tests on dependent calls and data-flow handoffs shown in workflow/lineage graphs."
    )

    related = [node.id for node in graph.nodes[:5]]

    logger.info("Returning local copilot fallback run_id=%s citations=%s", payload.run_id, len(citations))
    return CopilotResponse(
        answer=answer,
        citations=citations,
        risk_implications=[
            f"Top risk category: {top_risk.category}",
            "Potential regressions where control-flow and data-flow intersect",
        ],
        related_nodes=related,
    )

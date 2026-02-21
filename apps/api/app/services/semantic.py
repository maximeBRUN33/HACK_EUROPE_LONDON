from __future__ import annotations

import logging

from app.models import AnalysisRun, GraphPayload, RiskSummaryPayload
from app.services.dust_client import DustClient
from app.services.python_ast import ParsedFunction
from app.store import store

logger = logging.getLogger(__name__)


class SemanticEnricher:
    def __init__(self) -> None:
        self.dust = DustClient()

    def is_available(self) -> bool:
        return self.dust.is_configured()

    def enrich_workflow_graph(
        self,
        run: AnalysisRun,
        graph: GraphPayload,
        node_map: dict[str, ParsedFunction],
    ) -> None:
        if not self.is_available():
            logger.info("Dust not configured, skipping workflow enrichment")
            return

        # Prepare context for Dust
        # Limit to top 20 nodes to avoid huge context window
        target_nodes = graph.nodes[:20]
        context = {
            "nodes": [
                {
                    "id": node.id,
                    "label": node.label,
                    "type": node.node_type,
                    "function_name": node_map[node.id].qname if node.id in node_map else "unknown",
                    "file_path": node_map[node.id].file_path if node.id in node_map else "unknown",
                }
                for node in target_nodes
            ],
            "edges": [edge.model_dump() for edge in graph.edges if edge.source in [n.id for n in target_nodes] and edge.target in [n.id for n in target_nodes]],
        }

        try:
            descriptions = self.dust.semantic_workflow_enrichment(context)
        except Exception:
            logger.exception("Failed to get semantic workflow descriptions")
            return

        # Update evidence
        for node_id, description in descriptions.items():
            # Check if node exists in the graph to avoid hallucinations
            if any(n.id == node_id for n in graph.nodes):
                evidence = store.get_evidence(str(run.id), node_id)
                if evidence:
                    evidence.explanation = f"{description}\n\n(Technical details: {evidence.explanation})"
                    store.save_evidence(run.id, node_id, evidence)

    def enrich_risk_summary(self, run: AnalysisRun, summary: RiskSummaryPayload) -> None:
        if not self.is_available():
            logger.info("Dust not configured, skipping risk enrichment")
            return

        context = {
            "findings": [finding.model_dump() for finding in summary.findings[:10]]
        }

        try:
            assessments = self.dust.semantic_risk_assessment(context)
        except Exception:
            logger.exception("Failed to get semantic risk assessments")
            return

        updated = False
        for finding in summary.findings:
            if finding.id in assessments:
                assessment = assessments[finding.id]
                if assessment.get("title"):
                    finding.title = assessment["title"]
                if assessment.get("rationale"):
                    finding.rationale = assessment["rationale"]
                updated = True

        if updated:
            store.save_risk_summary(run.id, summary)

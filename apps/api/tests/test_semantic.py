from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.models import AnalysisRun, GraphPayload, Node, RiskFinding, RiskSummaryPayload, EvidencePayload
from app.services.semantic import SemanticEnricher
from app.services.python_ast import ParsedFunction


def test_semantic_enricher_workflow() -> None:
    # Setup
    run_id = uuid4()
    run = AnalysisRun(repository_id=uuid4(), commit_sha="sha", id=run_id)
    graph = GraphPayload(
        run_id=run_id,
        nodes=[Node(id="n1", label="test", node_type="process", risk_score=10.0)],
        edges=[]
    )
    node_map = {
        "n1": ParsedFunction(
            qname="module.test",
            short_name="test",
            file_path="module.py",
            line_start=1,
            line_end=10,
            complexity=1,
            calls=[],
            entities=set(),
            entity_sequence=[],
            crud_ops=set(),
        )
    }

    # Mock Evidence
    original_evidence = EvidencePayload(
        run_id=run_id,
        node_id="n1",
        files=["module.py"],
        symbols=["module.test"],
        explanation="Original explanation"
    )

    with patch("app.store.store.get_evidence", return_value=original_evidence):
        with patch("app.store.store.save_evidence") as save_mock:
            # Mock Dust
            with patch("app.services.semantic.DustClient") as DustClientMock:
                client_instance = DustClientMock.return_value
                client_instance.is_configured.return_value = True
                client_instance.semantic_workflow_enrichment.return_value = {
                    "n1": "Enriched description"
                }

                enricher = SemanticEnricher()
                enricher.enrich_workflow_graph(run, graph, node_map)

                # Verify
                client_instance.semantic_workflow_enrichment.assert_called_once()
                save_mock.assert_called_once()
                args, _ = save_mock.call_args
                saved_evidence = args[2]
                assert "Enriched description" in saved_evidence.explanation
                assert "Original explanation" in saved_evidence.explanation


def test_semantic_enricher_risk() -> None:
    # Setup
    run_id = uuid4()
    run = AnalysisRun(repository_id=uuid4(), commit_sha="sha", id=run_id)
    summary = RiskSummaryPayload(
        run_id=run_id,
        overall_score=50.0,
        findings=[
            RiskFinding(
                id="f1",
                category="complexity",
                severity="high",
                score=80.0,
                title="Bad Code",
                rationale="It is bad",
                symbol="module.bad",
            )
        ]
    )

    # Mock Dust
    with patch("app.store.store.save_risk_summary") as save_mock:
        with patch("app.services.semantic.DustClient") as DustClientMock:
            client_instance = DustClientMock.return_value
            client_instance.is_configured.return_value = True
            client_instance.semantic_risk_assessment.return_value = {
                "f1": {"title": "Better Title", "rationale": "Better rationale"}
            }

            enricher = SemanticEnricher()
            enricher.enrich_risk_summary(run, summary)

            # Verify
            client_instance.semantic_risk_assessment.assert_called_once()
            save_mock.assert_called_once()
            args, _ = save_mock.call_args
            saved_summary = args[1]
            assert saved_summary.findings[0].title == "Better Title"
            assert saved_summary.findings[0].rationale == "Better rationale"

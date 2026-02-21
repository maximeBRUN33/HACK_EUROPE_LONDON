import os
from pathlib import Path

from fastapi.testclient import TestClient

os.environ["LEGACY_ATLAS_SYNC_JOBS"] = "1"
os.environ["LEGACY_ATLAS_ENABLE_GIT_INGESTION"] = "0"
os.environ["LEGACY_ATLAS_CODEWORDS_RUNTIME_HOOK"] = "0"

from app.main import app
from app.services.dust_client import DustSemanticResponse
from app.store import store


client = TestClient(app)


def setup_function() -> None:
    store.clear_all()


def _build_sample_python_repo(root: Path) -> None:
    (root / "services").mkdir(parents=True, exist_ok=True)
    (root / "modules").mkdir(parents=True, exist_ok=True)
    (root / "services" / "workflow.py").write_text(
        """
def confirm_order(order):
    if order.get("credit_ok"):
        invoice = create_invoice(order)
        post_invoice(invoice)
        return invoice
    return None


def create_invoice(order):
    return {"invoice": order.get("id")}


def post_invoice(invoice):
    return invoice
""".strip(),
        encoding="utf-8",
    )
    (root / "modules" / "crm.py").write_text(
        """
def assign_lead(lead, agent):
    if lead and agent:
        return update_lead(lead, agent)
    return None


def update_lead(lead, agent):
    lead["owner"] = agent
    return lead
""".strip(),
        encoding="utf-8",
    )


def test_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_end_to_end_scan_and_graphs(tmp_path: Path) -> None:
    _build_sample_python_repo(tmp_path)
    register_response = client.post(
        "/api/repos/register",
        json={
            "repo_url": "https://github.com/frappe/erpnext",
            "default_branch": "develop",
            "local_path": str(tmp_path),
        },
    )
    assert register_response.status_code == 200
    repo = register_response.json()

    scan_response = client.post(
        f"/api/repos/{repo['id']}/scan",
        json={"commit_sha": "abc123"},
    )
    assert scan_response.status_code == 200
    run = scan_response.json()
    assert run["status"] == "completed"
    assert run["current_step"] == "completed"
    assert run["progress_pct"] == 100.0
    assert run["summary"]["codewords_runtime"]["status"] == "disabled"
    assert "ontology" in run["summary"]
    assert "migration" in run["summary"]
    assert "analysis_mode" in run["summary"]
    assert "workflow_nodes" in run["summary"]
    assert "lineage_edges" in run["summary"]
    assert "risk_findings" in run["summary"]
    assert "files_scanned" in run["summary"]
    assert "functions_scanned" in run["summary"]
    assert "parse_errors" in run["summary"]
    assert isinstance(run["summary"]["ontology"]["top_entities"], list)
    assert isinstance(run["summary"]["ontology"]["capability_clusters"], list)
    assert "readiness_score" in run["summary"]["migration"]
    assert isinstance(run["summary"]["migration"]["extraction_boundaries"], list)
    assert isinstance(run["summary"]["migration"]["impacted_modules"], list)
    assert isinstance(run["summary"]["migration"]["rerouting_risks"], list)

    workflow_response = client.get(f"/api/runs/{run['id']}/workflow-graph")
    lineage_response = client.get(f"/api/runs/{run['id']}/lineage-graph")
    risk_response = client.get(f"/api/runs/{run['id']}/risk-summary")
    enrichment_response = client.get(f"/api/runs/{run['id']}/enrichment")

    assert workflow_response.status_code == 200
    assert lineage_response.status_code == 200
    assert risk_response.status_code == 200
    assert enrichment_response.status_code == 200
    assert len(workflow_response.json()["nodes"]) > 0
    assert len(lineage_response.json()["edges"]) > 0
    assert len(risk_response.json()["findings"]) > 0
    assert enrichment_response.json()["status"] == "disabled"
    assert isinstance(enrichment_response.json()["ontology_enrichment"], dict)
    assert isinstance(enrichment_response.json()["migration_hints"], dict)
    assert isinstance(enrichment_response.json()["quality_checks"], dict)
    for finding in risk_response.json()["findings"]:
        assert "migration_suggestions" in finding
        assert isinstance(finding["migration_suggestions"], list)
        assert len(finding["migration_suggestions"]) > 0
    assert run["summary"]["analysis_mode"] == "ast-local"


def test_manual_cli_flow_sequence(tmp_path: Path) -> None:
    _build_sample_python_repo(tmp_path)
    register = client.post(
        "/api/repos/register",
        json={
            "repo_url": "https://github.com/frappe/erpnext",
            "default_branch": "develop",
            "local_path": str(tmp_path),
        },
    )
    assert register.status_code == 200
    repo = register.json()

    scan = client.post(
        f"/api/repos/{repo['id']}/scan",
        json={"commit_sha": "manual-seq-001"},
    )
    assert scan.status_code == 200
    run = scan.json()

    run_status = client.get(f"/api/repos/{repo['id']}/runs/{run['id']}")
    assert run_status.status_code == 200
    status_payload = run_status.json()
    assert status_payload["status"] == "completed"
    assert status_payload["current_step"] == "completed"
    assert status_payload["summary"]["ingestion_mode"] == "local"
    assert status_payload["summary"]["ingestion_branch"] == "develop"

    workflow = client.get(f"/api/runs/{run['id']}/workflow-graph")
    lineage = client.get(f"/api/runs/{run['id']}/lineage-graph")
    risk = client.get(f"/api/runs/{run['id']}/risk-summary")
    enrichment = client.get(f"/api/runs/{run['id']}/enrichment")

    assert workflow.status_code == 200
    assert lineage.status_code == 200
    assert risk.status_code == 200
    assert enrichment.status_code == 200
    assert enrichment.json()["status"] == "disabled"

    first_node = workflow.json()["nodes"][0]["id"]
    evidence = client.get(f"/api/runs/{run['id']}/node/{first_node}/evidence")
    assert evidence.status_code == 200

    copilot = client.post(
        "/api/copilot/query",
        json={
            "run_id": run["id"],
            "question": "Where is the sales confirmation logic?",
            "focus_node_id": first_node,
        },
    )
    assert copilot.status_code == 200
    copilot_payload = copilot.json()
    assert isinstance(copilot_payload["answer"], str) and copilot_payload["answer"]
    assert isinstance(copilot_payload["citations"], list) and len(copilot_payload["citations"]) >= 1
    assert isinstance(copilot_payload["risk_implications"], list)
    assert isinstance(copilot_payload["related_nodes"], list)


def test_copilot_returns_citations(tmp_path: Path) -> None:
    _build_sample_python_repo(tmp_path)
    repo = client.post(
        "/api/repos/register",
        json={
            "repo_url": "https://github.com/odoo/odoo",
            "default_branch": "master",
            "local_path": str(tmp_path),
        },
    ).json()

    run = client.post(
        f"/api/repos/{repo['id']}/scan",
        json={"commit_sha": "seed-001"},
    ).json()

    response = client.post(
        "/api/copilot/query",
        json={"run_id": run["id"], "question": "Where is sales confirmation logic?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "impact" in payload["answer"].lower()
    assert len(payload["citations"]) >= 1
    assert "risk_implications" in payload
    assert isinstance(payload["risk_implications"], list)
    assert "related_nodes" in payload
    assert isinstance(payload["related_nodes"], list)


def test_copilot_prefers_dust_when_configured(monkeypatch, tmp_path: Path) -> None:
    _build_sample_python_repo(tmp_path)
    repo = client.post(
        "/api/repos/register",
        json={
            "repo_url": "https://github.com/odoo/odoo",
            "default_branch": "master",
            "local_path": str(tmp_path),
        },
    ).json()

    run = client.post(
        f"/api/repos/{repo['id']}/scan",
        json={"commit_sha": "seed-002"},
    ).json()

    calls = {"semantic": 0}

    class FakeDust:
        def is_configured(self) -> bool:
            return True

        def semantic_copilot(self, *, question: str, context: dict) -> DustSemanticResponse:
            calls["semantic"] += 1
            assert question
            assert "codewords_enrichment" in context
            return DustSemanticResponse(
                answer="Dust grounded answer",
                citations=[
                    {
                        "file_path": "services/workflow.py",
                        "symbol": "confirm_order",
                        "reason": "Grounded in workflow evidence",
                        "line_start": 1,
                        "line_end": 8,
                    }
                ],
                risk_implications=["coupling risk"],
                related_nodes=[context["focus_node_id"]],
                raw_text="{}",
            )

    monkeypatch.setattr("app.routers.copilot.DustClient", FakeDust)

    response = client.post(
        "/api/copilot/query",
        json={"run_id": run["id"], "question": "Where is sales confirmation logic?"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "Dust grounded answer"
    assert payload["citations"][0]["file_path"] == "services/workflow.py"
    assert calls["semantic"] == 1


def test_mcp_status_endpoint_exposes_server_names_without_secrets() -> None:
    response = client.get("/api/integrations/mcp/status")
    assert response.status_code == 200

    payload = response.json()
    assert "servers" in payload
    assert "dust-tt" in payload["servers"]
    assert "CodeWords" in payload["servers"]
    codewords = payload["servers"]["CodeWords"]
    assert codewords["has_headers"] is True
    assert "Authorization" in codewords["header_keys"]


def test_dust_status_endpoint_returns_configuration_shape() -> None:
    response = client.get("/api/integrations/dust/status")
    assert response.status_code == 200
    payload = response.json()
    assert "configured" in payload
    assert "workspace_id" in payload
    assert "configuration_id" in payload


def test_scan_without_local_path_uses_fallback_mode() -> None:
    repo = client.post(
        "/api/repos/register",
        json={"repo_url": "https://github.com/frappe/erpnext", "default_branch": "develop"},
    ).json()

    run = client.post(
        f"/api/repos/{repo['id']}/scan",
        json={"commit_sha": "fallback-001"},
    ).json()

    assert run["summary"]["analysis_mode"] == "fallback"
    assert run["summary"]["codewords_runtime"]["status"] == "disabled"
    assert "ontology" in run["summary"]
    assert "migration" in run["summary"]
    assert run["summary"]["files_scanned"] == 0
    assert run["summary"]["functions_scanned"] == 0
    assert run["summary"]["parse_errors"] == 0
    assert isinstance(run["summary"]["ontology"]["top_entities"], list)
    assert isinstance(run["summary"]["migration"]["extraction_boundaries"], list)
    enrichment = client.get(f"/api/runs/{run['id']}/enrichment")
    assert enrichment.status_code == 200
    assert enrichment.json()["status"] == "disabled"
    ingest_evidence = client.get(f"/api/runs/{run['id']}/node/ingest/evidence")
    customer_evidence = client.get(f"/api/runs/{run['id']}/node/entity-customer/evidence")
    assert ingest_evidence.status_code == 200
    assert customer_evidence.status_code == 200

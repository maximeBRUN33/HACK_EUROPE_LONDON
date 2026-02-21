from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

from app.models import AnalysisRun, EnrichmentPayload, EvidencePayload, GraphPayload, Repository, RiskSummaryPayload
from app.persistence.sqlite_store import SQLiteStore

DB_PATH = Path(__file__).resolve().parents[3] / "data" / "legacy_atlas.db"


@dataclass
class AppStore:
    repositories: dict[UUID, Repository] = field(default_factory=dict)
    runs: dict[UUID, AnalysisRun] = field(default_factory=dict)
    workflow_graphs: dict[UUID, GraphPayload] = field(default_factory=dict)
    lineage_graphs: dict[UUID, GraphPayload] = field(default_factory=dict)
    risk_summaries: dict[UUID, RiskSummaryPayload] = field(default_factory=dict)
    evidences: dict[tuple[UUID, str], EvidencePayload] = field(default_factory=dict)
    enrichments: dict[UUID, EnrichmentPayload] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.sqlite = SQLiteStore(DB_PATH)
        self.metadata.update(self.sqlite.get_metadata())

    def save_repository(self, repository: Repository) -> None:
        self.repositories[repository.id] = repository
        self.sqlite.save_repository(repository)

    def get_repository(self, repo_id: str) -> Repository | None:
        for key, repository in self.repositories.items():
            if str(key) == repo_id:
                return repository

        repository = self.sqlite.get_repository(repo_id)
        if repository is None:
            return None
        self.repositories[repository.id] = repository
        return repository

    def save_run(self, run: AnalysisRun) -> None:
        self.runs[run.id] = run
        self.sqlite.save_run(run)

    def get_run(self, run_id: str) -> AnalysisRun | None:
        for key, run in self.runs.items():
            if str(key) == run_id:
                return run

        run = self.sqlite.get_run(run_id)
        if run is None:
            return None
        self.runs[run.id] = run
        return run

    def get_run_for_repository(self, repo_id: str, run_id: str) -> AnalysisRun | None:
        run = self.get_run(run_id)
        if run is not None and str(run.repository_id) == repo_id:
            return run

        run = self.sqlite.get_run_for_repository(repo_id, run_id)
        if run is None:
            return None
        self.runs[run.id] = run
        return run

    def save_workflow_graph(self, run_id: UUID, payload: GraphPayload) -> None:
        self.workflow_graphs[run_id] = payload
        self.sqlite.save_workflow_graph(str(run_id), payload)

    def get_workflow_graph(self, run_id: str) -> GraphPayload | None:
        for key, payload in self.workflow_graphs.items():
            if str(key) == run_id:
                return payload

        payload = self.sqlite.get_workflow_graph(run_id)
        if payload is None:
            return None
        self.workflow_graphs[payload.run_id] = payload
        return payload

    def save_lineage_graph(self, run_id: UUID, payload: GraphPayload) -> None:
        self.lineage_graphs[run_id] = payload
        self.sqlite.save_lineage_graph(str(run_id), payload)

    def get_lineage_graph(self, run_id: str) -> GraphPayload | None:
        for key, payload in self.lineage_graphs.items():
            if str(key) == run_id:
                return payload

        payload = self.sqlite.get_lineage_graph(run_id)
        if payload is None:
            return None
        self.lineage_graphs[payload.run_id] = payload
        return payload

    def save_risk_summary(self, run_id: UUID, payload: RiskSummaryPayload) -> None:
        self.risk_summaries[run_id] = payload
        self.sqlite.save_risk_summary(str(run_id), payload)

    def get_risk_summary(self, run_id: str) -> RiskSummaryPayload | None:
        for key, payload in self.risk_summaries.items():
            if str(key) == run_id:
                return payload

        payload = self.sqlite.get_risk_summary(run_id)
        if payload is None:
            return None
        self.risk_summaries[payload.run_id] = payload
        return payload

    def save_evidence(self, run_id: UUID, node_id: str, payload: EvidencePayload) -> None:
        self.evidences[(run_id, node_id)] = payload
        self.sqlite.save_evidence(str(run_id), node_id, payload)

    def get_evidence(self, run_id: str, node_id: str) -> EvidencePayload | None:
        for (cached_run_id, cached_node_id), payload in self.evidences.items():
            if str(cached_run_id) == run_id and cached_node_id == node_id:
                return payload

        payload = self.sqlite.get_evidence(run_id, node_id)
        if payload is None:
            return None
        self.evidences[(payload.run_id, node_id)] = payload
        return payload

    def save_enrichment(self, run_id: UUID, payload: EnrichmentPayload) -> None:
        self.enrichments[run_id] = payload
        self.sqlite.save_enrichment(str(run_id), payload)

    def get_enrichment(self, run_id: str) -> EnrichmentPayload | None:
        for key, payload in self.enrichments.items():
            if str(key) == run_id:
                return payload

        payload = self.sqlite.get_enrichment(run_id)
        if payload is None:
            return None
        self.enrichments[payload.run_id] = payload
        return payload

    def clear_all(self) -> None:
        self.repositories.clear()
        self.runs.clear()
        self.workflow_graphs.clear()
        self.lineage_graphs.clear()
        self.risk_summaries.clear()
        self.evidences.clear()
        self.enrichments.clear()
        self.sqlite.clear_all()


store = AppStore()

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from app.models import AnalysisRun, EvidencePayload, GraphPayload, Repository, RiskSummaryPayload


class SQLiteStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                create table if not exists repositories (
                    id text primary key,
                    payload text not null,
                    created_at text not null default current_timestamp
                );

                create table if not exists runs (
                    id text primary key,
                    repository_id text not null,
                    payload text not null,
                    created_at text not null default current_timestamp
                );

                create index if not exists idx_runs_repository_id on runs(repository_id);

                create table if not exists artifacts (
                    run_id text not null,
                    kind text not null,
                    node_id text not null default '',
                    payload text not null,
                    created_at text not null default current_timestamp,
                    primary key (run_id, kind, node_id)
                );

                create index if not exists idx_artifacts_run_id on artifacts(run_id);
                """
            )

    def save_repository(self, repository: Repository) -> None:
        with self._connect() as connection:
            connection.execute(
                "insert or replace into repositories (id, payload) values (?, ?)",
                (str(repository.id), repository.model_dump_json()),
            )

    def get_repository(self, repo_id: str) -> Repository | None:
        with self._connect() as connection:
            row = connection.execute("select payload from repositories where id = ?", (repo_id,)).fetchone()
        if row is None:
            return None
        return Repository.model_validate_json(row["payload"])

    def save_run(self, run: AnalysisRun) -> None:
        with self._connect() as connection:
            connection.execute(
                "insert or replace into runs (id, repository_id, payload) values (?, ?, ?)",
                (str(run.id), str(run.repository_id), run.model_dump_json()),
            )

    def get_run(self, run_id: str) -> AnalysisRun | None:
        with self._connect() as connection:
            row = connection.execute("select payload from runs where id = ?", (run_id,)).fetchone()
        if row is None:
            return None
        return AnalysisRun.model_validate_json(row["payload"])

    def get_run_for_repository(self, repo_id: str, run_id: str) -> AnalysisRun | None:
        with self._connect() as connection:
            row = connection.execute(
                "select payload from runs where id = ? and repository_id = ?",
                (run_id, repo_id),
            ).fetchone()
        if row is None:
            return None
        return AnalysisRun.model_validate_json(row["payload"])

    def save_workflow_graph(self, run_id: str, payload: GraphPayload) -> None:
        self._save_artifact(run_id, "workflow", "", payload.model_dump_json())

    def get_workflow_graph(self, run_id: str) -> GraphPayload | None:
        raw = self._get_artifact(run_id, "workflow", "")
        if raw is None:
            return None
        return GraphPayload.model_validate_json(raw)

    def save_lineage_graph(self, run_id: str, payload: GraphPayload) -> None:
        self._save_artifact(run_id, "lineage", "", payload.model_dump_json())

    def get_lineage_graph(self, run_id: str) -> GraphPayload | None:
        raw = self._get_artifact(run_id, "lineage", "")
        if raw is None:
            return None
        return GraphPayload.model_validate_json(raw)

    def save_risk_summary(self, run_id: str, payload: RiskSummaryPayload) -> None:
        self._save_artifact(run_id, "risk", "", payload.model_dump_json())

    def get_risk_summary(self, run_id: str) -> RiskSummaryPayload | None:
        raw = self._get_artifact(run_id, "risk", "")
        if raw is None:
            return None
        return RiskSummaryPayload.model_validate_json(raw)

    def save_evidence(self, run_id: str, node_id: str, payload: EvidencePayload) -> None:
        self._save_artifact(run_id, "evidence", node_id, payload.model_dump_json())

    def get_evidence(self, run_id: str, node_id: str) -> EvidencePayload | None:
        raw = self._get_artifact(run_id, "evidence", node_id)
        if raw is None:
            return None
        return EvidencePayload.model_validate_json(raw)

    def _save_artifact(self, run_id: str, kind: str, node_id: str, payload: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "insert or replace into artifacts (run_id, kind, node_id, payload) values (?, ?, ?, ?)",
                (run_id, kind, node_id, payload),
            )

    def _get_artifact(self, run_id: str, kind: str, node_id: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "select payload from artifacts where run_id = ? and kind = ? and node_id = ?",
                (run_id, kind, node_id),
            ).fetchone()
        if row is None:
            return None
        return str(row["payload"])

    def get_metadata(self) -> dict[str, Any]:
        return {
            "db_path": str(self.db_path),
        }

    def clear_all(self) -> None:
        with self._connect() as connection:
            connection.execute("delete from artifacts")
            connection.execute("delete from runs")
            connection.execute("delete from repositories")

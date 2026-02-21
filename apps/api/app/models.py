from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RunStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class Repository(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    provider: str = "github"
    owner: str
    name: str
    default_branch: str = "main"
    repo_url: HttpUrl
    local_path: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class RepositoryRegisterRequest(BaseModel):
    repo_url: HttpUrl
    default_branch: str = "main"
    local_path: str | None = None


class AnalysisRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    repository_id: UUID
    commit_sha: str
    status: RunStatus = RunStatus.queued
    current_step: str = "queued"
    progress_pct: float = 0.0
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    summary: dict = Field(default_factory=dict)


class ScanRequest(BaseModel):
    commit_sha: str


class Node(BaseModel):
    id: str
    label: str
    node_type: Literal["process", "data", "risk"]
    risk_score: float = 0.0


class Edge(BaseModel):
    source: str
    target: str
    edge_type: Literal["control", "data", "risk"]
    confidence: float = 1.0


class GraphPayload(BaseModel):
    run_id: UUID
    nodes: list[Node]
    edges: list[Edge]


class RiskFinding(BaseModel):
    id: str
    category: Literal["complexity", "coupling", "dead_code", "test_gap"]
    severity: Literal["low", "medium", "high", "critical"]
    score: float
    title: str
    rationale: str
    symbol: str
    migration_suggestions: list[str] = Field(default_factory=list)


class RiskSummaryPayload(BaseModel):
    run_id: UUID
    overall_score: float
    findings: list[RiskFinding]


class EvidencePayload(BaseModel):
    run_id: UUID
    node_id: str
    files: list[str]
    symbols: list[str]
    explanation: str


class CopilotRequest(BaseModel):
    run_id: UUID
    question: str
    focus_node_id: str | None = None


class CopilotCitation(BaseModel):
    file_path: str
    symbol: str
    reason: str
    line_start: int | None = None
    line_end: int | None = None


class CopilotResponse(BaseModel):
    answer: str
    citations: list[CopilotCitation]
    risk_implications: list[str]
    related_nodes: list[str]


class CodeWordsTriggerRequest(BaseModel):
    service_id: str
    inputs: dict = Field(default_factory=dict)
    async_mode: bool = True


class CodeWordsTriggerResponse(BaseModel):
    provider: str = "codewords"
    service_id: str
    status: str
    request_id: str | None = None
    raw: dict = Field(default_factory=dict)


class CodeWordsResultResponse(BaseModel):
    provider: str = "codewords"
    request_id: str
    status: str
    raw: dict = Field(default_factory=dict)

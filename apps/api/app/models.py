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


class CopilotWebCompareRequest(BaseModel):
    run_id: UUID
    question: str
    answer: str
    max_results: int = Field(default=6, ge=1, le=12)
    platforms: list[str] = Field(default_factory=lambda: ["reddit", "x"])


class WebReferenceItem(BaseModel):
    platform: str
    title: str
    url: HttpUrl
    snippet: str
    why_relevant: str = ""


class CopilotWebCompareResponse(BaseModel):
    provider: str = "gemini"
    model: str
    status: str
    summary: str
    items: list[WebReferenceItem] = Field(default_factory=list)
    raw: dict = Field(default_factory=dict)


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


class EnrichmentPayload(BaseModel):
    run_id: UUID
    provider: str = "codewords"
    service_id: str | None = None
    request_id: str | None = None
    status: str
    ontology_enrichment: dict = Field(default_factory=dict)
    migration_hints: dict = Field(default_factory=dict)
    quality_checks: dict = Field(default_factory=dict)
    raw: dict = Field(default_factory=dict)


class MigrationBlueprintPhase(BaseModel):
    phase_id: str
    title: str
    objective: str
    actions: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    impacted_modules: list[str] = Field(default_factory=list)
    risk_watch: list[str] = Field(default_factory=list)


class MigrationBlueprintPayload(BaseModel):
    run_id: UUID
    analysis_mode: str
    readiness_score: float
    readiness_band: Literal["low", "medium", "high"]
    entities: list[str] = Field(default_factory=list)
    impacted_modules: list[str] = Field(default_factory=list)
    extraction_boundaries: list[dict] = Field(default_factory=list)
    integration_routing: dict = Field(default_factory=dict)
    top_risks: list[dict] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    phased_plan: list[MigrationBlueprintPhase] = Field(default_factory=list)
    enrichment_status: str | None = None
    generated_at: datetime = Field(default_factory=utc_now)


class IntegrationProviderReadiness(BaseModel):
    configured: bool
    reachable: bool
    latency_ms: int | None = None
    detail: str | None = None


class IntegrationReadinessResponse(BaseModel):
    checked_at: datetime = Field(default_factory=utc_now)
    codewords: IntegrationProviderReadiness
    dust: IntegrationProviderReadiness
    mcp: IntegrationProviderReadiness

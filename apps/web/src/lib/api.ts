export type RepoResponse = {
  id: string;
  owner: string;
  name: string;
  default_branch: string;
  repo_url: string;
  local_path?: string | null;
};

export type RunResponse = {
  id: string;
  repository_id: string;
  commit_sha: string;
  status: "queued" | "running" | "completed" | "failed";
  current_step: string;
  progress_pct: number;
  error_message?: string | null;
  summary: Record<string, unknown>;
};

export type GraphNode = {
  id: string;
  label: string;
  node_type: "process" | "data" | "risk";
  risk_score: number;
};

export type GraphEdge = {
  source: string;
  target: string;
  edge_type: "control" | "data" | "risk";
  confidence: number;
};

export type GraphPayload = {
  run_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export type RiskFinding = {
  id: string;
  category: "complexity" | "coupling" | "dead_code" | "test_gap";
  severity: "low" | "medium" | "high" | "critical";
  score: number;
  title: string;
  rationale: string;
  symbol: string;
  migration_suggestions: string[];
};

export type RiskSummary = {
  run_id: string;
  overall_score: number;
  findings: RiskFinding[];
};

export type CopilotCitation = {
  file_path: string;
  symbol: string;
  reason: string;
  line_start?: number | null;
  line_end?: number | null;
};

export type CopilotResponse = {
  answer: string;
  citations: CopilotCitation[];
  risk_implications: string[];
  related_nodes: string[];
};

export type EvidencePayload = {
  run_id: string;
  node_id: string;
  files: string[];
  symbols: string[];
  explanation: string;
};

export type EnrichmentPayload = {
  run_id: string;
  provider: string;
  service_id?: string | null;
  request_id?: string | null;
  status: string;
  ontology_enrichment: Record<string, unknown>;
  migration_hints: Record<string, unknown>;
  quality_checks: Record<string, unknown>;
  raw: Record<string, unknown>;
};

export type MigrationBlueprintPhase = {
  phase_id: string;
  title: string;
  objective: string;
  actions: string[];
  success_criteria: string[];
  impacted_modules: string[];
  risk_watch: string[];
};

export type MigrationBlueprintPayload = {
  run_id: string;
  analysis_mode: string;
  readiness_score: number;
  readiness_band: string;
  entities: string[];
  impacted_modules: string[];
  extraction_boundaries: Array<Record<string, unknown>>;
  integration_routing: Record<string, unknown>;
  top_risks: Array<Record<string, unknown>>;
  recommendations: string[];
  phased_plan: MigrationBlueprintPhase[];
  enrichment_status?: string | null;
  generated_at: string;
};

export type IntegrationProviderReadiness = {
  configured: boolean;
  reachable: boolean;
  latency_ms?: number | null;
  detail?: string | null;
};

export type IntegrationsReadinessResponse = {
  checked_at: string;
  codewords: IntegrationProviderReadiness;
  dust: IntegrationProviderReadiness;
  mcp: IntegrationProviderReadiness;
};

const API_BASE = "http://localhost:8000";

export async function registerRepository(
  repoUrl: string,
  defaultBranch = "main",
  localPath?: string
): Promise<RepoResponse> {
  const response = await fetch(`${API_BASE}/api/repos/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl, default_branch: defaultBranch, local_path: localPath || null })
  });
  if (!response.ok) {
    throw new Error(`Failed to register repository (${response.status})`);
  }
  return response.json();
}

export async function startScan(repoId: string, commitSha: string): Promise<RunResponse> {
  const response = await fetch(`${API_BASE}/api/repos/${repoId}/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ commit_sha: commitSha })
  });
  if (!response.ok) {
    throw new Error(`Failed to start scan (${response.status})`);
  }
  return response.json();
}

export async function fetchRunStatus(repoId: string, runId: string): Promise<RunResponse> {
  return fetchJson<RunResponse>(`${API_BASE}/api/repos/${repoId}/runs/${runId}`);
}

export async function fetchWorkflowGraph(runId: string): Promise<GraphPayload> {
  return fetchJson<GraphPayload>(`${API_BASE}/api/runs/${runId}/workflow-graph`);
}

export async function fetchLineageGraph(runId: string): Promise<GraphPayload> {
  return fetchJson<GraphPayload>(`${API_BASE}/api/runs/${runId}/lineage-graph`);
}

export async function fetchRiskSummary(runId: string): Promise<RiskSummary> {
  return fetchJson<RiskSummary>(`${API_BASE}/api/runs/${runId}/risk-summary`);
}

export async function fetchNodeEvidence(runId: string, nodeId: string): Promise<EvidencePayload> {
  return fetchJson<EvidencePayload>(`${API_BASE}/api/runs/${runId}/node/${nodeId}/evidence`);
}

export async function fetchRunEnrichment(runId: string): Promise<EnrichmentPayload> {
  return fetchJson<EnrichmentPayload>(`${API_BASE}/api/runs/${runId}/enrichment`);
}

export async function fetchMigrationBlueprint(runId: string): Promise<MigrationBlueprintPayload> {
  return fetchJson<MigrationBlueprintPayload>(`${API_BASE}/api/runs/${runId}/migration-blueprint`);
}

export async function askCopilot(runId: string, question: string): Promise<CopilotResponse> {
  const response = await fetch(`${API_BASE}/api/copilot/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ run_id: runId, question })
  });
  if (!response.ok) {
    throw new Error(`Copilot query failed (${response.status})`);
  }
  return response.json();
}

export async function fetchDustStatus(): Promise<{ configured: boolean }> {
  return fetchJson<{ configured: boolean }>(`${API_BASE}/api/integrations/dust/status`);
}

export async function fetchMcpStatus(): Promise<{ servers: Record<string, unknown> }> {
  return fetchJson<{ servers: Record<string, unknown> }>(`${API_BASE}/api/integrations/mcp/status`);
}

export async function fetchIntegrationsReadiness(): Promise<IntegrationsReadinessResponse> {
  return fetchJson<IntegrationsReadinessResponse>(`${API_BASE}/api/integrations/readiness`);
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body?.detail?.detail_code) {
        message = `${body.detail.detail_code}: ${body.detail.message ?? message}`;
      } else if (typeof body?.detail === "string") {
        message = body.detail;
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(message);
  }
  return response.json();
}

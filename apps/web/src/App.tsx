import { useCallback, useEffect, useMemo, useState } from "react";
import { CopilotPanel } from "./components/CopilotPanel";
import { GraphPanel } from "./components/GraphPanel";
import { RepoIntakePanel } from "./components/RepoIntakePanel";
import { RiskPanel } from "./components/RiskPanel";
import {
  askCopilot,
  fetchDustStatus,
  fetchLineageGraph,
  fetchMcpStatus,
  fetchNodeEvidence,
  fetchRiskSummary,
  fetchRunStatus,
  fetchWorkflowGraph,
  registerRepository,
  startScan,
  type CopilotResponse,
  type EvidencePayload,
  type GraphPayload,
  type RepoResponse,
  type RiskSummary,
  type RunResponse
} from "./lib/api";

type AppState = {
  repo: RepoResponse | null;
  run: RunResponse | null;
  workflowGraph: GraphPayload | null;
  lineageGraph: GraphPayload | null;
  workflowEvidence: EvidencePayload | null;
  lineageEvidence: EvidencePayload | null;
  riskSummary: RiskSummary | null;
  copilot: CopilotResponse | null;
};

const initialState: AppState = {
  repo: null,
  run: null,
  workflowGraph: null,
  lineageGraph: null,
  workflowEvidence: null,
  lineageEvidence: null,
  riskSummary: null,
  copilot: null
};

export function App(): JSX.Element {
  const [state, setState] = useState<AppState>(initialState);
  const [busy, setBusy] = useState(false);
  const [copilotBusy, setCopilotBusy] = useState(false);
  const [workflowEvidenceLoading, setWorkflowEvidenceLoading] = useState(false);
  const [lineageEvidenceLoading, setLineageEvidenceLoading] = useState(false);
  const [dustConfigured, setDustConfigured] = useState(false);
  const [codewordsConfigured, setCodewordsConfigured] = useState(false);
  const [activeTab, setActiveTab] = useState<"scan" | "process" | "data" | "risk" | "copilot">("scan");
  const [symbolNodeMap, setSymbolNodeMap] = useState<Map<string, string>>(new Map());
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);

  useEffect(() => {
    fetchDustStatus()
      .then((res) => setDustConfigured(res.configured))
      .catch(() => setDustConfigured(false));
    fetchMcpStatus()
      .then((res) => setCodewordsConfigured("CodeWords" in (res.servers || {})))
      .catch(() => setCodewordsConfigured(false));
  }, []);

  async function handleStart(repoUrl: string, commitSha: string, localPath: string): Promise<{ repo: RepoResponse; run: RunResponse }> {
    setBusy(true);
    try {
      const repo = await registerRepository(repoUrl, "main", localPath || undefined);
      const queuedRun = await startScan(repo.id, commitSha);
      setState((current) => ({ ...current, repo, run: queuedRun, copilot: null }));

      const completedRun = await pollRunUntilCompleted(repo.id, queuedRun.id, (run) => {
        setState((current) => ({ ...current, run }));
      });

      const [workflowGraph, lineageGraph, riskSummary] = await Promise.all([
        fetchWorkflowGraph(completedRun.id),
        fetchLineageGraph(completedRun.id),
        fetchRiskSummary(completedRun.id)
      ]);

      setState((current) => ({
        ...current,
        repo,
        run: completedRun,
        workflowGraph,
        lineageGraph,
        workflowEvidence: null,
        lineageEvidence: null,
        riskSummary,
        copilot: null
      }));

      setActiveTab("process");

      return { repo, run: completedRun };
    } finally {
      setBusy(false);
    }
  }

  const handleSelectWorkflowNode = useCallback(
    async (nodeId: string): Promise<void> => {
      if (!state.run) {
        return;
      }
      setWorkflowEvidenceLoading(true);
      try {
        const evidence = await fetchNodeEvidence(state.run.id, nodeId);
        setState((current) => ({ ...current, workflowEvidence: evidence }));
      } catch {
        setState((current) => ({ ...current, workflowEvidence: null }));
      } finally {
        setWorkflowEvidenceLoading(false);
      }
    },
    [state.run]
  );

  const handleSelectLineageNode = useCallback(
    async (nodeId: string): Promise<void> => {
      if (!state.run) {
        return;
      }
      setLineageEvidenceLoading(true);
      try {
        const evidence = await fetchNodeEvidence(state.run.id, nodeId);
        setState((current) => ({ ...current, lineageEvidence: evidence }));
      } catch {
        setState((current) => ({ ...current, lineageEvidence: null }));
      } finally {
        setLineageEvidenceLoading(false);
      }
    },
    [state.run]
  );

  // Build symbol → nodeId map from workflow graph evidence
  useEffect(() => {
    if (!state.workflowGraph || state.workflowGraph.nodes.length === 0) {
      setSymbolNodeMap(new Map());
      return;
    }
    const runId = state.workflowGraph.run_id;
    const map = new Map<string, string>();
    Promise.all(
      state.workflowGraph.nodes.map(async (node) => {
        try {
          const ev = await fetchNodeEvidence(runId, node.id);
          for (const sym of ev.symbols) {
            map.set(sym, node.id);
          }
        } catch {
          // skip
        }
      })
    ).then(() => setSymbolNodeMap(new Map(map)));
  }, [state.workflowGraph]);

  const handleFocusNode = useCallback(
    (nodeId: string) => {
      setActiveTab("process");
      setFocusedNodeId(nodeId);
      handleSelectWorkflowNode(nodeId);
    },
    [handleSelectWorkflowNode]
  );

  async function handleAsk(question: string): Promise<void> {
    if (!state.run) {
      return;
    }

    setCopilotBusy(true);
    try {
      const copilot = await askCopilot(state.run.id, question);
      setState((current) => ({ ...current, copilot }));
    } finally {
      setCopilotBusy(false);
    }
  }

  const runSummary = useMemo(() => {
    if (!state.run || !state.repo) {
      return "No active run";
    }
    const mode = String(state.run.summary?.analysis_mode ?? "pending");
    const progress = `${Math.round(state.run.progress_pct)}%`;
    return `${state.repo.owner}/${state.repo.name} | ${state.run.commit_sha} | ${state.run.status} | ${state.run.current_step} | ${progress} | ${mode}`;
  }, [state.repo, state.run]);

  return (
    <div className="app-shell">
      <header>
        <h1>Legacy Atlas</h1>
        <p>AI-powered legacy comprehension with process maps, lineage tracing, and risk intelligence.</p>
        <div className={`run-pill ${state.run ? `run-pill-${state.run.status}` : ""}`}>{runSummary}</div>
      </header>

      {state.run?.status === "completed" && (
        <div className="kpi-bar">
          <div className="kpi-item">
            <span className="kpi-label">Files Analyzed</span>
            <span className="kpi-value">{String(state.run.summary?.files_scanned ?? 0)}</span>
          </div>
          <div className="kpi-divider" />
          <div className="kpi-item">
            <span className="kpi-label">Workflow Nodes</span>
            <span className="kpi-value">{state.workflowGraph?.nodes.length ?? 0}</span>
          </div>
          <div className="kpi-divider" />
          <div className="kpi-item">
            <span className="kpi-label">Data Entities</span>
            <span className="kpi-value">{state.lineageGraph?.nodes.length ?? 0}</span>
          </div>
          <div className="kpi-divider" />
          <div className="kpi-item">
            <span className="kpi-label">Risk Findings</span>
            <span className="kpi-value">{state.riskSummary?.findings.length ?? 0}</span>
          </div>
          <div className="kpi-divider" />
          <div className="kpi-item">
            <span className="kpi-label">Analysis Mode</span>
            <span className="kpi-value kpi-mode">{String(state.run.summary?.analysis_mode ?? "N/A")}</span>
          </div>
        </div>
      )}

      <nav className="tab-bar">
        <button className={`tab-btn ${activeTab === "scan" ? "active" : ""}`} onClick={() => setActiveTab("scan")}>Scan</button>
        <button className={`tab-btn ${activeTab === "process" ? "active" : ""}`} onClick={() => setActiveTab("process")}>Process Explorer</button>
        <button className={`tab-btn ${activeTab === "data" ? "active" : ""}`} onClick={() => setActiveTab("data")}>Data Lineage</button>
        <button className={`tab-btn ${activeTab === "risk" ? "active" : ""}`} onClick={() => setActiveTab("risk")}>Risk Analysis</button>
        <button className={`tab-btn ${activeTab === "copilot" ? "active" : ""}`} onClick={() => setActiveTab("copilot")}>Copilot</button>
      </nav>

      <main>
        {activeTab === "scan" && (
          <RepoIntakePanel
            isBusy={busy}
            run={state.run}
            dustConfigured={dustConfigured}
            codewordsConfigured={codewordsConfigured}
            onStart={handleStart}
          />
        )}

        {activeTab === "process" && (
          <GraphPanel
            title="Process Atlas"
            graph={state.workflowGraph}
            evidence={state.workflowEvidence}
            evidenceLoading={workflowEvidenceLoading}
            onSelectNode={handleSelectWorkflowNode}
            focusedNodeId={focusedNodeId}
            riskSummary={state.riskSummary}
          />
        )}

        {activeTab === "data" && (
          <GraphPanel
            title="Data Lineage Navigator"
            graph={state.lineageGraph}
            evidence={state.lineageEvidence}
            evidenceLoading={lineageEvidenceLoading}
            onSelectNode={handleSelectLineageNode}
            showEdgeLabels
            riskSummary={state.riskSummary}
          />
        )}

        {activeTab === "risk" && (
          <>
            <GraphPanel
              title="Risk Atlas"
              graph={state.workflowGraph}
              evidence={state.workflowEvidence}
              evidenceLoading={workflowEvidenceLoading}
              onSelectNode={handleSelectWorkflowNode}
              riskOverlay
              focusedNodeId={focusedNodeId}
              riskSummary={state.riskSummary}
            />
            <RiskPanel summary={state.riskSummary} />
          </>
        )}

        {activeTab === "copilot" && (
          <CopilotPanel runId={state.run?.id ?? null} response={state.copilot} isBusy={copilotBusy} onAsk={handleAsk} onFocusNode={handleFocusNode} symbolNodeMap={symbolNodeMap} />
        )}
      </main>
    </div>
  );
}

async function pollRunUntilCompleted(
  repoId: string,
  runId: string,
  onTick: (run: RunResponse) => void,
  timeoutMs = 180000,
  intervalMs = 1200
): Promise<RunResponse> {
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    const run = await fetchRunStatus(repoId, runId);
    onTick(run);

    if (run.status === "completed") {
      return run;
    }

    if (run.status === "failed") {
      const message = run.error_message || "Analysis run failed";
      throw new Error(message);
    }

    await sleep(intervalMs);
  }

  throw new Error("Analysis timeout reached while waiting for completion");
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

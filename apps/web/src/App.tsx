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

      <main>
        <RepoIntakePanel
          isBusy={busy}
          run={state.run}
          dustConfigured={dustConfigured}
          codewordsConfigured={codewordsConfigured}
          onStart={handleStart}
        />

        <section className="grid two-col">
          <GraphPanel
            title="Process Atlas"
            graph={state.workflowGraph}
            evidence={state.workflowEvidence}
            evidenceLoading={workflowEvidenceLoading}
            onSelectNode={handleSelectWorkflowNode}
          />
          <GraphPanel
            title="Data Lineage Navigator"
            graph={state.lineageGraph}
            evidence={state.lineageEvidence}
            evidenceLoading={lineageEvidenceLoading}
            onSelectNode={handleSelectLineageNode}
          />
        </section>

        <section className="grid two-col">
          <RiskPanel summary={state.riskSummary} />
          <CopilotPanel runId={state.run?.id ?? null} response={state.copilot} isBusy={copilotBusy} onAsk={handleAsk} />
        </section>
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

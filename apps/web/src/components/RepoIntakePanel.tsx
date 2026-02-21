import { FormEvent, useState } from "react";
import type { RepoResponse, RunResponse } from "../lib/api";

type RepoIntakePanelProps = {
  isBusy: boolean;
  run: RunResponse | null;
  dustConfigured: boolean;
  codewordsConfigured: boolean;
  onStart: (repoUrl: string, commitSha: string, localPath: string) => Promise<{ repo: RepoResponse; run: RunResponse }>;
};

const PIPELINE_STEPS = [
  { key: "ingesting", label: "Ingesting" },
  { key: "parsing-python-ast", label: "Parsing AST" },
  { key: "building-graphs", label: "Building Graphs" },
  { key: "persisting-artifacts", label: "Persisting" },
  { key: "completed", label: "Completed" },
] as const;

function stepStatus(stepKey: string, currentStep: string, runStatus: string): "pending" | "active" | "completed" {
  if (runStatus === "completed") return "completed";

  const stepIndex = PIPELINE_STEPS.findIndex((s) => s.key === stepKey);
  const currentIndex = PIPELINE_STEPS.findIndex((s) => s.key === currentStep);

  if (currentIndex === -1) {
    if (currentStep === "queued") return "pending";
    if (currentStep === "resolving-source") {
      return stepIndex === 0 ? "active" : "pending";
    }
    if (currentStep === "fallback-analysis") {
      return stepIndex <= 1 ? "completed" : stepIndex === 2 ? "active" : "pending";
    }
    return "pending";
  }

  if (stepIndex < currentIndex) return "completed";
  if (stepIndex === currentIndex) return "active";
  return "pending";
}

export function RepoIntakePanel({ isBusy, run, dustConfigured, codewordsConfigured, onStart }: RepoIntakePanelProps): JSX.Element {
  const [repoUrl, setRepoUrl] = useState("https://github.com/frappe/erpnext");
  const [commitSha, setCommitSha] = useState("hackathon-seed");
  const [localPath, setLocalPath] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    try {
      await onStart(repoUrl, commitSha, localPath.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run intake");
    }
  }

  return (
    <section className="card intake-card">
      <div className="card-title-row">
        <h2>Repository Mission Control</h2>
        <span className="badge">Phase 1</span>
      </div>
      <p className="muted">Register a repo and trigger an analysis run to populate workflow, lineage, and risk panels.</p>
      <form onSubmit={handleSubmit} className="stack">
        <label>
          Repository URL
          <input value={repoUrl} onChange={(event) => setRepoUrl(event.target.value)} placeholder="https://github.com/org/repo" required />
        </label>
        <label>
          Commit SHA (or label)
          <input value={commitSha} onChange={(event) => setCommitSha(event.target.value)} placeholder="commit-sha" required />
        </label>
        <label>
          Local Repo Path (recommended for real AST)
          <input
            value={localPath}
            onChange={(event) => setLocalPath(event.target.value)}
            placeholder="/absolute/path/to/local/repo"
          />
        </label>
        <button type="submit" disabled={isBusy}>{isBusy ? "Analyzing..." : "Start Analysis"}</button>
      </form>
      {error && <p className="error">{error}</p>}

      {run && run.status !== "queued" && (
        <div className="pipeline-tracker">
          <div className="pipeline-steps">
            {PIPELINE_STEPS.map((step) => {
              const status = stepStatus(step.key, run.current_step, run.status);
              return (
                <div key={step.key} className={`pipeline-step pipeline-step-${status}`}>
                  <div className="pipeline-step-indicator">
                    {status === "completed" ? "\u2713" : status === "active" ? "\u25CF" : "\u25CB"}
                  </div>
                  <span className="pipeline-step-label">{step.label}</span>
                </div>
              );
            })}
          </div>
          <div className="pipeline-bar">
            <div className="pipeline-bar-fill" style={{ width: `${Math.round(run.progress_pct)}%` }} />
          </div>
          <div className="integration-badges">
            <span className={`integration-badge ${dustConfigured ? "configured" : "not-configured"}`}>
              Dust {dustConfigured ? "\u2713" : "\u2717"}
            </span>
            <span className={`integration-badge ${codewordsConfigured ? "configured" : "not-configured"}`}>
              CodeWords {codewordsConfigured ? "\u2713" : "\u2717"}
            </span>
          </div>
        </div>
      )}
    </section>
  );
}

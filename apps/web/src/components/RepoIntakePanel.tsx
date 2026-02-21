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
  const [repoUrl, setRepoUrl] = useState("https://github.com/akashroshan135/inventory-management.git");
  const [commitSha, setCommitSha] = useState("main");
  const [localPath, setLocalPath] = useState("/Users/alessandrocondorelli/inventory-management");
  const [error, setError] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const isAnalyzing = isBusy || (run !== null && run.status !== "completed" && run.status !== "failed");

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    try {
      await onStart(repoUrl, commitSha, localPath.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run intake");
    }
  }

  const repoName = repoUrl.replace(/^https?:\/\/github\.com\//, "").replace(/\/$/, "") || "repository";

  if (isAnalyzing && run) {
    return (
      <div className="landing-light">
        <div className="ll-loading">
          <div className="ll-loading-label">Analyzing</div>
          <div className="ll-loading-repo">{repoName}</div>

          <div className="ll-pipeline">
            <div className="pipeline-steps ll-steps">
              {PIPELINE_STEPS.map((step) => {
                const status = stepStatus(step.key, run.current_step, run.status);
                return (
                  <div key={step.key} className={`pipeline-step ll-step ll-step-${status}`}>
                    <div className="ll-step-dot">
                      {status === "completed" ? "\u2713" : status === "active" ? "\u25CF" : "\u25CB"}
                    </div>
                    <span className="ll-step-label">{step.label}</span>
                  </div>
                );
              })}
            </div>
            <div className="ll-progress-track">
              <div className="ll-progress-fill" style={{ width: `${Math.round(run.progress_pct)}%` }} />
            </div>
          </div>

          <div className="ll-badges">
            <span className={`ll-badge ${dustConfigured ? "ll-badge-ok" : ""}`}>
              Dust {dustConfigured ? "\u2713" : "\u2717"}
            </span>
            <span className={`ll-badge ${codewordsConfigured ? "ll-badge-ok" : ""}`}>
              CodeWords {codewordsConfigured ? "\u2713" : "\u2717"}
            </span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="landing-light">
      <div className="ll-hero">
        <h1 className="ll-headline">
          Meet <strong>Legacy Atlas</strong>
        </h1>
        <p className="ll-subtitle">AI-powered legacy code comprehension.</p>
      </div>

      <div className="ll-input-card">
        <form onSubmit={handleSubmit}>
          <input
            className="ll-input"
            value={repoUrl}
            onChange={(event) => setRepoUrl(event.target.value)}
            placeholder="Paste a GitHub repository URL..."
            required
          />

          <button
            type="button"
            className="ll-advanced-toggle"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            {showAdvanced ? "Hide options" : "Advanced options"}
          </button>

          {showAdvanced && (
            <div className="ll-advanced">
              <label className="ll-adv-label">
                Commit SHA
                <input
                  className="ll-adv-input"
                  value={commitSha}
                  onChange={(event) => setCommitSha(event.target.value)}
                  placeholder="main"
                />
              </label>
              <label className="ll-adv-label">
                Local Repo Path
                <input
                  className="ll-adv-input"
                  value={localPath}
                  onChange={(event) => setLocalPath(event.target.value)}
                  placeholder="/absolute/path/to/local/repo"
                />
              </label>
            </div>
          )}

          <button type="submit" className="ll-cta" disabled={isBusy}>
            {isBusy ? "Analyzing..." : "Analyze Repository \u2192"}
          </button>
        </form>
        {error && <p className="ll-error">{error}</p>}
      </div>

      <div className="ll-social">
        <p className="ll-social-label">Built for companies managing legacy codebases</p>
        <p className="ll-social-logos">SAP &bull; Oracle &bull; ERPNext &bull; Odoo &bull; Django &bull; Python</p>
      </div>

      <footer className="ll-footer">
        <p>{"{Tech: Europe}"} London Hackathon &mdash; Conduct Track</p>
        <p>Powered by Gemini &bull; Dust &bull; CodeWords</p>
      </footer>
    </div>
  );
}

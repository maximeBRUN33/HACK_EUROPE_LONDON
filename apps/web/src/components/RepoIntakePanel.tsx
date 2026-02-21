import { FormEvent, useState } from "react";
import type { RepoResponse, RunResponse } from "../lib/api";

type RepoIntakePanelProps = {
  isBusy: boolean;
  onStart: (repoUrl: string, commitSha: string, localPath: string) => Promise<{ repo: RepoResponse; run: RunResponse }>;
};

export function RepoIntakePanel({ isBusy, onStart }: RepoIntakePanelProps): JSX.Element {
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
    </section>
  );
}

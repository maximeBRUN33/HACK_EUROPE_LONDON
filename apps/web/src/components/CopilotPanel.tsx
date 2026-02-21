import { FormEvent, useState } from "react";
import type { CopilotResponse } from "../lib/api";

type CopilotPanelProps = {
  runId: string | null;
  response: CopilotResponse | null;
  isBusy: boolean;
  onAsk: (question: string) => Promise<void>;
};

export function CopilotPanel({ runId, response, isBusy, onAsk }: CopilotPanelProps): JSX.Element {
  const [question, setQuestion] = useState("Where is the sales confirmation logic and what breaks if I modify it?");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!runId) {
      setError("Run analysis first before asking copilot.");
      return;
    }
    setError(null);
    try {
      await onAsk(question);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to query copilot");
    }
  }

  return (
    <section className="card copilot-card">
      <div className="card-title-row">
        <h2>Developer Copilot</h2>
        <span className="badge">Cited</span>
      </div>
      <form onSubmit={handleSubmit} className="stack">
        <label>
          Question
          <textarea value={question} onChange={(event) => setQuestion(event.target.value)} rows={3} />
        </label>
        <button type="submit" disabled={isBusy}>{isBusy ? "Thinking..." : "Ask Copilot"}</button>
      </form>
      {error && <p className="error">{error}</p>}
      {response && (
        <div className="response">
          <p>{response.answer}</p>
          <h3>Citations</h3>
          <ul className="citation-list">
            {response.citations.map((citation) => (
              <li key={`${citation.file_path}-${citation.symbol}`}>
                <code>{citation.file_path}</code> | <code>{citation.symbol}</code> | {citation.reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

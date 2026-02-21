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
                <code>{citation.file_path}</code>
                {citation.line_start != null && (
                  <span className="citation-lines">
                    L{citation.line_start}{citation.line_end != null && citation.line_end !== citation.line_start ? `\u2013${citation.line_end}` : ""}
                  </span>
                )}
                {" | "}<code>{citation.symbol}</code>{" | "}{citation.reason}
              </li>
            ))}
          </ul>

          {response.risk_implications.length > 0 && (
            <>
              <h3>Risk Implications</h3>
              <ul className="implication-list">
                {response.risk_implications.map((item, idx) => (
                  <li key={idx} className="implication-item">{item}</li>
                ))}
              </ul>
            </>
          )}

          {response.related_nodes.length > 0 && (
            <>
              <h3>Related Nodes</h3>
              <div className="related-nodes">
                {response.related_nodes.map((nodeId) => (
                  <span key={nodeId} className="node-pill process">{nodeId}</span>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
}

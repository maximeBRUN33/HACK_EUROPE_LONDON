import { FormEvent, useState } from "react";
import type { CopilotResponse, CopilotWebCompareResponse } from "../lib/api";

type CopilotPanelProps = {
  runId: string | null;
  response: CopilotResponse | null;
  webCompare: CopilotWebCompareResponse | null;
  webCompareBusy: boolean;
  webCompareError: string | null;
  isBusy: boolean;
  onAsk: (question: string) => Promise<void>;
  onFocusNode?: (nodeId: string) => void;
  symbolNodeMap?: Map<string, string>;
};

export function CopilotPanel({
  runId,
  response,
  webCompare,
  webCompareBusy,
  webCompareError,
  isBusy,
  onAsk,
  onFocusNode,
  symbolNodeMap
}: CopilotPanelProps): JSX.Element {
  const [question, setQuestion] = useState("");
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

  function handleCitationClick(symbol: string) {
    if (!onFocusNode || !symbolNodeMap) return;
    const nodeId = symbolNodeMap.get(symbol);
    if (nodeId) {
      onFocusNode(nodeId);
    }
  }

  function handleRelatedNodeClick(nodeId: string) {
    if (onFocusNode) {
      onFocusNode(nodeId);
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
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={3}
            placeholder="Ask about the codebase... e.g., What happens if I change the sales logic?"
          />
        </label>
        <button type="submit" disabled={isBusy}>{isBusy ? "Thinking..." : "Ask Copilot"}</button>
      </form>
      {error && <p className="error">{error}</p>}
      {response && (
        <div className="response">
          <div className="copilot-answer-card">
            <h3>Answer</h3>
            <p>{response.answer}</p>
          </div>

          {response.citations.length > 0 && (
            <div className="copilot-section">
              <h3>Source References</h3>
              <div className="citation-cards">
                {response.citations.map((citation) => {
                  const matchedNodeId = symbolNodeMap?.get(citation.symbol);
                  return (
                    <div
                      key={`${citation.file_path}-${citation.symbol}`}
                      className={`citation-card ${matchedNodeId ? "clickable" : ""}`}
                      onClick={matchedNodeId ? () => handleCitationClick(citation.symbol) : undefined}
                      role={matchedNodeId ? "button" : undefined}
                      tabIndex={matchedNodeId ? 0 : undefined}
                      onKeyDown={matchedNodeId ? (e) => { if (e.key === "Enter") handleCitationClick(citation.symbol); } : undefined}
                    >
                      <div className="citation-card-header">
                        <code>{citation.file_path}</code>
                        {citation.line_start != null && (
                          <span className="citation-lines">
                            L{citation.line_start}{citation.line_end != null && citation.line_end !== citation.line_start ? `\u2013${citation.line_end}` : ""}
                          </span>
                        )}
                        {matchedNodeId && <span className="citation-link-icon" title="Jump to graph node">&rarr;</span>}
                      </div>
                      <div className="citation-card-symbol"><code>{citation.symbol}</code></div>
                      <div className="citation-card-reason">{citation.reason}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {response.risk_implications.length > 0 && (
            <div className="copilot-callout-box">
              <h3>Risk Implications</h3>
              <ul className="implication-list">
                {response.risk_implications.map((item, idx) => (
                  <li key={idx} className="implication-item">{item}</li>
                ))}
              </ul>
            </div>
          )}

          {response.related_nodes.length > 0 && (
            <div className="copilot-section">
              <h3>Related Components</h3>
              <div className="related-nodes">
                {response.related_nodes.map((nodeId) => (
                  <span
                    key={nodeId}
                    className={`node-pill process ${onFocusNode ? "clickable" : ""}`}
                    onClick={() => handleRelatedNodeClick(nodeId)}
                    role={onFocusNode ? "button" : undefined}
                    tabIndex={onFocusNode ? 0 : undefined}
                    onKeyDown={onFocusNode ? (e) => { if (e.key === "Enter") handleRelatedNodeClick(nodeId); } : undefined}
                  >
                    {nodeId}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="copilot-section">
            <div className="web-compare-card">
              <div className="web-compare-header">
                <h3>Web Comparison</h3>
                <span className="badge subtle">Gemini</span>
              </div>

              {webCompareBusy && <p className="muted">Searching Reddit and X for similar implementation guidance...</p>}

              {!webCompareBusy && webCompareError && (
                <p className="muted">Web comparison unavailable: {webCompareError}</p>
              )}

              {!webCompareBusy && !webCompareError && webCompare && (
                <>
                  <p className="web-compare-summary">{webCompare.summary}</p>

                  {webCompare.items.length === 0 && (
                    <p className="muted">No close public references found for this question yet.</p>
                  )}

                  {webCompare.items.length > 0 && (
                    <div className="web-compare-list">
                      {webCompare.items.map((item, index) => (
                        <a
                          key={`${item.url}-${index}`}
                          className="web-compare-item"
                          href={item.url}
                          target="_blank"
                          rel="noreferrer noopener"
                        >
                          <div className="web-compare-item-head">
                            <span className={`platform-pill ${item.platform}`}>{item.platform.toUpperCase()}</span>
                            <strong>{item.title}</strong>
                          </div>
                          <p>{item.snippet}</p>
                          {item.why_relevant && <span className="web-compare-why">{item.why_relevant}</span>}
                        </a>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

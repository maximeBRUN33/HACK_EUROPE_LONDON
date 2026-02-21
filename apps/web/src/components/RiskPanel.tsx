import type { RiskSummary } from "../lib/api";

type RiskPanelProps = {
  summary: RiskSummary | null;
};

export function RiskPanel({ summary }: RiskPanelProps): JSX.Element {
  return (
    <section className="card risk-card">
      <div className="card-title-row">
        <h2>Risk Observatory</h2>
        <span className="badge high">Critical Insight</span>
      </div>
      {!summary && <p className="muted">Risk findings appear after a run completes.</p>}
      {summary && (
        <>
          <p className="score">Overall Score: {summary.overall_score}</p>
          <ul className="finding-list">
            {summary.findings.map((finding) => (
              <li key={finding.id} className={`severity-${finding.severity}`}>
                <strong>{finding.title}</strong>
                <p>{finding.rationale}</p>
                {finding.migration_suggestions && finding.migration_suggestions.length > 0 && (
                  <ul className="migration-suggestions">
                    {finding.migration_suggestions.map((suggestion, idx) => (
                      <li key={idx} className="migration-suggestion-item">
                        <span className="suggestion-arrow">{"\u2192"}</span>
                        {suggestion}
                      </li>
                    ))}
                  </ul>
                )}
                <div className="finding-meta">
                  <span>{finding.category}</span>
                  <span>{finding.symbol}</span>
                  <span>{finding.severity}</span>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

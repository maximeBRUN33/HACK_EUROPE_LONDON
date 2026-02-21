import { useMemo, useState } from "react";
import type { RiskSummary } from "../lib/api";

type RiskPanelProps = {
  summary: RiskSummary | null;
};

const SEVERITY_ORDER: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
const SEVERITY_FILTERS = ["all", "critical", "high", "medium", "low"] as const;
type SeverityFilter = (typeof SEVERITY_FILTERS)[number];

export function RiskPanel({ summary }: RiskPanelProps): JSX.Element {
  const [filter, setFilter] = useState<SeverityFilter>("all");

  const sortedFindings = useMemo(() => {
    if (!summary) return [];
    const sorted = [...summary.findings].sort(
      (a, b) => (SEVERITY_ORDER[a.severity] ?? 9) - (SEVERITY_ORDER[b.severity] ?? 9)
    );
    if (filter === "all") return sorted;
    return sorted.filter((f) => f.severity === filter);
  }, [summary, filter]);

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

          <div className="risk-filters">
            {SEVERITY_FILTERS.map((sev) => (
              <button
                key={sev}
                className={`risk-filter-btn ${filter === sev ? "active" : ""} ${sev !== "all" ? `sev-${sev}` : ""}`}
                onClick={() => setFilter(sev)}
              >
                {sev === "all" ? `All (${summary.findings.length})` : `${sev} (${summary.findings.filter((f) => f.severity === sev).length})`}
              </button>
            ))}
          </div>

          <ul className="finding-list">
            {sortedFindings.map((finding) => (
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

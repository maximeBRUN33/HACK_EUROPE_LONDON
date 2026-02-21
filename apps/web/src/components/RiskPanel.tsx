import { useMemo, useState } from "react";
import type { EnrichmentPayload, RiskSummary } from "../lib/api";

type RiskPanelProps = {
  summary: RiskSummary | null;
  enrichment?: EnrichmentPayload | null;
};

const SEVERITY_ORDER: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
const SEVERITY_FILTERS = ["all", "critical", "high", "medium", "low"] as const;
type SeverityFilter = (typeof SEVERITY_FILTERS)[number];

export function RiskPanel({ summary, enrichment }: RiskPanelProps): JSX.Element {
  const [filter, setFilter] = useState<SeverityFilter>("all");

  const sortedFindings = useMemo(() => {
    if (!summary) return [];
    const sorted = [...summary.findings].sort(
      (a, b) => (SEVERITY_ORDER[a.severity] ?? 9) - (SEVERITY_ORDER[b.severity] ?? 9)
    );
    if (filter === "all") return sorted;
    return sorted.filter((f) => f.severity === filter);
  }, [summary, filter]);

  const migrationHints = useMemo(() => {
    if (!enrichment?.migration_hints) return [];
    const hints = enrichment.migration_hints;
    if (Array.isArray(hints)) return hints.map(String);
    if (typeof hints === "object") {
      return Object.entries(hints).map(([k, v]) => `${k}: ${String(v)}`);
    }
    return [];
  }, [enrichment]);

  const qualityChecks = useMemo(() => {
    if (!enrichment?.quality_checks) return [];
    const checks = enrichment.quality_checks;
    if (Array.isArray(checks)) {
      return checks.map((c) => {
        if (typeof c === "object" && c !== null) {
          const obj = c as Record<string, unknown>;
          return { label: String(obj.name ?? obj.label ?? obj.check ?? "Check"), passed: Boolean(obj.passed ?? obj.pass ?? obj.status === "pass") };
        }
        return { label: String(c), passed: true };
      });
    }
    if (typeof checks === "object") {
      return Object.entries(checks).map(([k, v]) => ({ label: k, passed: Boolean(v) }));
    }
    return [];
  }, [enrichment]);

  const hasEnrichment = migrationHints.length > 0 || qualityChecks.length > 0;

  return (
    <>
      {hasEnrichment && (
        <section className="card enrichment-card">
          <div className="card-title-row">
            <h2>Migration Intelligence</h2>
            <span className="badge subtle">Enrichment</span>
          </div>

          {migrationHints.length > 0 && (
            <div className="enrichment-section">
              <span className="detail-section-label">Migration Hints</span>
              <ul className="enrichment-list">
                {migrationHints.map((hint, i) => (
                  <li key={i} className="enrichment-hint-item">
                    <span className="suggestion-arrow">{"\u2192"}</span>
                    {hint}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {qualityChecks.length > 0 && (
            <div className="enrichment-section">
              <span className="detail-section-label">Quality Checks</span>
              <ul className="enrichment-list">
                {qualityChecks.map((check, i) => (
                  <li key={i} className="enrichment-check-item">
                    <span className={`check-indicator ${check.passed ? "check-pass" : "check-fail"}`}>
                      {check.passed ? "\u2713" : "\u2717"}
                    </span>
                    {check.label}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

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
    </>
  );
}

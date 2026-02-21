import { useMemo, useState } from "react";
import type { EnrichmentPayload, MigrationBlueprintPayload, RiskSummary } from "../lib/api";

type RiskPanelProps = {
  summary: RiskSummary | null;
  enrichment?: EnrichmentPayload | null;
  migrationBlueprint?: MigrationBlueprintPayload | null;
  blueprintLoading?: boolean;
};

const SEVERITY_ORDER: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
const SEVERITY_FILTERS = ["all", "critical", "high", "medium", "low"] as const;
type SeverityFilter = (typeof SEVERITY_FILTERS)[number];

function readinessBandColor(band: string): string {
  const lower = band.toLowerCase();
  if (lower === "high") return "var(--risk-low)";
  if (lower === "moderate" || lower === "medium") return "var(--risk-mid)";
  return "var(--risk-high)";
}

export function RiskPanel({ summary, enrichment, migrationBlueprint, blueprintLoading }: RiskPanelProps): JSX.Element {
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

  const ontologySummary = useMemo(() => {
    if (!enrichment?.ontology_enrichment) return [];
    const ont = enrichment.ontology_enrichment;
    if (typeof ont !== "object" || Array.isArray(ont)) return [];
    return Object.entries(ont).slice(0, 8).map(([k, v]) => [k, typeof v === "object" ? JSON.stringify(v) : String(v)] as [string, string]);
  }, [enrichment]);

  const enrichmentStatus = enrichment?.status;
  const enrichmentAvailable = enrichmentStatus === "completed";
  const enrichmentUnavailable = !enrichment || enrichmentStatus === "not_configured" || enrichmentStatus === "failed" || enrichmentStatus === "error";
  const enrichmentRunning = enrichmentStatus === "queued" || enrichmentStatus === "running";

  const extractionBoundaries = useMemo(() => {
    if (!migrationBlueprint?.extraction_boundaries) return [];
    return migrationBlueprint.extraction_boundaries.map((b) => {
      const anchor = String(b.anchor_symbol ?? b.anchor ?? b.symbol ?? "");
      const entities = Array.isArray(b.required_entities) ? (b.required_entities as string[]).join(", ") : String(b.required_entities ?? "");
      return { anchor, entities };
    });
  }, [migrationBlueprint]);

  const routingRisks = useMemo(() => {
    if (!migrationBlueprint?.integration_routing) return [];
    const routing = migrationBlueprint.integration_routing;
    if (Array.isArray(routing)) return routing.map(String);
    if (typeof routing === "object") {
      return Object.entries(routing).map(([k, v]) => `${k}: ${String(v)}`);
    }
    return [];
  }, [migrationBlueprint]);

  const topRisks = useMemo(() => {
    if (!migrationBlueprint?.top_risks) return [];
    return migrationBlueprint.top_risks.map((r) => {
      const title = String(r.title ?? r.risk ?? r.description ?? "");
      const detail = String(r.detail ?? r.rationale ?? r.impact ?? "");
      return { title, detail };
    });
  }, [migrationBlueprint]);

  return (
    <>
      {/* ── AI Enrichment section ── */}
      <section className="card enrichment-card">
        <div className="card-title-row">
          <h2>AI Enrichment</h2>
          {enrichmentAvailable && <span className="enrichment-status-badge enrichment-status-ok">Completed {"\u2713"}</span>}
          {enrichmentRunning && <span className="enrichment-status-badge enrichment-status-running">Running...</span>}
          {enrichmentUnavailable && <span className="enrichment-status-badge enrichment-status-off">Not Available</span>}
        </div>

        {enrichmentUnavailable && (
          <p className="enrichment-unavailable">CodeWords enrichment not available for this run.</p>
        )}

        {enrichmentRunning && (
          <p className="muted">Enrichment analysis is in progress...</p>
        )}

        {enrichmentAvailable && (
          <>
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

            {ontologySummary.length > 0 && (
              <div className="enrichment-section">
                <span className="detail-section-label">Ontology Enrichment</span>
                <div className="ontology-summary-card">
                  <dl className="ontology-dl">
                    {ontologySummary.map(([k, v]) => (
                      <div key={k} className="ontology-entry">
                        <dt>{k}</dt>
                        <dd>{v}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              </div>
            )}

            {qualityChecks.length === 0 && migrationHints.length === 0 && ontologySummary.length === 0 && (
              <p className="muted">Enrichment completed but no additional data was returned.</p>
            )}
          </>
        )}
      </section>

      {/* ── Risk Observatory ── */}
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

      {/* ── Migration Blueprint ── */}
      {blueprintLoading && (
        <section className="card blueprint-card">
          <div className="card-title-row">
            <h2>Migration Blueprint</h2>
            <span className="badge subtle">Loading...</span>
          </div>
          <p className="muted">Generating migration blueprint...</p>
        </section>
      )}

      {migrationBlueprint && (
        <section className="card blueprint-card">
          <div className="card-title-row">
            <h2>Migration Blueprint</h2>
            <span
              className="badge"
              style={{ background: readinessBandColor(migrationBlueprint.readiness_band) }}
            >
              {migrationBlueprint.readiness_band} Readiness
            </span>
          </div>

          <div className="blueprint-readiness">
            <span className="detail-section-label">Migration Readiness</span>
            <div className="blueprint-score-row">
              <span className="blueprint-score-number" style={{ color: readinessBandColor(migrationBlueprint.readiness_band) }}>
                {Math.round(migrationBlueprint.readiness_score)}
              </span>
              <span className="blueprint-score-band">{migrationBlueprint.readiness_band}</span>
            </div>
            <div className="detail-risk-row">
              <div className="detail-risk-bar">
                <div
                  className="detail-risk-fill"
                  style={{
                    width: `${Math.min(100, Math.round(migrationBlueprint.readiness_score))}%`,
                    background: readinessBandColor(migrationBlueprint.readiness_band)
                  }}
                />
              </div>
            </div>
          </div>

          {topRisks.length > 0 && (
            <div className="blueprint-section">
              <span className="detail-section-label">Top Risks</span>
              <ol className="blueprint-top-risks">
                {topRisks.map((risk, i) => (
                  <li key={i} className="blueprint-top-risk-item">
                    <strong>{risk.title}</strong>
                    {risk.detail && <p>{risk.detail}</p>}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {extractionBoundaries.length > 0 && (
            <div className="blueprint-section">
              <span className="detail-section-label">Extraction Boundaries</span>
              <ul className="blueprint-list">
                {extractionBoundaries.map((b, i) => (
                  <li key={i} className="blueprint-boundary-item">
                    <code>{b.anchor}</code>
                    {b.entities && <span className="blueprint-entities">{b.entities}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {routingRisks.length > 0 && (
            <div className="blueprint-section">
              <span className="detail-section-label">Integration Routing Risks</span>
              <ul className="blueprint-list">
                {routingRisks.map((risk, i) => (
                  <li key={i} className="blueprint-warning-item">{risk}</li>
                ))}
              </ul>
            </div>
          )}

          {migrationBlueprint.recommendations.length > 0 && (
            <div className="blueprint-section">
              <span className="detail-section-label">Recommendations</span>
              <ul className="blueprint-list">
                {migrationBlueprint.recommendations.map((rec, i) => (
                  <li key={i} className="blueprint-rec-item">
                    <span className="suggestion-arrow">{"\u2192"}</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {migrationBlueprint.phased_plan.length > 0 && (
            <div className="blueprint-section">
              <span className="detail-section-label">Phased Plan</span>
              <div className="timeline">
                {migrationBlueprint.phased_plan.map((phase, idx) => (
                  <div key={phase.phase_id} className={`timeline-step ${idx === migrationBlueprint.phased_plan.length - 1 ? "timeline-step-last" : ""}`}>
                    <div className="timeline-marker">
                      <div className="timeline-dot">{idx + 1}</div>
                      {idx < migrationBlueprint.phased_plan.length - 1 && <div className="timeline-line" />}
                    </div>
                    <div className="timeline-content">
                      <strong>{phase.title}</strong>
                      <p className="timeline-objective">{phase.objective}</p>
                      {phase.actions.length > 0 && (
                        <ul className="timeline-actions">
                          {phase.actions.map((action, i) => (
                            <li key={i}>{action}</li>
                          ))}
                        </ul>
                      )}
                      {phase.risk_watch.length > 0 && (
                        <div className="timeline-risk-watch">
                          <span className="timeline-risk-label">Risk watch:</span>
                          {phase.risk_watch.map((r, i) => (
                            <span key={i} className="timeline-risk-tag">{r}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}
    </>
  );
}

import { useEffect, useMemo, useState } from "react";
import type { EnrichmentPayload, EvidencePayload, GraphPayload, RiskSummary } from "../lib/api";
import { fetchNodeEvidence } from "../lib/api";
import { GraphCanvas } from "./GraphCanvas";

type GraphPanelProps = {
  title: string;
  graph: GraphPayload | null;
  evidence: EvidencePayload | null;
  evidenceLoading: boolean;
  onSelectNode: (nodeId: string) => void;
  focusedNodeId?: string | null;
  riskOverlay?: boolean;
  showEdgeLabels?: boolean;
  riskSummary?: RiskSummary | null;
  enrichment?: EnrichmentPayload | null;
};

export function GraphPanel({ title, graph, evidence, evidenceLoading, onSelectNode, focusedNodeId, riskOverlay, showEdgeLabels, riskSummary, enrichment }: GraphPanelProps): JSX.Element {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [nodeSubtitles, setNodeSubtitles] = useState<Map<string, string>>(new Map());

  useEffect(() => {
    if (focusedNodeId) {
      setSelectedNodeId(focusedNodeId);
    }
  }, [focusedNodeId]);

  useEffect(() => {
    if (!graph || graph.nodes.length === 0) {
      setNodeSubtitles(new Map());
      return;
    }
    const runId = graph.run_id;
    const subtitles = new Map<string, string>();
    Promise.all(
      graph.nodes.map(async (node) => {
        try {
          const ev = await fetchNodeEvidence(runId, node.id);
          const firstSymbol = ev.symbols[0];
          let subtitle = ev.files[0] ?? "";
          if (firstSymbol) {
            const parts = firstSymbol.split(".");
            subtitle = parts.length >= 2 ? parts[parts.length - 2] : firstSymbol;
          }
          if (subtitle) {
            subtitles.set(node.id, subtitle);
          }
        } catch {
          // skip nodes without evidence
        }
      })
    ).then(() => {
      setNodeSubtitles(new Map(subtitles));
    });
  }, [graph]);

  const selectedNode = useMemo(() => {
    if (!graph) {
      return null;
    }
    const fallback = graph.nodes[0] ?? null;
    const activeId = selectedNodeId ?? fallback?.id ?? null;
    return graph.nodes.find((node) => node.id === activeId) ?? fallback;
  }, [graph, selectedNodeId]);

  const connectedEdges = useMemo(() => {
    if (!graph || !selectedNode) {
      return [];
    }
    return graph.edges.filter((edge) => edge.source === selectedNode.id || edge.target === selectedNode.id);
  }, [graph, selectedNode]);

  const connectedNodeIds = useMemo(() => {
    if (!selectedNode) return [];
    const ids = new Set<string>();
    for (const edge of connectedEdges) {
      if (edge.source !== selectedNode.id) ids.add(edge.source);
      if (edge.target !== selectedNode.id) ids.add(edge.target);
    }
    return [...ids];
  }, [selectedNode, connectedEdges]);

  const relevantFindings = useMemo(() => {
    if (!riskSummary || !selectedNode || !evidence) return [];
    const symbolSet = new Set(evidence.symbols);
    return riskSummary.findings.filter((f) => symbolSet.has(f.symbol) || f.symbol === selectedNode.label || f.symbol === selectedNode.id);
  }, [riskSummary, selectedNode, evidence]);

  useEffect(() => {
    if (selectedNode?.id) {
      onSelectNode(selectedNode.id);
    }
  }, [onSelectNode, selectedNode?.id]);

  const riskPct = selectedNode ? Math.min(100, Math.round(selectedNode.risk_score)) : 0;
  const riskBarColor = riskPct > 70 ? "var(--risk-high)" : riskPct >= 50 ? "var(--risk-mid)" : "var(--risk-low)";

  return (
    <section className="card graph-card">
      <div className="card-title-row">
        <h2>{title}</h2>
        <span className="badge subtle">Interactive Graph</span>
      </div>

      {!graph && <p className="muted">Run an analysis to render the graph canvas.</p>}

      {graph && (
        <div className={`graph-split ${selectedNode ? "has-detail" : ""}`}>
          <div className="graph-main">
            <div className="graph-stats">
              <div>
                <span>Nodes</span>
                <strong>{graph.nodes.length}</strong>
              </div>
              <div>
                <span>Edges</span>
                <strong>{graph.edges.length}</strong>
              </div>
              <div>
                <span>Selected</span>
                <strong>{selectedNode?.label ?? "-"}</strong>
              </div>
            </div>

            <GraphCanvas graph={graph} selectedNodeId={selectedNode?.id ?? null} onSelectNode={setSelectedNodeId} nodeSubtitles={nodeSubtitles} riskOverlay={riskOverlay} showEdgeLabels={showEdgeLabels} />
          </div>

          {selectedNode && (
            <div className="detail-panel">
              <h3 className="detail-node-name">{selectedNode.label}</h3>
              <div className="detail-badges">
                <span className={`node-pill ${selectedNode.node_type}`}>{selectedNode.node_type}</span>
              </div>

              <div className="detail-section">
                <span className="detail-section-label">Risk Score</span>
                <div className="detail-risk-row">
                  <div className="detail-risk-bar">
                    <div className="detail-risk-fill" style={{ width: `${riskPct}%`, background: riskBarColor }} />
                  </div>
                  <span className="detail-risk-value" style={{ color: riskBarColor }}>{riskPct}</span>
                </div>
              </div>

              <div className="detail-section">
                <span className="detail-section-label">Evidence</span>
                {evidenceLoading && <p className="muted">Loading...</p>}
                {!evidenceLoading && !evidence && <p className="muted">No evidence available.</p>}
                {!evidenceLoading && evidence && (
                  <>
                    <p className="detail-explanation">{evidence.explanation}</p>
                    {evidence.files.length > 0 && (
                      <>
                        <span className="detail-sub-label">Files</span>
                        <ul className="detail-list">
                          {evidence.files.map((file) => (
                            <li key={file}><code>{file}</code></li>
                          ))}
                        </ul>
                      </>
                    )}
                    {evidence.symbols.length > 0 && (
                      <>
                        <span className="detail-sub-label">Symbols</span>
                        <ul className="detail-list">
                          {evidence.symbols.map((symbol) => (
                            <li key={symbol}><code>{symbol}</code></li>
                          ))}
                        </ul>
                      </>
                    )}
                  </>
                )}
              </div>

              {connectedNodeIds.length > 0 && (
                <div className="detail-section">
                  <span className="detail-section-label">Connected Nodes</span>
                  <div className="detail-connected">
                    {connectedNodeIds.map((id) => (
                      <span
                        key={id}
                        className="node-pill process clickable"
                        role="button"
                        tabIndex={0}
                        onClick={() => setSelectedNodeId(id)}
                        onKeyDown={(e) => { if (e.key === "Enter") setSelectedNodeId(id); }}
                      >
                        {id}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {enrichment && enrichment.ontology_enrichment && Object.keys(enrichment.ontology_enrichment).length > 0 && (() => {
                const ont = enrichment.ontology_enrichment;
                const nodeKey = selectedNode.label;
                const nodeData = (ont[nodeKey] ?? ont[selectedNode.id]) as Record<string, unknown> | undefined;
                const entries: [string, string][] = nodeData
                  ? Object.entries(nodeData).map(([k, v]) => [k, String(v)])
                  : [];
                if (entries.length === 0) return null;
                return (
                  <div className="detail-section">
                    <span className="detail-section-label">Ontology Enrichment</span>
                    <dl className="ontology-dl">
                      {entries.map(([k, v]) => (
                        <div key={k} className="ontology-entry">
                          <dt>{k}</dt>
                          <dd>{v}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                );
              })()}

              {relevantFindings.length > 0 && (
                <div className="detail-section">
                  <span className="detail-section-label">Migration Suggestions</span>
                  {relevantFindings.map((finding) =>
                    finding.migration_suggestions?.map((sug, idx) => (
                      <div key={`${finding.id}-${idx}`} className="migration-suggestion-item">
                        <span className="suggestion-arrow">{"\u2192"}</span>
                        {sug}
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

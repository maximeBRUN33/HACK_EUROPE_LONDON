import { useEffect, useMemo, useState } from "react";
import type { EnrichmentPayload, EvidencePayload, GraphPayload, RiskSummary } from "../lib/api";
import { fetchNodeEvidence } from "../lib/api";
import { GraphCanvas, humanizeLabel, nodeDescription } from "./GraphCanvas";

type GraphPanelProps = {
  title: string;
  graph: GraphPayload | null;
  evidence: EvidencePayload | null;
  evidenceLoading: boolean;
  onSelectNode: (nodeId: string) => void;
  focusedNodeId?: string | null;
  showEdgeLabels?: boolean;
  riskSummary?: RiskSummary | null;
  enrichment?: EnrichmentPayload | null;
  graphMode?: "process" | "lineage";
};

type NodeMeta = { crudOps: string[]; modules: string[] };

/** Extract entity name from evidence explanation text.
 *  Looks for patterns like: Entity `Stock`, entity "Order", data entity Stock */
function extractEntityName(explanation: string): string | null {
  const backtickMatch = explanation.match(/[Ee]ntity\s+`([^`]+)`/);
  if (backtickMatch) return backtickMatch[1];
  const quoteMatch = explanation.match(/[Ee]ntity\s+"([^"]+)"/);
  if (quoteMatch) return quoteMatch[1];
  const plainMatch = explanation.match(/[Ee]ntity\s+([A-Z][a-zA-Z]*)/);
  if (plainMatch) return plainMatch[1];
  return null;
}

/** Extract CRUD operations mentioned in evidence explanation. */
function extractCrudOps(explanation: string): string[] {
  const ops: string[] = [];
  const lower = explanation.toLowerCase();
  if (lower.includes("create") || lower.includes("insert") || lower.includes("add")) ops.push("Create");
  if (lower.includes("read") || lower.includes("fetch") || lower.includes("get") || lower.includes("list") || lower.includes("retrieve") || lower.includes("query")) ops.push("Read");
  if (lower.includes("update") || lower.includes("edit") || lower.includes("modify") || lower.includes("change")) ops.push("Update");
  if (lower.includes("delete") || lower.includes("remove") || lower.includes("destroy")) ops.push("Delete");
  return ops;
}

export function GraphPanel({ title, graph, evidence, evidenceLoading, onSelectNode, focusedNodeId, showEdgeLabels, riskSummary, enrichment, graphMode }: GraphPanelProps): JSX.Element {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [nodeDisplayNames, setNodeDisplayNames] = useState<Map<string, string>>(new Map());
  const [nodeSubtitles, setNodeSubtitles] = useState<Map<string, string>>(new Map());
  const [nodeMeta, setNodeMeta] = useState<Map<string, NodeMeta>>(new Map());
  const [showLegend, setShowLegend] = useState(false);
  const [showNodeInfo, setShowNodeInfo] = useState(false);

  useEffect(() => {
    if (focusedNodeId) {
      setSelectedNodeId(focusedNodeId);
    }
  }, [focusedNodeId]);

  useEffect(() => {
    if (!graph || graph.nodes.length === 0) {
      setNodeDisplayNames(new Map());
      setNodeSubtitles(new Map());
      setNodeMeta(new Map());
      return;
    }
    const runId = graph.run_id;
    const names = new Map<string, string>();
    const subtitles = new Map<string, string>();
    const meta = new Map<string, NodeMeta>();
    const isLineage = graphMode === "lineage";
    Promise.all(
      graph.nodes.map(async (node) => {
        try {
          const ev = await fetchNodeEvidence(runId, node.id);

          if (isLineage) {
            // For lineage: extract entity name from explanation
            const entityName = extractEntityName(ev.explanation) ?? humanizeLabel(node.label);
            names.set(node.id, entityName);
            // Extract CRUD ops and modules
            const crudOps = extractCrudOps(ev.explanation);
            const modules = ev.files.map((f) => f.split("/")[0] || f);
            meta.set(node.id, { crudOps, modules: [...new Set(modules)] });
          } else {
            // For process: extract class name from first symbol
            const firstSymbol = ev.symbols[0];
            if (firstSymbol) {
              const parts = firstSymbol.split(".");
              const className = parts.length >= 2 ? parts[parts.length - 2] : firstSymbol;
              names.set(node.id, humanizeLabel(className));
            }
          }

          // File path as subtitle
          const filePath = ev.files[0] ?? "";
          if (filePath) {
            subtitles.set(node.id, filePath);
          }
        } catch {
          // skip nodes without evidence
        }
      })
    ).then(() => {
      setNodeDisplayNames(new Map(names));
      setNodeSubtitles(new Map(subtitles));
      setNodeMeta(new Map(meta));
    });
  }, [graph, graphMode]);

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

  const uniqueModules = useMemo(() => {
    const mods = new Set<string>();
    for (const m of nodeMeta.values()) {
      for (const mod of m.modules) mods.add(mod);
    }
    return mods.size;
  }, [nodeMeta]);

  const selectedNodeName = selectedNode ? (nodeDisplayNames.get(selectedNode.id) ?? humanizeLabel(selectedNode.label)) : "";
  const selectedMeta = selectedNode ? nodeMeta.get(selectedNode.id) : undefined;

  const riskPct = selectedNode ? Math.min(100, Math.round(selectedNode.risk_score)) : 0;
  const riskBarColor = riskPct > 70 ? "var(--risk-high)" : riskPct >= 50 ? "var(--risk-mid)" : "var(--risk-low)";
  const riskExplanation = riskPct > 70
    ? "High risk \u2014 changes here could break other parts"
    : riskPct > 50
      ? "Elevated risk \u2014 consider refactoring before changes"
      : riskPct >= 30
        ? "Moderate risk \u2014 some complexity to manage"
        : "Low risk \u2014 simple, well-structured code";

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
            {graphMode === "lineage" && graph.nodes.length > 0 && (
              <p className="graph-dynamic-desc">
                Shows how {graph.nodes.length} data entit{graph.nodes.length === 1 ? "y" : "ies"} flow across {uniqueModules || "multiple"} module{uniqueModules === 1 ? "" : "s"} in this codebase.
              </p>
            )}
            <div className="graph-stats">
              <div>
                <span>{graphMode === "lineage" ? "Entities" : "Nodes"}</span>
                <strong>{graph.nodes.length}</strong>
              </div>
              <div>
                <span>{graphMode === "lineage" ? "Flows" : "Edges"}</span>
                <strong>{graph.edges.length}</strong>
              </div>
              <div>
                <span>Selected</span>
                <strong>{selectedNodeName || "-"}</strong>
              </div>
            </div>

            <GraphCanvas graph={graph} selectedNodeId={selectedNode?.id ?? null} onSelectNode={setSelectedNodeId} nodeDisplayNames={nodeDisplayNames} nodeSubtitles={nodeSubtitles} showEdgeLabels={showEdgeLabels} />

            {graphMode && (
              <div className="graph-legend-wrap">
                <button className="legend-toggle" onClick={() => setShowLegend(!showLegend)}>
                  {showLegend ? "Hide legend" : "Show legend"}
                </button>
                {showLegend && (
                  <div className="graph-legend">
                    {graphMode === "process" && (
                      <>
                        <div className="legend-item"><span className="legend-dot legend-dot-process" /> Process Node &mdash; a meaningful execution step</div>
                        <div className="legend-item"><span className="legend-dot legend-dot-risk" /> Risk Node &mdash; a high-risk hotspot or aggregation point</div>
                        <div className="legend-item"><span className="legend-line legend-line-control" /> Control Edge &mdash; execution relationship between steps</div>
                        <div className="legend-item"><span className="legend-line legend-line-risk" /> Risk Edge &mdash; risk linkage to process areas</div>
                      </>
                    )}
                    {graphMode === "lineage" && (
                      <>
                        <div className="legend-item"><span className="legend-dot legend-dot-data" /> Entity Node &mdash; a business data object (e.g., Customer, Order)</div>
                        <div className="legend-item"><span className="legend-line legend-line-data" /> Data Edge &mdash; inferred data movement between entities</div>
                      </>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {selectedNode && (
            <div className="detail-panel">
              <h3 className="detail-node-name">{selectedNodeName}</h3>
              <p className="detail-node-description">
                {graphMode === "lineage"
                  ? `Tracks ${selectedNodeName} data across the system \u2014 how it\u2019s created, read, updated, and deleted`
                  : nodeDescription(selectedNodeName)}
              </p>
              <div className="detail-badges">
                <span className={`node-pill ${selectedNode.node_type}`}>{selectedNode.node_type}</span>
              </div>

              {graphMode === "process" && (
                <div className="node-info-toggle-wrap">
                  <button className="node-info-toggle" onClick={() => setShowNodeInfo(!showNodeInfo)}>
                    {showNodeInfo ? "Hide explanation" : "What is this?"}
                  </button>
                  {showNodeInfo && (
                    <p className="node-info-text">
                      A workflow node represents a key business-relevant step extracted from code execution analysis. It is selected from top-ranked functions based on complexity, call patterns, and entity signals.
                    </p>
                  )}
                </div>
              )}

              {graphMode === "lineage" && selectedMeta && selectedMeta.crudOps.length > 0 && (
                <div className="detail-section">
                  <span className="detail-section-label">Detected Operations</span>
                  <div className="crud-ops">
                    {(["Create", "Read", "Update", "Delete"] as const).map((op) => (
                      <span key={op} className={`crud-pill ${selectedMeta.crudOps.includes(op) ? "crud-active" : "crud-inactive"}`}>
                        {op}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {graphMode === "lineage" && selectedMeta && selectedMeta.modules.length > 0 && (
                <div className="detail-section">
                  <span className="detail-section-label">Accessed By Modules</span>
                  <div className="detail-connected">
                    {selectedMeta.modules.map((mod) => (
                      <span key={mod} className="node-pill data">{mod}</span>
                    ))}
                  </div>
                </div>
              )}

              <div className="detail-section">
                <span className="detail-section-label">Risk Score</span>
                <div className="detail-risk-row">
                  <div className="detail-risk-bar">
                    <div className="detail-risk-fill" style={{ width: `${riskPct}%`, background: riskBarColor }} />
                  </div>
                  <span className="detail-risk-value" style={{ color: riskBarColor }}>{riskPct}</span>
                </div>
                <p className="risk-explanation">{riskExplanation}</p>
              </div>

              <div className="detail-section">
                <span className="detail-section-label">{graphMode === "lineage" ? "Evidence" : "What This Does"}</span>
                {evidenceLoading && <p className="muted">Loading...</p>}
                {!evidenceLoading && !evidence && <p className="muted">No evidence available.</p>}
                {!evidenceLoading && evidence && (
                  <>
                    <p className="detail-explanation">{evidence.explanation}</p>
                    {evidence.files.length > 0 && (
                      <>
                        <span className="detail-sub-label">Source Files</span>
                        <ul className="detail-list">
                          {evidence.files.map((file) => (
                            <li key={file}><code>{file}</code></li>
                          ))}
                        </ul>
                      </>
                    )}
                    {evidence.symbols.length > 0 && (
                      <>
                        <span className="detail-sub-label">Code References</span>
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
                  <span className="detail-section-label">Connects To</span>
                  <div className="detail-connected">
                    {connectedNodeIds.map((id) => {
                      const label = nodeDisplayNames.get(id) ?? humanizeLabel(graph.nodes.find((n) => n.id === id)?.label ?? id);
                      return (
                        <span
                          key={id}
                          className="node-pill process clickable"
                          role="button"
                          tabIndex={0}
                          onClick={() => setSelectedNodeId(id)}
                          onKeyDown={(e) => { if (e.key === "Enter") setSelectedNodeId(id); }}
                        >
                          {label}
                        </span>
                      );
                    })}
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
                  <span className="detail-section-label">Recommended Actions</span>
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

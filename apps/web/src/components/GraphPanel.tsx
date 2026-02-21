import { useEffect, useMemo, useState } from "react";
import type { EvidencePayload, GraphPayload } from "../lib/api";
import { GraphCanvas } from "./GraphCanvas";

type GraphPanelProps = {
  title: string;
  graph: GraphPayload | null;
  evidence: EvidencePayload | null;
  evidenceLoading: boolean;
  onSelectNode: (nodeId: string) => void;
};

export function GraphPanel({ title, graph, evidence, evidenceLoading, onSelectNode }: GraphPanelProps): JSX.Element {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

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

  useEffect(() => {
    if (selectedNode?.id) {
      onSelectNode(selectedNode.id);
    }
  }, [onSelectNode, selectedNode?.id]);

  return (
    <section className="card graph-card">
      <div className="card-title-row">
        <h2>{title}</h2>
        <span className="badge subtle">Interactive Graph</span>
      </div>

      {!graph && <p className="muted">Run an analysis to render the graph canvas.</p>}

      {graph && (
        <>
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

          <GraphCanvas graph={graph} selectedNodeId={selectedNode?.id ?? null} onSelectNode={setSelectedNodeId} />

          <div className="graph-inspector">
            {selectedNode && (
              <>
                <h3>{selectedNode.label}</h3>
                <p>
                  <span className={`node-pill ${selectedNode.node_type}`}>{selectedNode.node_type}</span>
                  <span className="node-risk">Risk {Math.round(selectedNode.risk_score)}</span>
                </p>
                <ul className="edge-list compact">
                  {connectedEdges.slice(0, 5).map((edge, index) => (
                    <li key={`${edge.source}-${edge.target}-${index}`}>
                      <code>{edge.source}</code>
                      <span>{"->"}</span>
                      <code>{edge.target}</code>
                      <span>{edge.edge_type}</span>
                    </li>
                  ))}
                </ul>
                {connectedEdges.length === 0 && <p className="muted">No direct edges for this node.</p>}

                <div className="evidence-panel">
                  <h4>Evidence</h4>
                  {evidenceLoading && <p className="muted">Loading evidence...</p>}
                  {!evidenceLoading && !evidence && <p className="muted">No evidence available for this node.</p>}
                  {!evidenceLoading && evidence && (
                    <>
                      <p>{evidence.explanation}</p>
                      <ul className="edge-list">
                        {evidence.files.map((file) => (
                          <li key={file}>
                            <code>{file}</code>
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              </>
            )}
          </div>
        </>
      )}
    </section>
  );
}

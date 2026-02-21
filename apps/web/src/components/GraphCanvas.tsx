import { useEffect, useMemo, useRef, useState } from "react";
import type { GraphPayload, GraphNode } from "../lib/api";

type GraphCanvasProps = {
  graph: GraphPayload;
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
  nodeDisplayNames?: Map<string, string>;
  nodeSubtitles?: Map<string, string>;
  riskOverlay?: boolean;
  showEdgeLabels?: boolean;
};

type Point = { x: number; y: number };

const NODE_WIDTH = 260;
const NODE_HEIGHT = 52;
const LAYER_GAP_Y = 110;
const NODE_GAP_X = 40;
const PADDING = 80;

export function GraphCanvas({ graph, selectedNodeId, onSelectNode, nodeDisplayNames, nodeSubtitles, riskOverlay, showEdgeLabels }: GraphCanvasProps): JSX.Element {
  const { positions, viewWidth, viewHeight } = useMemo(() => buildLayout(graph), [graph]);
  const svgRef = useRef<SVGSVGElement>(null);
  const dragRef = useRef<{ startX: number; startY: number; startPanX: number; startPanY: number } | null>(null);
  const [viewState, setViewState] = useState({ zoom: 1, panX: 0, panY: 0 });

  // Reset zoom/pan when graph data changes
  useEffect(() => {
    setViewState({ zoom: 1, panX: 0, panY: 0 });
  }, [graph]);

  // Non-passive wheel listener for zoom-toward-cursor
  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;

    function onWheel(e: WheelEvent) {
      e.preventDefault();
      const factor = e.deltaY > 0 ? 0.9 : 1.1;
      setViewState((prev) => {
        const newZoom = Math.max(0.3, Math.min(5, prev.zoom * factor));
        const rect = svg!.getBoundingClientRect();
        const cx = (e.clientX - rect.left) / rect.width;
        const cy = (e.clientY - rect.top) / rect.height;
        const oldW = viewWidth / prev.zoom;
        const oldH = viewHeight / prev.zoom;
        const newW = viewWidth / newZoom;
        const newH = viewHeight / newZoom;
        return {
          zoom: newZoom,
          panX: prev.panX + cx * (oldW - newW),
          panY: prev.panY + cy * (oldH - newH),
        };
      });
    }

    svg.addEventListener("wheel", onWheel, { passive: false });
    return () => svg.removeEventListener("wheel", onWheel);
  }, [viewWidth, viewHeight]);

  function handleMouseDown(e: React.MouseEvent<SVGSVGElement>) {
    if (e.button !== 0) return;
    if ((e.target as Element).closest(".graph-node")) return;
    e.preventDefault();
    dragRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      startPanX: viewState.panX,
      startPanY: viewState.panY,
    };
  }

  function handleMouseMove(e: React.MouseEvent<SVGSVGElement>) {
    if (!dragRef.current) return;
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    setViewState((prev) => {
      const scaleX = (viewWidth / prev.zoom) / rect.width;
      const scaleY = (viewHeight / prev.zoom) / rect.height;
      return {
        ...prev,
        panX: dragRef.current!.startPanX - (e.clientX - dragRef.current!.startX) * scaleX,
        panY: dragRef.current!.startPanY - (e.clientY - dragRef.current!.startY) * scaleY,
      };
    });
  }

  function handleMouseUp() {
    dragRef.current = null;
  }

  function handleZoomIn() {
    setViewState((prev) => {
      const newZoom = Math.min(5, prev.zoom * 1.3);
      const oldW = viewWidth / prev.zoom;
      const oldH = viewHeight / prev.zoom;
      const newW = viewWidth / newZoom;
      const newH = viewHeight / newZoom;
      return { zoom: newZoom, panX: prev.panX + (oldW - newW) / 2, panY: prev.panY + (oldH - newH) / 2 };
    });
  }

  function handleZoomOut() {
    setViewState((prev) => {
      const newZoom = Math.max(0.3, prev.zoom / 1.3);
      const oldW = viewWidth / prev.zoom;
      const oldH = viewHeight / prev.zoom;
      const newW = viewWidth / newZoom;
      const newH = viewHeight / newZoom;
      return { zoom: newZoom, panX: prev.panX + (oldW - newW) / 2, panY: prev.panY + (oldH - newH) / 2 };
    });
  }

  function handleResetView() {
    setViewState({ zoom: 1, panX: 0, panY: 0 });
  }

  const vbW = viewWidth / viewState.zoom;
  const vbH = viewHeight / viewState.zoom;
  const halfW = NODE_WIDTH / 2;
  const halfH = NODE_HEIGHT / 2;

  return (
    <div className="graph-canvas-wrap">
      <div className="graph-controls">
        <button onClick={handleZoomIn} title="Zoom in">+</button>
        <button onClick={handleZoomOut} title="Zoom out">&minus;</button>
        <button onClick={handleResetView} title="Reset view">&#x21BA;</button>
      </div>
      <svg
        ref={svgRef}
        className="graph-canvas"
        viewBox={`${viewState.panX} ${viewState.panY} ${vbW} ${vbH}`}
        role="img"
        aria-label="Dependency graph canvas"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <defs>
          <marker id="arrow-control" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#D1D5DB" />
          </marker>
          <marker id="arrow-data" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#D1D5DB" />
          </marker>
          <marker id="arrow-data-lg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#D1D5DB" />
          </marker>
          <marker id="arrow-risk" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#D1D5DB" />
          </marker>
        </defs>

        {graph.edges.map((edge, index) => {
          const source = positions.get(edge.source);
          const target = positions.get(edge.target);
          if (!source || !target) {
            return null;
          }

          const path = verticalCurvedPath(source, target);
          const markerId = edge.edge_type === "data" ? (showEdgeLabels ? "arrow-data-lg" : "arrow-data") : edge.edge_type === "risk" ? "arrow-risk" : "arrow-control";

          return (
            <path
              key={`${edge.source}-${edge.target}-${index}`}
              d={path}
              className={`edge edge-${edge.edge_type}`}
              markerEnd={`url(#${markerId})`}
              strokeOpacity={Math.max(0.35, edge.confidence)}
            />
          );
        })}

        {showEdgeLabels && graph.edges.map((edge, index) => {
          const source = positions.get(edge.source);
          const target = positions.get(edge.target);
          if (!source || !target) return null;
          const midX = (source.x + target.x) / 2;
          const midY = (source.y + target.y) / 2;
          const label = edge.edge_type === "data" ? "data flow" : edge.edge_type;
          const pillW = label.length * 7 + 16;
          const pillH = 20;
          return (
            <g key={`elabel-${index}`}>
              <rect x={midX + 6} y={midY - pillH / 2} width={pillW} height={pillH} rx={10} className="edge-label-pill" />
              <text x={midX + 6 + pillW / 2} y={midY + 4} className="edge-label" textAnchor="middle">
                {label}
              </text>
            </g>
          );
        })}

        {graph.nodes.map((node) => {
          const point = positions.get(node.id);
          if (!point) {
            return null;
          }

          const isSelected = selectedNodeId === node.id;
          const riskClass = riskOverlay ? riskLevelClass(node.risk_score) : "";
          const riskColor = riskScoreColor(node.risk_score);
          return (
            <g
              key={node.id}
              className={`graph-node node-${node.node_type} ${isSelected ? "selected" : ""} ${riskClass}`}
              transform={`translate(${point.x}, ${point.y})`}
              role="button"
              tabIndex={0}
              onClick={() => onSelectNode(node.id)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelectNode(node.id);
                }
              }}
            >
              <rect x={-halfW} y={-halfH} rx={12} ry={12} width={NODE_WIDTH} height={NODE_HEIGHT} />
              <circle cx={halfW - 18} cy={0} r={7} fill={riskColor} opacity={0.85} />
              <text className="node-label" x={-halfW + 16} y={-6} textAnchor="start">
                {truncate(nodeDisplayNames?.get(node.id) ?? humanizeLabel(node.label), 30)}
              </text>
              <text className="node-subtitle" x={-halfW + 16} y={10} textAnchor="start">
                {truncate(nodeSubtitles?.get(node.id) ?? "", 36)}
              </text>
              <text className="node-meta" x={halfW - 32} y={-6} textAnchor="end">
                {Math.round(node.risk_score)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

/** Convert a PascalCase class/function name into a verb-first readable action.
 *  "SaleCreateView" → "Create Sale", "Risk Aggregator" → "Risk Aggregator" */
export function humanizeLabel(label: string): string {
  // Already human-readable (contains spaces and no PascalCase pattern)
  if (label.includes(" ") && !/[a-z][A-Z]/.test(label)) return label;

  const words = label
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/([A-Z]+)([A-Z][a-z])/g, "$1 $2")
    .replace(/_/g, " ")
    .split(/\s+/);

  // Strip framework suffixes
  const strip = ["View", "Model", "Serializer", "Controller", "Handler", "Manager", "Mixin"];
  if (words.length > 1 && strip.includes(words[words.length - 1])) {
    words.pop();
  }

  // Reorder so verb comes first: ["Sale", "Create"] → ["Create", "Sale"]
  const verbs = ["Create", "Delete", "Update", "Edit", "Select", "List", "Destroy", "Retrieve"];
  const verbIdx = words.findIndex((w) => verbs.includes(w));
  if (verbIdx > 0) {
    const verb = words.splice(verbIdx, 1)[0];
    words.unshift(verb);
  }

  return words.join(" ");
}

/** Generate a one-line business description for a humanized label. */
export function nodeDescription(readableLabel: string): string {
  const KNOWN: Record<string, string> = {
    "Create Sale": "Creates a new sale transaction in the system",
    "Create Purchase": "Creates a new purchase order",
    "Delete Stock": "Removes items from inventory",
    "Purchase Bill": "Records a purchase bill from a supplier",
    "Sale Bill": "Records a bill for a completed sale",
    "Select Supplier": "Selects which supplier to order from",
    "Delete Purchase": "Deletes a purchase record",
    "Risk Aggregator": "Highlights the highest-risk area in the codebase",
  };
  if (KNOWN[readableLabel]) return KNOWN[readableLabel];
  return `Handles ${readableLabel} operations`;
}

function truncate(value: string, max: number): string {
  if (value.length <= max) {
    return value;
  }
  return `${value.slice(0, max - 3)}...`;
}

function riskLevelClass(score: number): string {
  if (score > 70) return "risk-high";
  if (score >= 50) return "risk-medium";
  return "risk-low";
}

function riskScoreColor(score: number): string {
  if (score > 70) return "#EF4444";
  if (score >= 50) return "#F59E0B";
  return "#22C55E";
}

function verticalCurvedPath(source: Point, target: Point): string {
  const controlOffset = Math.max(30, Math.abs(target.y - source.y) * 0.35);
  const c1y = source.y + controlOffset;
  const c2y = target.y - controlOffset;
  return `M ${source.x} ${source.y} C ${source.x} ${c1y}, ${target.x} ${c2y}, ${target.x} ${target.y}`;
}

function buildLayout(graph: GraphPayload): { positions: Map<string, Point>; viewWidth: number; viewHeight: number } {
  const positions = new Map<string, Point>();
  const byId = new Map(graph.nodes.map((node) => [node.id, node]));

  if (graph.nodes.length === 0) {
    return { positions, viewWidth: 960, viewHeight: 420 };
  }

  const outgoing = new Map<string, string[]>();
  const indegree = new Map<string, number>();

  for (const node of graph.nodes) {
    outgoing.set(node.id, []);
    indegree.set(node.id, 0);
  }

  for (const edge of graph.edges) {
    if (!byId.has(edge.source) || !byId.has(edge.target)) {
      continue;
    }
    outgoing.get(edge.source)?.push(edge.target);
    indegree.set(edge.target, (indegree.get(edge.target) ?? 0) + 1);
  }

  const roots = graph.nodes.filter((node) => (indegree.get(node.id) ?? 0) === 0).map((node) => node.id);
  const queue = roots.length > 0 ? [...roots] : [graph.nodes[0].id];

  const layerByNode = new Map<string, number>();
  const visited = new Set<string>();
  for (const root of queue) {
    layerByNode.set(root, 0);
  }

  while (queue.length > 0) {
    const current = queue.shift();
    if (!current || visited.has(current)) {
      continue;
    }
    visited.add(current);
    const currentLayer = layerByNode.get(current) ?? 0;
    for (const next of outgoing.get(current) ?? []) {
      if (!visited.has(next)) {
        const nextLayer = currentLayer + 1;
        if (!layerByNode.has(next) || nextLayer > (layerByNode.get(next) ?? 0)) {
          layerByNode.set(next, nextLayer);
        }
        queue.push(next);
      }
    }
  }

  for (const node of graph.nodes) {
    if (!layerByNode.has(node.id)) {
      layerByNode.set(node.id, Math.max(...layerByNode.values(), 0));
    }
  }

  const layers = new Map<number, GraphNode[]>();
  for (const node of graph.nodes) {
    const layer = layerByNode.get(node.id) ?? 0;
    const bucket = layers.get(layer) ?? [];
    bucket.push(node);
    layers.set(layer, bucket);
  }

  const sortedLayers = [...layers.entries()].sort((a, b) => a[0] - b[0]);
  const layerCount = sortedLayers.length;
  const maxNodesInLayer = Math.max(...sortedLayers.map(([, nodes]) => nodes.length), 1);
  const viewWidth = Math.max(960, PADDING * 2 + maxNodesInLayer * (NODE_WIDTH + NODE_GAP_X));
  const viewHeight = Math.max(420, PADDING * 2 + layerCount * LAYER_GAP_Y);

  for (const [layer, nodes] of sortedLayers) {
    const y = PADDING + layer * LAYER_GAP_Y;
    const totalWidth = nodes.length * NODE_WIDTH + (nodes.length - 1) * NODE_GAP_X;
    const startX = (viewWidth - totalWidth) / 2 + NODE_WIDTH / 2;
    nodes.forEach((node, index) => {
      const x = startX + index * (NODE_WIDTH + NODE_GAP_X);
      positions.set(node.id, { x, y });
    });
  }

  return { positions, viewWidth, viewHeight };
}

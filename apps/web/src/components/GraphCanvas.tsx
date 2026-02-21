import { useMemo } from "react";
import type { GraphPayload, GraphNode } from "../lib/api";

type GraphCanvasProps = {
  graph: GraphPayload;
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
};

type Point = { x: number; y: number };

const WIDTH = 960;
const HEIGHT = 420;

export function GraphCanvas({ graph, selectedNodeId, onSelectNode }: GraphCanvasProps): JSX.Element {
  const positions = useMemo(() => buildLayout(graph), [graph]);

  return (
    <div className="graph-canvas-wrap">
      <svg className="graph-canvas" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="Dependency graph canvas">
        <defs>
          <marker id="arrow-control" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#5ec9f3" />
          </marker>
          <marker id="arrow-data" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#7ce3b6" />
          </marker>
          <marker id="arrow-risk" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#ff8a6f" />
          </marker>
        </defs>

        {graph.edges.map((edge, index) => {
          const source = positions.get(edge.source);
          const target = positions.get(edge.target);
          if (!source || !target) {
            return null;
          }

          const path = curvedPath(source, target);
          const markerId = edge.edge_type === "data" ? "arrow-data" : edge.edge_type === "risk" ? "arrow-risk" : "arrow-control";

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

        {graph.nodes.map((node) => {
          const point = positions.get(node.id);
          if (!point) {
            return null;
          }

          const isSelected = selectedNodeId === node.id;
          return (
            <g
              key={node.id}
              className={`graph-node node-${node.node_type} ${isSelected ? "selected" : ""}`}
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
              <rect x={-72} y={-24} rx={12} ry={12} width={144} height={48} />
              <text className="node-label" x={0} y={-2} textAnchor="middle">
                {truncate(node.label, 22)}
              </text>
              <text className="node-meta" x={0} y={14} textAnchor="middle">
                {node.node_type} | risk {Math.round(node.risk_score)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function truncate(value: string, max: number): string {
  if (value.length <= max) {
    return value;
  }
  return `${value.slice(0, max - 3)}...`;
}

function curvedPath(source: Point, target: Point): string {
  const controlOffset = Math.max(40, Math.abs(target.x - source.x) * 0.4);
  const c1x = source.x + controlOffset;
  const c2x = target.x - controlOffset;
  return `M ${source.x} ${source.y} C ${c1x} ${source.y}, ${c2x} ${target.y}, ${target.x} ${target.y}`;
}

function buildLayout(graph: GraphPayload): Map<string, Point> {
  const points = new Map<string, Point>();
  const byId = new Map(graph.nodes.map((node) => [node.id, node]));

  if (graph.nodes.length === 0) {
    return points;
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
  for (const root of queue) {
    layerByNode.set(root, 0);
  }

  while (queue.length > 0) {
    const current = queue.shift();
    if (!current) {
      continue;
    }
    const currentLayer = layerByNode.get(current) ?? 0;
    for (const next of outgoing.get(current) ?? []) {
      const nextLayer = currentLayer + 1;
      if (!layerByNode.has(next) || nextLayer > (layerByNode.get(next) ?? 0)) {
        layerByNode.set(next, nextLayer);
      }
      if (!queue.includes(next)) {
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
  const maxLayer = Math.max(...sortedLayers.map(([layer]) => layer));

  for (const [layer, nodes] of sortedLayers) {
    const x = maxLayer === 0 ? WIDTH / 2 : 90 + (layer / maxLayer) * (WIDTH - 180);
    const verticalGap = HEIGHT / (nodes.length + 1);
    nodes.forEach((node, index) => {
      const y = (index + 1) * verticalGap;
      points.set(node.id, { x, y });
    });
  }

  return points;
}

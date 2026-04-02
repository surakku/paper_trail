"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { Badge } from "@/components/ui/badge";
import { getGraph } from "@/lib/api";
import type { GraphData, GraphNode } from "@/lib/types";
import { RefreshCw, ZoomIn, ZoomOut, Maximize2 } from "lucide-react";

// react-force-graph-2d must be dynamically imported (it uses browser APIs)
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

const NODE_COLORS: Record<string, string> = {
  Paper: "#3b82f6",
  Author: "#10b981",
  Concept: "#f59e0b",
  Institution: "#8b5cf6",
  WebContent: "#ec4899",
};

const NODE_LABELS: Record<string, string> = {
  Paper: "Paper",
  Author: "Author",
  Concept: "Concept",
  Institution: "Institution",
  WebContent: "Web",
};

interface GraphPanelProps {
  onNodeSelect?: (node: GraphNode) => void;
}

export function GraphPanel({ onNodeSelect }: GraphPanelProps) {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const graphRef = useRef<any>(null);

  // Assign hierarchical y-positions based on node type
  function applyHierarchicalLayout(data: GraphData): GraphData {
    const layerHeights: Record<string, number> = {
      Author: -300,
      Paper: 0,
      Concept: 300,
      Institution: 400,
      WebContent: 500,
    };

    // Count nodes per layer
    const layerCounts: Record<number, number> = {};
    const layerIndices: Record<number, number> = {};
    
    data.nodes.forEach(node => {
      const layer = layerHeights[node.type] ?? 0;
      layerCounts[layer] = (layerCounts[layer] ?? 0) + 1;
    });

    // Assign positions with spreading
    const nodesWithLayout = data.nodes.map(node => {
      const layer = layerHeights[node.type] ?? 0;
      const totalInLayer = layerCounts[layer];
      const indexInLayer = layerIndices[layer] ?? 0;
      layerIndices[layer] = indexInLayer + 1;
      
      // Y-position based on layer (fixed vertically)
      const yPosition = layer;
      
      // X-position spread out with significant gaps between nodes in the same layer
      const xPosition = (indexInLayer - totalInLayer / 2) * (400 / Math.max(totalInLayer, 1));
      
      return {
        ...node,
        x: xPosition,
        y: yPosition,
        fy: yPosition, // Lock Y position to maintain hierarchy
      };
    });

    return { nodes: nodesWithLayout, links: data.links };
  }

  async function loadGraph() {
    setLoading(true);
    try {
      const data = await getGraph(300);
      console.log("📊 Graph Data Loaded:", {
        nodesCount: data.nodes.length,
        linksCount: data.links.length,
      });
      
      // Verify links reference valid nodes
      const nodeIds = new Set(data.nodes.map(n => n.id));
      const invalidLinks = data.links.filter(l => !nodeIds.has(l.source) || !nodeIds.has(l.target));
      if (invalidLinks.length > 0) {
        console.warn("⚠️ Invalid links found:", invalidLinks);
      } else {
        console.log("✅ All links reference valid nodes");
      }
      
      // Apply hierarchical layout
      const layoutData = applyHierarchicalLayout(data);
      setGraphData(layoutData);
    } catch (error) {
      console.error("Error loading graph:", error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadGraph(); }, []);

  const handleNodeClick = useCallback((node: any) => {
    setSelected(node as GraphNode);
    onNodeSelect?.(node as GraphNode);
    // Centre view on node
    graphRef.current?.centerAt(node.x, node.y, 600);
    graphRef.current?.zoom(3, 600);
  }, [onNodeSelect]);

  const nodePaint = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const color = NODE_COLORS[node.type as string] ?? "#71717a";
    const r = node.type === "Concept" ? 4 : node.type === "Paper" ? 6 : 5;
    ctx.beginPath();
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
    ctx.fillStyle = selected?.id === node.id ? "#fff" : color;
    ctx.fill();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.stroke();

    if (globalScale > 2) {
      const label: string = node.label?.slice(0, 30) ?? "";
      ctx.font = `${9 / globalScale}px sans-serif`;
      ctx.fillStyle = "rgba(255,255,255,0.7)";
      ctx.textAlign = "center";
      ctx.fillText(label, node.x, node.y + r + 6 / globalScale);
    }
  }, [selected]);

  const nodeCounts = graphData.nodes.reduce<Record<string, number>>((acc, n) => {
    acc[n.type] = (acc[n.type] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="flex flex-col h-full bg-zinc-950 border-l border-zinc-800">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <span className="text-xs font-medium text-zinc-300">Knowledge Graph</span>
        <div className="flex items-center gap-1.5">
          <button
            onClick={loadGraph}
            className="p-1.5 rounded-md text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
          </button>
          <button
            onClick={() => graphRef.current?.zoom(graphRef.current.zoom() * 1.3, 300)}
            className="p-1.5 rounded-md text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
          >
            <ZoomIn size={13} />
          </button>
          <button
            onClick={() => graphRef.current?.zoom(graphRef.current.zoom() * 0.7, 300)}
            className="p-1.5 rounded-md text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
          >
            <ZoomOut size={13} />
          </button>
          <button
            onClick={() => graphRef.current?.zoomToFit(400)}
            className="p-1.5 rounded-md text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
          >
            <Maximize2 size={13} />
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="flex flex-wrap gap-1.5 px-3 py-2 border-b border-zinc-800/50">
        {Object.entries(nodeCounts).map(([type, count]) => (
          <span
            key={type}
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium"
            style={{ backgroundColor: `${NODE_COLORS[type]}20`, color: NODE_COLORS[type] }}
          >
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: NODE_COLORS[type] }} />
            {NODE_LABELS[type] ?? type}: {count}
          </span>
        ))}
        {graphData.links.length > 0 && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-zinc-800 text-zinc-400">
            {graphData.links.length} edges
          </span>
        )}
      </div>

      {/* Graph */}
      <div className="flex-1 relative">
        {loading && graphData.nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-xs text-zinc-600">Loading graph…</p>
          </div>
        )}
        {!loading && graphData.nodes.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-6">
            <p className="text-xs text-zinc-500">Knowledge graph is empty</p>
            <p className="text-[10px] text-zinc-600 mt-1">Add papers using the button in the sidebar</p>
          </div>
        )}
        {graphData.nodes.length > 0 && (
          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            nodeId="id"
            nodeCanvasObject={nodePaint}
            nodeCanvasObjectMode={() => "replace"}
            nodeStrength={-500}
            linkLength={150}
            linkColor={() => "rgba(255, 255, 255, 0.8)"}
            linkWidth={2.5}
            linkLabel={(link: any) => link.relationship || ""}
            linkLineDash={(link: any) => {
              return link.relationship === "REFERENCES" ? [5, 5] : undefined;
            }}
            backgroundColor="#09090b"
            onNodeClick={handleNodeClick}
            nodeLabel={(node: any) => `${node.type}: ${node.label}`}
            enableNodeDrag={true}
            enableZoomInteraction={true}
            enablePanInteraction={true}
            d3AlphaDecay={0.05}
            d3AlphaMin={0.0001}
            d3VelocityDecay={0.2}
            d3MaxEffectiveDistance={800}
            minZoom={0.1}
            maxZoom={20}
            warmupTicks={100}
            cooldownTicks={200}
            onEngineStop={() => console.log("✅ Graph engine stopped")}
          />
        )}
      </div>

      {/* Selected node info */}
      {selected && (
        <div className="border-t border-zinc-800 px-4 py-3">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 mb-1">
                <span
                  className="text-[10px] font-medium px-1.5 py-0.5 rounded"
                  style={{ backgroundColor: `${NODE_COLORS[selected.type]}20`, color: NODE_COLORS[selected.type] }}
                >
                  {selected.type}
                </span>
              </div>
              <p className="text-xs text-zinc-200 font-medium line-clamp-2">{selected.label}</p>
              {typeof selected.properties?.url === "string" && (
                <a
                  href={selected.properties.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[10px] text-blue-400 hover:text-blue-300 mt-0.5 block"
                >
                  Open ↗
                </a>
              )}
            </div>
            <button
              onClick={() => setSelected(null)}
              className="text-zinc-600 hover:text-zinc-400 text-xs shrink-0"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useEffect, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

const orderedNodeTypes = ['topic', 'decision', 'action', 'blocker', 'person', 'meeting'];

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  description?: string;
  source_entity_id?: string;
  metadata?: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source_node_id: string;
  target_node_id: string;
  relationship_type: string;
  weight: string;
}

interface IntelligenceGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (node: GraphNode) => void;
  onEdgeClick?: (edge: GraphEdge) => void;
  loading?: boolean;
  selectedNodeId?: string | null;
  layoutMode?: 'clustered' | 'timeline' | 'radial';
}

const nodeTypeColors: Record<string, string> = {
  decision: '#3b82f6',      // blue
  action: '#10b981',        // green
  blocker: '#ef4444',       // red
  topic: '#f59e0b',         // amber
  person: '#8b5cf6',        // purple
  meeting: '#06b6d4',       // cyan
};

const getNodeColor = (type: string): string => {
  return nodeTypeColors[type] || '#6b7280';
};

const IntelligenceGraph: React.FC<IntelligenceGraphProps> = ({
  nodes: graphNodes,
  edges: graphEdges,
  onNodeClick,
  onEdgeClick,
  loading = false,
  selectedNodeId,
  layoutMode = 'clustered',
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const layoutGraphNodes = useCallback(
    (inputNodes: GraphNode[], inputEdges: GraphEdge[]) => {
      if (!inputNodes.length) {
        return [];
      }

      const degreeMap = new Map<string, number>();
      inputEdges.forEach((edge) => {
        degreeMap.set(edge.source_node_id, (degreeMap.get(edge.source_node_id) || 0) + 1);
        degreeMap.set(edge.target_node_id, (degreeMap.get(edge.target_node_id) || 0) + 1);
      });

      if (layoutMode === 'timeline') {
        return inputNodes.map((node, idx) => ({
          id: node.id,
          data: {
            label: node.label,
            description: node.description,
            type: node.type,
          },
          position: { x: 40 + idx * 240, y: 100 + (idx % 2) * 70 },
          style: {
            background: getNodeColor(node.type),
            color: '#fff',
            border: node.id === selectedNodeId ? '3px solid #0f172a' : '2px solid rgba(15,23,42,0.18)',
            boxShadow: node.id === selectedNodeId ? '0 20px 45px rgba(15, 23, 42, 0.18)' : '0 10px 30px rgba(15, 23, 42, 0.08)',
            borderRadius: '16px',
            padding: '12px',
            fontSize: '12px',
            fontWeight: 'bold',
            minWidth: '150px',
            textAlign: 'center' as const,
            transition: 'all 220ms ease',
          },
        }));
      }

      const grouped = orderedNodeTypes.map((type) => inputNodes.filter((node) => node.type === type));
      const fallback = inputNodes.filter((node) => !orderedNodeTypes.includes(node.type));
      if (fallback.length) {
        grouped.push(fallback);
      }

      const nodesPerRow = 3;
      const clusterSpacingX = 380;
      const clusterSpacingY = 240;

      return inputNodes.map((node) => {
        const groupIndex = Math.max(0, grouped.findIndex((group) => group.some((item) => item.id === node.id)));
        const group = grouped[groupIndex] || [];
        const indexInGroup = Math.max(0, group.findIndex((item) => item.id === node.id));
        const row = Math.floor(indexInGroup / nodesPerRow);
        const col = indexInGroup % nodesPerRow;
        const clusterRow = Math.floor(groupIndex / 2);
        const clusterCol = groupIndex % 2;
        const importanceOffset = Math.min(degreeMap.get(node.id) || 0, 4) * 10;

        return {
          id: node.id,
          data: {
            label: node.label,
            description: node.description,
            type: node.type,
            count: degreeMap.get(node.id) || 0,
          },
          position: {
            x: 40 + clusterCol * clusterSpacingX + col * 190 + importanceOffset,
            y: 40 + clusterRow * clusterSpacingY + row * 150,
          },
          style: {
            background: getNodeColor(node.type),
            color: '#fff',
            border: node.id === selectedNodeId ? '3px solid #0f172a' : '2px solid rgba(15,23,42,0.18)',
            boxShadow: node.id === selectedNodeId ? '0 24px 50px rgba(15, 23, 42, 0.2)' : '0 10px 30px rgba(15, 23, 42, 0.08)',
            borderRadius: '16px',
            padding: '12px',
            fontSize: '12px',
            fontWeight: 'bold',
            minWidth: '150px',
            textAlign: 'center' as const,
            opacity: node.id === selectedNodeId ? 1 : 0.95,
            transform: node.id === selectedNodeId ? 'scale(1.02)' : 'scale(1)',
            transition: 'all 220ms ease',
          },
        };
      });
    },
    [layoutMode, selectedNodeId]
  );

  // Convert graph data to React Flow format
  useEffect(() => {
    if (graphNodes && graphNodes.length > 0) {
      const rfNodes: Node[] = layoutGraphNodes(graphNodes, graphEdges);

      setNodes(rfNodes);
    }

    if (graphEdges && graphEdges.length > 0) {
      const rfEdges: Edge[] = graphEdges.map((edge) => ({
        id: edge.id,
        source: edge.source_node_id,
        target: edge.target_node_id,
        label: edge.relationship_type,
        markerEnd: { type: MarkerType.ArrowClosed },
        data: {
          weight: edge.weight,
          relationship_type: edge.relationship_type,
        },
      }));

      setEdges(rfEdges);
    }
  }, [graphNodes, graphEdges, setNodes, setEdges, layoutGraphNodes]);

  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      const graphNode = graphNodes.find((n) => n.id === node.id);
      if (graphNode && onNodeClick) {
        onNodeClick(graphNode);
      }
    },
    [graphNodes, onNodeClick]
  );

  const handleEdgeClick = useCallback(
    (_event: React.MouseEvent, edge: Edge) => {
      const graphEdge = graphEdges.find((e) => e.id === edge.id);
      if (graphEdge && onEdgeClick) {
        onEdgeClick(graphEdge);
      }
    },
    [graphEdges, onEdgeClick]
  );

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <p className="mt-4 text-gray-600">Loading graph...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-gradient-to-br from-slate-50 via-white to-slate-100">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        onEdgeClick={handleEdgeClick}
        fitView
        minZoom={0.2}
        maxZoom={1.6}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#cbd5e1" gap={20} />
        <MiniMap
          nodeStrokeColor={(n) => getNodeColor(String(n.data?.type || 'topic'))}
          nodeColor={(n) => getNodeColor(String(n.data?.type || 'topic'))}
          maskColor="rgba(15, 23, 42, 0.08)"
          zoomable
          pannable
        />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
};

export default IntelligenceGraph;

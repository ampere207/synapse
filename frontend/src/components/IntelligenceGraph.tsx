import React, { useEffect, useCallback, useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';

const phaseOrder = ['meeting', 'topic', 'blocker', 'decision', 'action'];

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

const getDisplayType = (node: GraphNode): string => {
  const entityType = String(node.metadata?.entity_type || node.type);
  if (entityType === 'meeting_root') {
    return 'meeting';
  }

  return entityType;
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

  const adjacency = useMemo(() => {
    const connectedNodeIds = new Set<string>();
    const connectedEdgeIds = new Set<string>();

    if (selectedNodeId) {
      connectedNodeIds.add(selectedNodeId);
      graphEdges.forEach((edge) => {
        if (edge.source_node_id === selectedNodeId || edge.target_node_id === selectedNodeId) {
          connectedNodeIds.add(edge.source_node_id);
          connectedNodeIds.add(edge.target_node_id);
          connectedEdgeIds.add(edge.id);
        }
      });
    }

    return { connectedNodeIds, connectedEdgeIds };
  }, [graphEdges, selectedNodeId]);

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

      const sortedNodes = [...inputNodes].sort((left, right) => {
        const leftDisplayType = getDisplayType(left);
        const rightDisplayType = getDisplayType(right);
        const leftPhase = phaseOrder.includes(leftDisplayType) ? phaseOrder.indexOf(leftDisplayType) : phaseOrder.length;
        const rightPhase = phaseOrder.includes(rightDisplayType) ? phaseOrder.indexOf(rightDisplayType) : phaseOrder.length;
        if (leftPhase !== rightPhase) {
          return leftPhase - rightPhase;
        }

        return (degreeMap.get(right.id) || 0) - (degreeMap.get(left.id) || 0);
      });

      if (layoutMode === 'timeline') {
        return sortedNodes.map((node, idx) => ({
          id: node.id,
          data: {
            label: node.label,
            description: node.description,
            type: getDisplayType(node),
          },
          position: { x: 40 + idx * 240, y: 100 + (idx % 2) * 70 },
          style: {
            background: getNodeColor(getDisplayType(node)),
            color: '#fff',
            border: selectedNodeId === node.id ? '3px solid #0f172a' : '2px solid rgba(15,23,42,0.18)',
            boxShadow: selectedNodeId === node.id ? '0 20px 45px rgba(15, 23, 42, 0.18)' : '0 10px 30px rgba(15, 23, 42, 0.08)',
            borderRadius: '16px',
            padding: '12px',
            fontSize: '12px',
            fontWeight: 'bold',
            minWidth: '150px',
            textAlign: 'center' as const,
            transition: 'all 220ms ease',
          },
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
        }));
      }

      const groupedByDisplayType = phaseOrder.map((type) => sortedNodes.filter((node) => getDisplayType(node) === type));

      const nodesPerRow = 4;
      const clusterSpacingX = 240;
      const clusterSpacingY = 220;

      return sortedNodes.map((node) => {
        const displayType = getDisplayType(node);
        const groupIndex = Math.max(0, groupedByDisplayType.findIndex((group) => group.some((item) => item.id === node.id)));
        const group = groupedByDisplayType[groupIndex] || [];
        const indexInGroup = Math.max(0, group.findIndex((item) => item.id === node.id));
        const row = Math.floor(indexInGroup / nodesPerRow);
        const col = indexInGroup % nodesPerRow;
        const importanceOffset = Math.min(degreeMap.get(node.id) || 0, 4) * 12;

        return {
          id: node.id,
          data: {
            label: node.label,
            description: node.description,
            type: displayType,
            count: degreeMap.get(node.id) || 0,
          },
          position: {
            x: 80 + col * clusterSpacingX + importanceOffset,
            y: 60 + groupIndex * clusterSpacingY + row * 120,
          },
          style: {
            background: getNodeColor(displayType),
            color: '#fff',
            border: selectedNodeId === node.id ? '3px solid #0f172a' : '2px solid rgba(15,23,42,0.18)',
            boxShadow: selectedNodeId === node.id ? '0 24px 50px rgba(15, 23, 42, 0.2)' : '0 10px 30px rgba(15, 23, 42, 0.08)',
            borderRadius: '16px',
            padding: '12px',
            fontSize: '12px',
            fontWeight: 'bold',
            minWidth: '150px',
            textAlign: 'center' as const,
            opacity: selectedNodeId && selectedNodeId !== node.id && !adjacency.connectedNodeIds.has(node.id) ? 0.5 : 1,
            transform: selectedNodeId === node.id ? 'scale(1.03)' : 'scale(1)',
            transition: 'all 220ms ease',
          },
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
        };
      });
    },
    [layoutMode, selectedNodeId, adjacency.connectedNodeIds]
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
        markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 },
        type: 'smoothstep',
        animated: selectedNodeId ? adjacency.connectedEdgeIds.has(edge.id) : true,
        style: {
          strokeWidth: adjacency.connectedEdgeIds.has(edge.id) ? 3 : 2,
          opacity: selectedNodeId && !adjacency.connectedEdgeIds.has(edge.id) ? 0.25 : 0.9,
        },
        data: {
          weight: edge.weight,
          relationship_type: edge.relationship_type,
        },
      }));

      setEdges(rfEdges);
    }
  }, [graphNodes, graphEdges, setNodes, setEdges, layoutGraphNodes, selectedNodeId, adjacency.connectedEdgeIds]);

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
        defaultEdgeOptions={{ type: 'smoothstep', markerEnd: { type: MarkerType.ArrowClosed } }}
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

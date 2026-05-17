import { create } from "zustand";

export interface GraphNode {
  id: string;
  label: string;
  type: "topic" | "decision" | "action" | "person" | "objective";
  description?: string;
  position?: { x: number; y: number };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationshipType: string;
  weight?: "low" | "medium" | "high";
}

interface GraphStore {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNode: GraphNode | null;
  setNodes: (nodes: GraphNode[]) => void;
  setEdges: (edges: GraphEdge[]) => void;
  addNode: (node: GraphNode) => void;
  addEdge: (edge: GraphEdge) => void;
  selectNode: (node: GraphNode | null) => void;
  clearGraph: () => void;
}

export const useGraphStore = create<GraphStore>((set) => ({
  nodes: [],
  edges: [],
  selectedNode: null,
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  addNode: (node) => set((state) => ({ nodes: [...state.nodes, node] })),
  addEdge: (edge) => set((state) => ({ edges: [...state.edges, edge] })),
  selectNode: (node) => set({ selectedNode: node }),
  clearGraph: () => set({ nodes: [], edges: [], selectedNode: null }),
}));

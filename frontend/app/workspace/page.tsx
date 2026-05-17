"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { useMeetingStore } from "@/store/meeting";
import { useGraphStore } from "@/store/graph";
import type { Edge, Node } from "reactflow";
import dynamic from "next/dynamic";

const ReactFlow = dynamic(() => import("reactflow"), { ssr: false });
import "reactflow/dist/style.css";

export default function WorkspacePage() {
  const router = useRouter();
  const { isAuthenticated, loadFromStorage } = useAuthStore();
  const { transcriptChunks } = useMeetingStore();
  const { nodes, edges } = useGraphStore();
  const [loading, setLoading] = useState(true);

  const flowNodes: Node[] = nodes.map((node) => ({
    id: node.id,
    type: "default",
    data: { label: node.label },
    position: node.position ?? { x: 0, y: 0 },
  }));

  const flowEdges: Edge[] = edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    label: edge.relationshipType,
  }));

  useEffect(() => {
    loadFromStorage();
    setLoading(false);
  }, [loadFromStorage]);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/auth/login");
    }
  }, [isAuthenticated, loading, router]);

  if (loading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-slate-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-slate-900">Live Meeting</h1>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => {
                useAuthStore.getState().logout();
                router.push("/auth/login");
              }}
              className="px-4 py-2 text-slate-700 hover:bg-slate-100 rounded-lg transition"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left panel - Transcript */}
        <div className="w-1/3 border-r border-slate-200 flex flex-col bg-white">
          <div className="p-4 border-b border-slate-200">
            <h2 className="font-semibold text-slate-900">Transcript</h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {transcriptChunks.map((chunk) => (
              <div key={chunk.id} className="text-sm">
                <div className="font-medium text-slate-900">{chunk.speaker || "Unknown"}</div>
                <div className="text-slate-600">{chunk.text}</div>
              </div>
            ))}
            {transcriptChunks.length === 0 && (
              <div className="text-slate-400 text-sm">Waiting for transcript...</div>
            )}
          </div>
        </div>

        {/* Center panel - Graph visualization */}
        <div className="w-1/3 flex flex-col bg-slate-50">
          <div className="p-4 border-b border-slate-200">
            <h2 className="font-semibold text-slate-900">Intelligence Graph</h2>
          </div>
          <div className="flex-1">
            <ReactFlow nodes={flowNodes} edges={flowEdges}>
              <div className="text-slate-400 text-sm flex items-center justify-center h-full">
                {flowNodes.length === 0 ? "Graph will appear here" : ""}
              </div>
            </ReactFlow>
          </div>
        </div>

        {/* Right panel - Decisions & Actions */}
        <div className="w-1/3 border-l border-slate-200 flex flex-col bg-white">
          <div className="p-4 border-b border-slate-200 space-y-2">
            <h2 className="font-semibold text-slate-900">Decisions & Actions</h2>
            <p className="text-xs text-slate-500">AI-extracted from meeting</p>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <div className="text-slate-400 text-sm">
              Decisions and action items will appear here as they&apos;re extracted
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

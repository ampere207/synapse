import React, { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { useParams } from 'next/navigation';
import { useWebSocket } from '@/lib/websocket';
import IntelligenceGraph, { GraphNode, GraphEdge } from '@/components/IntelligenceGraph';
import IntelligenceEntities, { IntelligenceEntity } from '@/components/IntelligenceEntities';
import ExecutionDashboard from '@/components/ExecutionDashboard';
import IntelligenceSearch, { IntelligenceSearchResult } from '@/components/IntelligenceSearch';
import IntelligenceTimeline, { IntelligenceTimelineEvent } from '@/components/IntelligenceTimeline';
import GraphContextPanel from '@/components/GraphContextPanel';
import { Zap, Layers3, MessageSquareText, Clock3, Grid2X2, Activity } from 'lucide-react';

type TabType = 'graph' | 'discover' | 'timeline' | 'entities' | 'execution' | 'segments';
type LayoutMode = 'clustered' | 'timeline';

type ExecutionStatus = 'pending' | 'in_progress' | 'completed' | 'blocked' | 'overdue';

interface ExecutionState {
  execution_id: string;
  entity_id: string;
  status: ExecutionStatus;
  progress_percent: number;
  due_date?: string;
  completed_date?: string;
  depends_on?: string[];
  blocking?: string[];
  recurring?: boolean;
  recurrence_pattern?: string;
}

interface ExecutionSummary {
  total_executions: number;
  pending: number;
  in_progress: number;
  completed: number;
  blocked: number;
  overdue: number;
  critical_items?: Array<{
    execution_id: string;
    entity_title: string;
    status: string;
    reason: string;
    blocking_ids?: string[];
  }>;
}

interface NodeContextData {
  node: {
    id: string;
    type: string;
    label: string;
    description?: string | null;
    source_entity_id?: string | null;
    metadata?: Record<string, any> | null;
  };
  source_entity?: {
    id: string;
    entity_type: string;
    title: string;
    description?: string | null;
    status?: string | null;
    confidence_score?: number | null;
    assigned_to?: string | null;
    due_date?: string | null;
    priority?: string | null;
  } | null;
  execution_state?: {
    execution_id: string;
    status: string;
    progress_percent?: number | null;
    due_date?: string | null;
    blocking_ids?: string[];
    depends_on_ids?: string[];
    recurring?: boolean;
    recurrence_pattern?: string | null;
  } | null;
  related_nodes?: Array<{
    id: string;
    type: string;
    label: string;
    description?: string | null;
  }>;
  linked_edges?: Array<{
    id: string;
    source_node_id: string;
    target_node_id: string;
    relationship_type: string;
    weight: string;
  }>;
  transcript_references?: Array<{
    meeting_id?: string | null;
    entity_id?: string | null;
    speaker?: string | null;
    timestamp?: number | null;
    description?: string | null;
  }>;
}

const IntelligencePage: React.FC = () => {
  const params = useParams();
  const organizationId = params.organizationId as string;
  const meetingId = params.meetingId as string;

  const [token, setToken] = useState<string | null>(null);
  const [tab, setTab] = useState<TabType>('graph');
  const [layoutMode, setLayoutMode] = useState<LayoutMode>('clustered');
  const [loading, setLoading] = useState(false);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [entities, setEntities] = useState<IntelligenceEntity[]>([]);
  const [executionSummary, setExecutionSummary] = useState<ExecutionSummary | null>(null);
  const [executions, setExecutions] = useState<ExecutionState[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<IntelligenceEntity | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [nodeContext, setNodeContext] = useState<NodeContextData | null>(null);
  const [segments, setSegments] = useState<any[]>([]);
  const [timelineEvents, setTimelineEvents] = useState<IntelligenceTimelineEvent[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<IntelligenceSearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [contextLoading, setContextLoading] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setToken(localStorage.getItem('token'));
    }
  }, []);

  const fetchGraphData = useCallback(async () => {
    if (!token) return;
    try {
      setLoading(true);
      const [nodesRes, edgesRes] = await Promise.all([
        axios.get(`${API_BASE}/api/graph/nodes`, {
          params: { meeting_id: meetingId },
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API_BASE}/api/graph/edges`, {
          params: { meeting_id: meetingId },
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);
      setNodes(nodesRes.data);
      setEdges(edgesRes.data);
    } catch (error) {
      console.error('Error fetching graph data:', error);
    } finally {
      setLoading(false);
    }
  }, [token, meetingId, API_BASE]);

  const fetchEntities = useCallback(async () => {
    if (!token) return;
    try {
      setLoading(true);
      const res = await axios.get(`${API_BASE}/api/extraction/entities`, {
        params: { meeting_id: meetingId },
        headers: { Authorization: `Bearer ${token}` },
      });
      setEntities(res.data);
    } catch (error) {
      console.error('Error fetching entities:', error);
    } finally {
      setLoading(false);
    }
  }, [token, meetingId, API_BASE]);

  const fetchExecutionSummary = useCallback(async () => {
    if (!token) return;
    try {
      setLoading(true);
      const [summaryRes, executionResults] = await Promise.all([
        axios.get(`${API_BASE}/api/execution/summary/${organizationId}`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        Promise.all(
          entities.map((entity) =>
            axios.get(`${API_BASE}/api/execution/status/${entity.id}`, {
              headers: { Authorization: `Bearer ${token}` },
            }).then((response) => response.data as ExecutionState).catch(() => null)
          )
        ),
      ]);

      setExecutionSummary(summaryRes.data);
      setExecutions(executionResults.filter(Boolean) as ExecutionState[]);
    } catch (error) {
      console.error('Error fetching execution summary:', error);
    } finally {
      setLoading(false);
    }
  }, [token, organizationId, entities, API_BASE]);

  const fetchSegmentation = useCallback(async () => {
    if (!token) return;
    try {
      setLoading(true);
      const res = await axios.post(
        `${API_BASE}/api/segmentation/segment-transcript`,
        {},
        {
          params: { meeting_id: meetingId },
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setSegments(res.data.segments || []);
    } catch (error) {
      console.error('Error fetching segmentation:', error);
    } finally {
      setLoading(false);
    }
  }, [token, meetingId, API_BASE]);

  const fetchTimeline = useCallback(async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${API_BASE}/api/intelligence/timeline`, {
        params: { organization_id: organizationId, meeting_id: meetingId, limit: 50 },
        headers: { Authorization: `Bearer ${token}` },
      });
      setTimelineEvents(res.data.events || []);
    } catch (error) {
      console.error('Error fetching timeline:', error);
    }
  }, [token, organizationId, meetingId, API_BASE]);

  const fetchNodeContext = useCallback(
    async (nodeId: string) => {
      if (!token) return;
      try {
        setContextLoading(true);
        const res = await axios.get(`${API_BASE}/api/intelligence/context/${nodeId}`, {
          params: { meeting_id: meetingId, organization_id: organizationId },
          headers: { Authorization: `Bearer ${token}` },
        });
        setNodeContext(res.data);
      } catch (error) {
        console.error('Error fetching node context:', error);
      } finally {
        setContextLoading(false);
      }
    },
    [token, organizationId, meetingId, API_BASE]
  );

  const runSearch = useCallback(async () => {
    if (!token || !searchQuery.trim()) return;
    try {
      setSearchLoading(true);
      const res = await axios.get(`${API_BASE}/api/intelligence/search`, {
        params: { organization_id: organizationId, meeting_id: meetingId, query: searchQuery, limit: 12 },
        headers: { Authorization: `Bearer ${token}` },
      });
      setSearchResults((res.data.results || []) as IntelligenceSearchResult[]);
    } catch (error) {
      console.error('Error searching intelligence:', error);
    } finally {
      setSearchLoading(false);
    }
  }, [token, searchQuery, organizationId, meetingId, API_BASE]);

  const triggerExtraction = useCallback(async () => {
    if (!token) return;
    try {
      setLoading(true);
      await axios.post(
        `${API_BASE}/api/extraction/extract-meeting`,
        {},
        {
          params: { meeting_id: meetingId },
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setTimeout(() => {
        fetchEntities();
        fetchGraphData();
        fetchTimeline();
      }, 2000);
    } catch (error) {
      console.error('Error triggering extraction:', error);
    } finally {
      setLoading(false);
    }
  }, [token, meetingId, API_BASE, fetchEntities, fetchGraphData, fetchTimeline]);

  const handleSocketMessage = useCallback(
    (message: { type: string; [key: string]: any }) => {
      if (message.type === 'graph_mutation') {
        fetchGraphData();
        fetchTimeline();
      }
      if (message.type === 'entity_extracted') {
        fetchEntities();
        fetchExecutionSummary();
        fetchTimeline();
      }
      if (message.type === 'execution_status_update') {
        fetchExecutionSummary();
        fetchTimeline();
      }
    },
    [fetchGraphData, fetchEntities, fetchExecutionSummary, fetchTimeline]
  );

  useWebSocket(organizationId, meetingId, token || '', handleSocketMessage);

  useEffect(() => {
    if (tab === 'graph') {
      fetchGraphData();
      fetchTimeline();
    }
    if (tab === 'entities') {
      fetchEntities();
    }
    if (tab === 'execution') {
      fetchExecutionSummary();
    }
    if (tab === 'segments') {
      fetchSegmentation();
    }
    if (tab === 'timeline') {
      fetchTimeline();
    }
  }, [tab, fetchGraphData, fetchEntities, fetchExecutionSummary, fetchSegmentation, fetchTimeline]);

  useEffect(() => {
    if (selectedNodeId) {
      fetchNodeContext(selectedNodeId);
    }
  }, [selectedNodeId, fetchNodeContext]);

  const selectedNode = useMemo(
    () => nodes.find((node) => node.id === selectedNodeId) || null,
    [nodes, selectedNodeId]
  );

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(15,23,42,0.06),_transparent_35%),linear-gradient(180deg,_#f8fafc_0%,_#ffffff_35%,_#f8fafc_100%)] text-slate-900">
      <div className="border-b border-slate-200/70 bg-white/80 backdrop-blur-xl">
        <div className="mx-auto max-w-[1600px] px-4 py-4 lg:px-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-lg shadow-slate-900/20">
                <Zap size={22} />
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">
                  Operational Intelligence Workspace
                </p>
                <h1 className="text-xl font-semibold text-slate-950 lg:text-2xl">
                  {meetingId?.slice(0, 8)} · {organizationId?.slice(0, 8)}
                </h1>
                <p className="text-sm text-slate-500">
                  Live graph evolution, organizational memory, and execution continuity.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={triggerExtraction}
                className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={loading}
              >
                {loading ? 'Refreshing intelligence...' : 'Extract Intelligence'}
              </button>
              <div className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-500 shadow-sm">
                WebSocket live feed
              </div>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {([['graph', 'Graph'], ['discover', 'Discover'], ['timeline', 'Timeline'], ['entities', 'Entities'], ['execution', 'Execution'], ['segments', 'Segments']] as const).map(([key, label]) => (
              <button
                key={key}
                type="button"
                onClick={() => setTab(key)}
                className={`rounded-xl px-4 py-2 text-sm font-medium transition ${
                  tab === key
                    ? 'bg-slate-900 text-white shadow-lg shadow-slate-900/15'
                    : 'bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-[1600px] px-4 py-5 lg:px-6">
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1.8fr)_minmax(360px,0.8fr)]">
          <div className="space-y-5">
            {tab === 'graph' && (
              <div className="overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-sm">
                <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
                  <div>
                    <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Graph Intelligence Explorer</h2>
                    <p className="mt-1 text-sm text-slate-600">Clustered relationships with live mutation awareness.</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setLayoutMode('clustered')}
                      className={`rounded-lg px-3 py-2 text-xs font-medium transition ${layoutMode === 'clustered' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'}`}
                    >
                      Clustered
                    </button>
                    <button
                      type="button"
                      onClick={() => setLayoutMode('timeline')}
                      className={`rounded-lg px-3 py-2 text-xs font-medium transition ${layoutMode === 'timeline' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'}`}
                    >
                      Timeline
                    </button>
                  </div>
                </div>
                <div className="h-[760px]">
                  <IntelligenceGraph
                    nodes={nodes}
                    edges={edges}
                    loading={loading}
                    selectedNodeId={selectedNodeId}
                    layoutMode={layoutMode}
                    onNodeClick={(node) => {
                      setSelectedNodeId(node.id);
                      const entity = entities.find((entityItem) => entityItem.id === node.source_entity_id);
                      if (entity) {
                        setSelectedEntity(entity);
                      }
                    }}
                  />
                </div>
              </div>
            )}

            {tab === 'discover' && (
              <div className="space-y-5">
                <IntelligenceSearch
                  query={searchQuery}
                  onQueryChange={setSearchQuery}
                  onSearch={runSearch}
                  results={searchResults}
                  loading={searchLoading}
                  onSelectResult={(result) => {
                    if (result.kind === 'entity') {
                      const entity = entities.find((item) => item.id === result.id);
                      if (entity) {
                        setSelectedEntity(entity);
                      }
                    }
                  }}
                />

                <div className="grid gap-4 lg:grid-cols-3">
                  <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                    <div className="flex items-center gap-2 text-slate-500">
                      <Grid2X2 size={16} />
                      <span className="text-xs font-semibold uppercase tracking-[0.18em]">Graph Nodes</span>
                    </div>
                    <p className="mt-3 text-2xl font-semibold text-slate-950">{nodes.length}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                    <div className="flex items-center gap-2 text-slate-500">
                      <MessageSquareText size={16} />
                      <span className="text-xs font-semibold uppercase tracking-[0.18em]">Entities</span>
                    </div>
                    <p className="mt-3 text-2xl font-semibold text-slate-950">{entities.length}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                    <div className="flex items-center gap-2 text-slate-500">
                      <Activity size={16} />
                      <span className="text-xs font-semibold uppercase tracking-[0.18em]">Execution Items</span>
                    </div>
                    <p className="mt-3 text-2xl font-semibold text-slate-950">{executions.length}</p>
                  </div>
                </div>
              </div>
            )}

            {tab === 'timeline' && (
              <IntelligenceTimeline
                events={timelineEvents}
                loading={loading}
                onEventClick={(event) => {
                  if (event.entity_id) {
                    const entity = entities.find((item) => item.id === event.entity_id);
                    if (entity) {
                      setSelectedEntity(entity);
                    }
                  }
                }}
              />
            )}

            {tab === 'entities' && (
              <IntelligenceEntities
                entities={entities}
                loading={loading}
                onEntityClick={setSelectedEntity}
              />
            )}

            {tab === 'execution' && executionSummary && (
              <ExecutionDashboard
                summary={executionSummary}
                executions={executions}
                loading={loading}
              />
            )}

            {tab === 'segments' && (
              <div className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Semantic Segmentation</h2>
                    <p className="mt-1 text-sm text-slate-600">Topic windows that feed extraction and graph clustering.</p>
                  </div>
                  <Layers3 className="text-slate-400" size={18} />
                </div>
                <div className="mt-4 space-y-3">
                  {segments.length === 0 ? (
                    <div className="py-8 text-sm text-slate-500">No segments extracted yet.</div>
                  ) : (
                    segments.map((segment, index) => (
                      <div key={`${segment.topic_id}-${index}`} className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4">
                        <div className="flex items-center justify-between gap-4">
                          <h3 className="text-sm font-semibold text-slate-900">Topic {segment.topic_id}</h3>
                          <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-600">
                            {segment.chunk_count} chunks
                          </span>
                        </div>
                        <p className="mt-2 text-sm text-slate-600">{segment.summary}</p>
                        <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
                          <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1">Cluster {segment.cluster_id}</span>
                          <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1">Speakers: {segment.speakers?.join(', ') || 'Unknown'}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-5 xl:sticky xl:top-5 xl:self-start">
            <GraphContextPanel
              loading={contextLoading}
              node={nodeContext?.node || selectedNode}
              sourceEntity={nodeContext?.source_entity || selectedEntity || null}
              executionState={nodeContext?.execution_state || null}
              relatedNodes={nodeContext?.related_nodes || []}
              linkedEdges={nodeContext?.linked_edges || []}
              transcriptReferences={nodeContext?.transcript_references || []}
            />

            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Live Status</h2>
                  <p className="mt-1 text-sm text-slate-600">Realtime feed, extraction, and execution readiness.</p>
                </div>
                <Clock3 className="text-slate-400" size={18} />
              </div>
              <div className="mt-4 space-y-3 text-sm text-slate-600">
                <div className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
                  <span>WebSocket</span>
                  <span className="font-medium text-slate-900">Live</span>
                </div>
                <div className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
                  <span>Graph mutations</span>
                  <span className="font-medium text-slate-900">{edges.length} edges tracked</span>
                </div>
                <div className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
                  <span>Selected node</span>
                  <span className="font-medium text-slate-900">{selectedNode?.label || 'None'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntelligencePage;
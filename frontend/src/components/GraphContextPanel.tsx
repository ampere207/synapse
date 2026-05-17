import React from 'react';
import { BookOpen, Link2, Clock3, Users, CheckCircle2 } from 'lucide-react';

interface GraphContextPanelProps {
  loading?: boolean;
  node?: {
    id: string;
    type: string;
    label: string;
    description?: string | null;
    source_entity_id?: string | null;
    metadata?: Record<string, any> | null;
  } | null;
  sourceEntity?: {
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
  executionState?: {
    execution_id: string;
    status: string;
    progress_percent?: number | null;
    due_date?: string | null;
    blocking_ids?: string[];
    depends_on_ids?: string[];
    recurring?: boolean;
    recurrence_pattern?: string | null;
  } | null;
  relatedNodes?: Array<{
    id: string;
    type: string;
    label: string;
    description?: string | null;
  }>;
  linkedEdges?: Array<{
    id: string;
    source_node_id: string;
    target_node_id: string;
    relationship_type: string;
    weight: string;
  }>;
  transcriptReferences?: Array<{
    meeting_id?: string | null;
    entity_id?: string | null;
    speaker?: string | null;
    timestamp?: number | null;
    description?: string | null;
  }>;
}

const pill = 'rounded-full border px-2.5 py-1 text-[11px] font-medium';

const GraphContextPanel: React.FC<GraphContextPanelProps> = ({
  loading = false,
  node,
  sourceEntity,
  executionState,
  relatedNodes = [],
  linkedEdges = [],
  transcriptReferences = [],
}) => {
  return (
    <aside className="rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-5 py-4">
        <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
          Context Panel
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          Expandable context for the selected intelligence node.
        </p>
      </div>

      <div className="space-y-5 px-5 py-4">
        {loading ? (
          <div className="py-8 text-sm text-slate-500">Loading context...</div>
        ) : node ? (
          <>
            <div>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">Selected Node</p>
                  <h3 className="mt-2 text-lg font-semibold text-slate-900">{node.label}</h3>
                </div>
                <span className={`${pill} border-slate-200 bg-slate-50 text-slate-600 capitalize`}>
                  {node.type}
                </span>
              </div>
              {node.description && <p className="mt-3 text-sm leading-6 text-slate-600">{node.description}</p>}
            </div>

            {sourceEntity && (
              <section className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4">
                <div className="flex items-center gap-2 text-slate-500">
                  <BookOpen size={16} />
                  <span className="text-xs font-semibold uppercase tracking-[0.18em]">Source Entity</span>
                </div>
                <h4 className="mt-3 text-base font-semibold text-slate-900">{sourceEntity.title}</h4>
                {sourceEntity.description && <p className="mt-2 text-sm leading-6 text-slate-600">{sourceEntity.description}</p>}
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className={`${pill} border-slate-200 bg-white text-slate-700 capitalize`}>{sourceEntity.entity_type}</span>
                  {sourceEntity.status && <span className={`${pill} border-amber-200 bg-amber-50 text-amber-700 capitalize`}>{sourceEntity.status}</span>}
                  {sourceEntity.priority && <span className={`${pill} border-rose-200 bg-rose-50 text-rose-700 capitalize`}>{sourceEntity.priority}</span>}
                  {sourceEntity.assigned_to && <span className={`${pill} border-slate-200 bg-white text-slate-700`}>{sourceEntity.assigned_to}</span>}
                </div>
              </section>
            )}

            {executionState && (
              <section className="rounded-2xl border border-slate-100 p-4">
                <div className="flex items-center gap-2 text-slate-500">
                  <CheckCircle2 size={16} />
                  <span className="text-xs font-semibold uppercase tracking-[0.18em]">Execution Continuity</span>
                </div>
                <div className="mt-3 flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-slate-900 capitalize">{executionState.status}</p>
                    <p className="text-xs text-slate-500">
                      {executionState.progress_percent ?? 0}% complete
                    </p>
                  </div>
                  <div className="h-2 w-32 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-slate-900 transition-all"
                      style={{ width: `${executionState.progress_percent ?? 0}%` }}
                    />
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
                  {executionState.recurring && <span className={`${pill} border-sky-200 bg-sky-50 text-sky-700`}>Recurring</span>}
                  {executionState.recurrence_pattern && <span className={`${pill} border-slate-200 bg-white text-slate-600`}>{executionState.recurrence_pattern}</span>}
                  {executionState.due_date && <span className={`${pill} border-slate-200 bg-white text-slate-600`}>{new Date(executionState.due_date).toLocaleDateString()}</span>}
                </div>
              </section>
            )}

            <section>
              <div className="flex items-center gap-2 text-slate-500">
                <Link2 size={16} />
                <span className="text-xs font-semibold uppercase tracking-[0.18em]">Linked Relationships</span>
              </div>
              <div className="mt-3 space-y-2">
                {linkedEdges.length === 0 ? (
                  <p className="text-sm text-slate-500">No linked graph relationships.</p>
                ) : (
                  linkedEdges.map((edge) => (
                    <div key={edge.id} className="rounded-2xl border border-slate-100 px-3 py-2 text-sm text-slate-700">
                      <span className="font-medium capitalize">{edge.relationship_type.replace(/_/g, ' ')}</span>
                      <span className="text-slate-400"> · {edge.weight}</span>
                    </div>
                  ))
                )}
              </div>
            </section>

            <section>
              <div className="flex items-center gap-2 text-slate-500">
                <Users size={16} />
                <span className="text-xs font-semibold uppercase tracking-[0.18em]">Related Nodes</span>
              </div>
              <div className="mt-3 space-y-2">
                {relatedNodes.length === 0 ? (
                  <p className="text-sm text-slate-500">No nearby nodes.</p>
                ) : (
                  relatedNodes.map((relatedNode) => (
                    <div key={relatedNode.id} className="rounded-2xl border border-slate-100 px-3 py-2">
                      <p className="text-sm font-medium text-slate-900">{relatedNode.label}</p>
                      <p className="text-xs capitalize text-slate-500">{relatedNode.type}</p>
                    </div>
                  ))
                )}
              </div>
            </section>

            <section>
              <div className="flex items-center gap-2 text-slate-500">
                <Clock3 size={16} />
                <span className="text-xs font-semibold uppercase tracking-[0.18em]">Transcript References</span>
              </div>
              <div className="mt-3 space-y-2">
                {transcriptReferences.length === 0 ? (
                  <p className="text-sm text-slate-500">No transcript references available yet.</p>
                ) : (
                  transcriptReferences.map((reference, index) => (
                    <div key={`${reference.entity_id ?? 'ref'}-${index}`} className="rounded-2xl border border-slate-100 px-3 py-2 text-sm text-slate-700">
                      {reference.speaker && <p className="font-medium text-slate-900">{reference.speaker}</p>}
                      <p className="text-xs text-slate-500">
                        {reference.timestamp != null ? `${Math.round(reference.timestamp)}s` : 'No timestamp'}
                      </p>
                      {reference.description && <p className="mt-1 text-xs leading-5 text-slate-500">{reference.description}</p>}
                    </div>
                  ))
                )}
              </div>
            </section>
          </>
        ) : (
          <div className="py-8 text-sm text-slate-500">Select a node to inspect its context.</div>
        )}
      </div>
    </aside>
  );
};

export default GraphContextPanel;
import React from 'react';
import { ArrowUpRight, Clock3 } from 'lucide-react';

export interface IntelligenceTimelineEvent {
  id: string;
  event_type: string;
  title: string;
  description?: string | null;
  timestamp: string;
  meeting_id?: string | null;
  entity_id?: string | null;
  status?: string | null;
  sequence_number?: number | null;
}

interface IntelligenceTimelineProps {
  events: IntelligenceTimelineEvent[];
  loading?: boolean;
  onEventClick?: (event: IntelligenceTimelineEvent) => void;
}

const typeTone: Record<string, string> = {
  execution_update: 'bg-amber-50 text-amber-700 border-amber-200',
  graph_node_added: 'bg-sky-50 text-sky-700 border-sky-200',
  graph_node_updated: 'bg-sky-50 text-sky-700 border-sky-200',
  graph_edge_added: 'bg-violet-50 text-violet-700 border-violet-200',
  entity_decision: 'bg-blue-50 text-blue-700 border-blue-200',
  entity_action: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  entity_blocker: 'bg-rose-50 text-rose-700 border-rose-200',
  entity_topic: 'bg-amber-50 text-amber-700 border-amber-200',
};

const IntelligenceTimeline: React.FC<IntelligenceTimelineProps> = ({
  events,
  loading = false,
  onEventClick,
}) => {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Intelligence Timeline
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Decisions, blockers, execution drift, and graph mutations over time.
          </p>
        </div>
        <Clock3 className="text-slate-400" size={18} />
      </div>

      <div className="max-h-[28rem] overflow-auto px-5 py-4">
        {loading ? (
          <div className="py-10 text-center text-sm text-slate-500">Loading timeline...</div>
        ) : events.length === 0 ? (
          <div className="py-10 text-center text-sm text-slate-500">No timeline events yet.</div>
        ) : (
          <div className="space-y-3">
            {events.map((event) => (
              <button
                key={`${event.id}-${event.timestamp}`}
                type="button"
                onClick={() => onEventClick?.(event)}
                className="group flex w-full items-start gap-4 rounded-2xl border border-slate-100 bg-slate-50/60 px-4 py-3 text-left transition hover:border-slate-200 hover:bg-white"
              >
                <div className={`mt-0.5 rounded-full border px-2.5 py-1 text-[11px] font-medium ${typeTone[event.event_type] || 'bg-slate-100 text-slate-700 border-slate-200'}`}>
                  {event.event_type.replace(/_/g, ' ')}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-4">
                    <h3 className="truncate text-sm font-semibold text-slate-900">
                      {event.title}
                    </h3>
                    <span className="shrink-0 text-xs text-slate-500">
                      {new Date(event.timestamp).toLocaleString()}
                    </span>
                  </div>
                  {event.description && (
                    <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-600">
                      {event.description}
                    </p>
                  )}
                  <div className="mt-2 flex items-center gap-3 text-[11px] text-slate-500">
                    {event.meeting_id && <span>Meeting {event.meeting_id.slice(0, 8)}</span>}
                    {event.status && <span className="capitalize">{event.status}</span>}
                  </div>
                </div>
                <ArrowUpRight size={14} className="mt-1 text-slate-400 opacity-0 transition group-hover:opacity-100" />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default IntelligenceTimeline;
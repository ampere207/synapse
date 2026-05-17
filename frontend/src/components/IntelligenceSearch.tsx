import React from 'react';
import { Search, Sparkles } from 'lucide-react';

export interface IntelligenceSearchResult {
  kind: 'entity' | 'meeting' | 'memory' | 'semantic_memory';
  id: string;
  title: string;
  description?: string | null;
  score: number;
  meeting_title?: string | null;
  meeting_id?: string | null;
  entity_type?: string | null;
  status?: string | null;
  memory_type?: string | null;
}

interface IntelligenceSearchProps {
  query: string;
  onQueryChange: (query: string) => void;
  onSearch: () => void;
  results: IntelligenceSearchResult[];
  loading?: boolean;
  onSelectResult?: (result: IntelligenceSearchResult) => void;
}

const kindLabels: Record<IntelligenceSearchResult['kind'], string> = {
  entity: 'Entity',
  meeting: 'Meeting',
  memory: 'Memory',
  semantic_memory: 'Semantic',
};

const IntelligenceSearch: React.FC<IntelligenceSearchProps> = ({
  query,
  onQueryChange,
  onSearch,
  results,
  loading = false,
  onSelectResult,
}) => {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center gap-3 border-b border-slate-100 px-4 py-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-white">
          <Sparkles size={18} />
        </div>
        <div className="flex-1">
          <label className="sr-only" htmlFor="intelligence-search">
            Search organizational intelligence
          </label>
          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 focus-within:border-slate-400">
            <Search size={16} className="text-slate-400" />
            <input
              id="intelligence-search"
              value={query}
              onChange={(event) => onQueryChange(event.target.value)}
              onKeyDown={(event) => event.key === 'Enter' && onSearch()}
              placeholder="Search decisions, blockers, people, meetings, actions..."
              className="w-full bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400"
            />
          </div>
        </div>
        <button
          type="button"
          onClick={onSearch}
          disabled={loading}
          className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? 'Searching' : 'Search'}
        </button>
      </div>

      <div className="max-h-[28rem] overflow-auto px-2 py-2">
        {results.length === 0 ? (
          <div className="px-4 py-10 text-center text-sm text-slate-500">
            Search results will appear here.
          </div>
        ) : (
          <div className="space-y-2">
            {results.map((result) => (
              <button
                key={`${result.kind}-${result.id}`}
                type="button"
                onClick={() => onSelectResult?.(result)}
                className="w-full rounded-2xl border border-transparent px-4 py-3 text-left transition hover:border-slate-200 hover:bg-slate-50"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-slate-900 px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide text-white">
                        {kindLabels[result.kind]}
                      </span>
                      <span className="text-xs text-slate-500">{Math.round(result.score * 100)} relevance</span>
                    </div>
                    <h3 className="mt-2 text-sm font-semibold text-slate-900">
                      {result.title}
                    </h3>
                    {result.description && (
                      <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-600">
                        {result.description}
                      </p>
                    )}
                  </div>
                  <div className="text-right text-xs text-slate-500">
                    {result.meeting_title && <div>{result.meeting_title}</div>}
                    {result.entity_type && <div className="capitalize">{result.entity_type}</div>}
                    {result.status && <div className="capitalize">{result.status}</div>}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default IntelligenceSearch;
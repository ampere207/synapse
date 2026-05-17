import React, { useState } from 'react';
import { ChevronDown, ChevronUp, AlertCircle, CheckCircle, Clock, Users } from 'lucide-react';

export interface IntelligenceEntity {
  id: string;
  entity_type: 'decision' | 'action' | 'blocker' | 'topic';
  title: string;
  description: string;
  confidence_score?: number;
  status?: string;
  assigned_to?: string;
  due_date?: string;
  priority?: string;
}

interface IntelligenceEntitiesProps {
  entities: IntelligenceEntity[];
  loading?: boolean;
  onEntityClick?: (entity: IntelligenceEntity) => void;
}

const entityIcons: Record<string, React.ReactNode> = {
  decision: '✓',
  action: '→',
  blocker: '⚠',
  topic: '#',
};

const entityColors: Record<string, { bg: string; text: string; border: string }> = {
  decision: {
    bg: 'bg-blue-50',
    text: 'text-blue-900',
    border: 'border-blue-200',
  },
  action: {
    bg: 'bg-green-50',
    text: 'text-green-900',
    border: 'border-green-200',
  },
  blocker: {
    bg: 'bg-red-50',
    text: 'text-red-900',
    border: 'border-red-200',
  },
  topic: {
    bg: 'bg-amber-50',
    text: 'text-amber-900',
    border: 'border-amber-200',
  },
};

const EntityCard: React.FC<{
  entity: IntelligenceEntity;
  onClick?: () => void;
}> = ({ entity, onClick }) => {
  const [expanded, setExpanded] = useState(false);
  const colors = entityColors[entity.entity_type] || entityColors.decision;

  return (
    <div
      className={`${colors.bg} ${colors.border} border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md`}
      onClick={onClick}
    >
      <div
        className="flex items-start justify-between"
        onClick={(e) => {
          e.stopPropagation();
          setExpanded(!expanded);
        }}
      >
        <div className="flex items-start gap-3 flex-1">
          <div className={`${colors.text} font-bold text-lg`}>
            {entityIcons[entity.entity_type]}
          </div>
          <div className="flex-1">
            <h3 className={`${colors.text} font-semibold text-sm`}>
              {entity.title}
            </h3>
            <p className={`${colors.text} text-xs opacity-75 mt-1`}>
              {entity.entity_type.toUpperCase()}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {entity.confidence_score !== undefined && (
            <div className="text-xs font-medium">
              {Math.round(entity.confidence_score * 100)}%
            </div>
          )}
          {expanded ? (
            <ChevronUp size={18} />
          ) : (
            <ChevronDown size={18} />
          )}
        </div>
      </div>

      {expanded && (
        <div className="mt-4 border-t border-opacity-20 pt-4">
          <p className={`${colors.text} text-sm mb-3`}>{entity.description}</p>

          <div className="flex flex-wrap gap-2">
            {entity.status && (
              <div className="inline-flex items-center gap-1 text-xs bg-white px-2 py-1 rounded">
                <CheckCircle size={14} />
                <span>{entity.status}</span>
              </div>
            )}

            {entity.priority && (
              <div className="inline-flex items-center gap-1 text-xs bg-white px-2 py-1 rounded">
                <AlertCircle size={14} />
                <span>{entity.priority}</span>
              </div>
            )}

            {entity.assigned_to && (
              <div className="inline-flex items-center gap-1 text-xs bg-white px-2 py-1 rounded">
                <Users size={14} />
                <span>{entity.assigned_to}</span>
              </div>
            )}

            {entity.due_date && (
              <div className="inline-flex items-center gap-1 text-xs bg-white px-2 py-1 rounded">
                <Clock size={14} />
                <span>{new Date(entity.due_date).toLocaleDateString()}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const IntelligenceEntities: React.FC<IntelligenceEntitiesProps> = ({
  entities,
  loading = false,
  onEntityClick,
}) => {
  const [filter, setFilter] = useState<string | null>(null);

  const filtered =
    filter && filter !== 'all'
      ? entities.filter((e) => e.entity_type === filter)
      : entities;

  const grouped = {
    decision: filtered.filter((e) => e.entity_type === 'decision'),
    action: filtered.filter((e) => e.entity_type === 'action'),
    blocker: filtered.filter((e) => e.entity_type === 'blocker'),
    topic: filtered.filter((e) => e.entity_type === 'topic'),
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="mt-2 text-gray-600 text-sm">Loading entities...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filter buttons */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setFilter(null)}
          className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
            filter === null
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          All
        </button>
        {['decision', 'action', 'blocker', 'topic'].map((type) => (
          <button
            key={type}
            onClick={() => setFilter(type)}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              filter === type
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {type.charAt(0).toUpperCase() + type.slice(1)} ({grouped[type as keyof typeof grouped].length})
          </button>
        ))}
      </div>

      {/* Entity groups */}
      <div className="space-y-6">
        {Object.entries(grouped).map(([type, items]) => {
          if (items.length === 0 && filter) return null;

          return (
            <div key={type}>
              {!filter && (
                <h3 className="text-lg font-semibold mb-3 capitalize">
                  {type}s ({items.length})
                </h3>
              )}
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                {items.map((entity) => (
                  <EntityCard
                    key={entity.id}
                    entity={entity}
                    onClick={() => onEntityClick?.(entity)}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-8">
          <p className="text-gray-500">No entities found</p>
        </div>
      )}
    </div>
  );
};

export default IntelligenceEntities;

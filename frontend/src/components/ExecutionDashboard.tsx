import React, { useState } from 'react';
import { AlertCircle, CheckCircle, Clock, TrendingUp, Zap } from 'lucide-react';

interface ExecutionState {
  execution_id: string;
  entity_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'blocked' | 'overdue';
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

interface ExecutionDashboardProps {
  summary: ExecutionSummary;
  executions: ExecutionState[];
  loading?: boolean;
  onExecutionClick?: (execution: ExecutionState) => void;
}

const statusColors: Record<string, { bg: string; text: string; border: string }> =
  {
    pending: {
      bg: 'bg-gray-50',
      text: 'text-gray-700',
      border: 'border-gray-200',
    },
    in_progress: {
      bg: 'bg-blue-50',
      text: 'text-blue-700',
      border: 'border-blue-200',
    },
    completed: {
      bg: 'bg-green-50',
      text: 'text-green-700',
      border: 'border-green-200',
    },
    blocked: {
      bg: 'bg-red-50',
      text: 'text-red-700',
      border: 'border-red-200',
    },
    overdue: {
      bg: 'bg-orange-50',
      text: 'text-orange-700',
      border: 'border-orange-200',
    },
  };

const statusIcons: Record<string, React.ReactNode> = {
  pending: <Clock size={18} />,
  in_progress: <TrendingUp size={18} />,
  completed: <CheckCircle size={18} />,
  blocked: <AlertCircle size={18} />,
  overdue: <Zap size={18} />,
};

const SummaryCard: React.FC<{
  label: string;
  count: number;
  status: string;
}> = ({ label, count, status }) => {
  const colors = statusColors[status as keyof typeof statusColors] || statusColors.pending;

  return (
    <div className={`${colors.bg} ${colors.border} border rounded-lg p-4`}>
      <div className={`${colors.text} flex items-center gap-2 mb-2`}>
        {statusIcons[status]}
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className={`${colors.text} text-3xl font-bold`}>{count}</div>
    </div>
  );
};

const ExecutionItem: React.FC<{
  execution: ExecutionState;
  onClick?: () => void;
}> = ({ execution, onClick }) => {
  const colors = statusColors[execution.status];

  return (
    <div
      className={`${colors.bg} ${colors.border} border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className={colors.text}>{statusIcons[execution.status]}</div>
          <div>
            <p className={`${colors.text} font-semibold text-sm`}>
              {execution.entity_id}
            </p>
            <p className={`${colors.text} text-xs opacity-75`}>
              {execution.status.toUpperCase().replace('_', ' ')}
            </p>
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs opacity-75">Progress</span>
          <span className="text-xs font-medium">{execution.progress_percent}%</span>
        </div>
        <div className="w-full h-2 bg-gray-300 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all"
            style={{ width: `${execution.progress_percent}%` }}
          />
        </div>
      </div>

      {/* Metadata */}
      <div className="flex flex-wrap gap-2 text-xs">
        {execution.due_date && (
          <span className="bg-white px-2 py-1 rounded">
            Due: {new Date(execution.due_date).toLocaleDateString()}
          </span>
        )}
        {execution.recurring && (
          <span className="bg-white px-2 py-1 rounded">
            Recurring: {execution.recurrence_pattern}
          </span>
        )}
        {execution.depends_on && execution.depends_on.length > 0 && (
          <span className="bg-white px-2 py-1 rounded">
            Depends: {execution.depends_on.length}
          </span>
        )}
      </div>
    </div>
  );
};

const ExecutionDashboard: React.FC<ExecutionDashboardProps> = ({
  summary,
  executions,
  loading = false,
  onExecutionClick,
}) => {
  const [filter, setFilter] = useState<string | null>(null);

  const filtered =
    filter && filter !== 'all'
      ? executions.filter((e) => e.status === filter)
      : executions;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="mt-2 text-gray-600 text-sm">Loading execution data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <SummaryCard
          label="Total"
          count={summary.total_executions}
          status="pending"
        />
        <SummaryCard label="Pending" count={summary.pending} status="pending" />
        <SummaryCard
          label="In Progress"
          count={summary.in_progress}
          status="in_progress"
        />
        <SummaryCard
          label="Completed"
          count={summary.completed}
          status="completed"
        />
        <SummaryCard label="Blocked" count={summary.blocked} status="blocked" />
        <SummaryCard label="Overdue" count={summary.overdue} status="overdue" />
      </div>

      {/* Critical items */}
      {summary.critical_items && summary.critical_items.length > 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-orange-900 mb-3">
            Critical Items ({summary.critical_items.length})
          </h3>
          <div className="space-y-2">
            {summary.critical_items.map((item) => (
              <div
                key={item.execution_id}
                className="bg-white p-3 rounded border border-orange-100 text-sm"
              >
                <p className="font-medium text-orange-900">{item.entity_title}</p>
                <p className="text-orange-700 text-xs mt-1">
                  {item.reason.replace(/_/g, ' ').toUpperCase()}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

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
        {['pending', 'in_progress', 'completed', 'blocked', 'overdue'].map(
          (status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                filter === status
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {status.replace('_', ' ').toUpperCase()}
            </button>
          )
        )}
      </div>

      {/* Execution list */}
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map((execution) => (
          <ExecutionItem
            key={execution.execution_id}
            execution={execution}
            onClick={() => onExecutionClick?.(execution)}
          />
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-8">
          <p className="text-gray-500">No executions found</p>
        </div>
      )}
    </div>
  );
};

export default ExecutionDashboard;

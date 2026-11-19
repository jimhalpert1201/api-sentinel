import { FC } from 'react';
import { CheckResult } from '../types/monitor';
import { CheckCircle2, XCircle, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';

interface CheckHistoryTableProps {
  checks: CheckResult[];
  total: number;
  page: number;
  pages: number;
  statusFilter: string;
  onPageChange: (newPage: number) => void;
  onStatusFilterChange: (status: string) => void;
  isLoading?: boolean;
}

export const CheckHistoryTable: FC<CheckHistoryTableProps> = ({
  checks,
  total,
  page,
  pages,
  statusFilter,
  onPageChange,
  onStatusFilterChange,
  isLoading = false,
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
      {/* Table Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-white">Execution History</h3>
          <p className="text-xs text-slate-400">Total recorded checks: {total}</p>
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <label htmlFor="check-status-filter" className="text-xs text-slate-400">
            Filter:
          </label>
          <select
            id="check-status-filter"
            value={statusFilter}
            onChange={(e) => onStatusFilterChange(e.target.value)}
            className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-white text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="all">All Results</option>
            <option value="passed">Passed (2xx/3xx)</option>
            <option value="failed">Failed (Errors/Timeouts)</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
              <th className="py-3 px-3">Status</th>
              <th className="py-3 px-3">Checked At</th>
              <th className="py-3 px-3">HTTP Code</th>
              <th className="py-3 px-3">Latency</th>
              <th className="py-3 px-3">Diagnostics / Error</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="py-12 text-center text-slate-500">
                  <div className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-emerald-500" />
                    <span>Loading check logs...</span>
                  </div>
                </td>
              </tr>
            ) : checks.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-500">
                  No checks recorded for this filter.
                </td>
              </tr>
            ) : (
              checks.map((check) => (
                <tr key={check.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-3 whitespace-nowrap">
                    {check.is_successful ? (
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Pass
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        <XCircle className="w-3.5 h-3.5" />
                        Fail
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap font-mono text-slate-300">
                    {new Date(check.checked_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap font-mono">
                    {check.status_code != null ? (
                      <span
                        className={`px-1.5 py-0.5 rounded text-[11px] font-bold ${
                          check.status_code >= 200 && check.status_code < 400
                            ? 'bg-slate-800 text-emerald-400'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}
                      >
                        {check.status_code}
                      </span>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap font-mono text-slate-300">
                    {check.response_time_ms != null
                      ? `${Math.round(check.response_time_ms)} ms`
                      : '—'}
                  </td>
                  <td className="py-3 px-3 max-w-xs truncate text-slate-400 font-mono">
                    {check.error_message ? (
                      <span className="text-rose-400/90" title={check.error_message}>
                        {check.error_message}
                      </span>
                    ) : (
                      <span className="text-slate-600">None</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {pages > 1 && (
        <div className="flex items-center justify-between pt-4 border-t border-slate-800 text-xs">
          <span className="text-slate-400">
            Page {page} of {pages}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={page <= 1 || isLoading}
              onClick={() => onPageChange(page - 1)}
              className="p-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              type="button"
              disabled={page >= pages || isLoading}
              onClick={() => onPageChange(page + 1)}
              className="p-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};


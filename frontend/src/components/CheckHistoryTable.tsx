import { useState, FC } from 'react';
import { CheckResult } from '../types/monitor';
import {
  CheckCircle2,
  XCircle,
  ChevronLeft,
  ChevronRight,
  Loader2,
  X,
  Clock,
  Zap,
  AlertTriangle,
  Info,
} from 'lucide-react';

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
  const [selectedCheck, setSelectedCheck] = useState<CheckResult | null>(null);

  return (
    <div className="bg-[#0e1526] border border-slate-800/80 rounded-2xl p-6 shadow-sm space-y-4">
      {/* Table Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-bold text-white tracking-tight uppercase font-mono">
            Execution Telemetry History
          </h3>
          <p className="text-xs text-slate-400">
            {total} total recorded probes. Click any row to inspect deep diagnostic details.
          </p>
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <label htmlFor="check-status-filter" className="text-xs text-slate-400 font-mono">
            Filter:
          </label>
          <select
            id="check-status-filter"
            value={statusFilter}
            onChange={(e) => onStatusFilterChange(e.target.value)}
            className="px-3 py-1.5 bg-[#080d19] border border-slate-800 rounded-xl text-white text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
          >
            <option value="all">All Results</option>
            <option value="passed">Passed Probes</option>
            <option value="failed">Failed Probes</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider font-mono">
              <th className="py-3 px-3">Status</th>
              <th className="py-3 px-3">Checked At</th>
              <th className="py-3 px-3">HTTP Code</th>
              <th className="py-3 px-3">Latency</th>
              <th className="py-3 px-3">Diagnostics / Error</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="py-12 text-center text-slate-500">
                  <div className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-emerald-500" />
                    <span>Loading execution telemetry...</span>
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
                <tr
                  key={check.id}
                  onClick={() => setSelectedCheck(check)}
                  title="Click to inspect probe diagnostic details"
                  className="hover:bg-slate-800/40 cursor-pointer transition-colors group"
                >
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
                  <td className="py-3 px-3 whitespace-nowrap text-slate-300">
                    {new Date(check.checked_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
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
                  <td className="py-3 px-3 whitespace-nowrap text-slate-300">
                    {check.response_time_ms != null
                      ? `${Math.round(check.response_time_ms)} ms`
                      : '—'}
                  </td>
                  <td className="py-3 px-3 max-w-xs truncate text-slate-400">
                    {check.error_message ? (
                      <span className="text-rose-400/90 group-hover:text-rose-300" title={check.error_message}>
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
        <div className="flex items-center justify-between pt-4 border-t border-slate-800 text-xs font-mono">
          <span className="text-slate-400">
            Page {page} of {pages}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={page <= 1 || isLoading}
              onClick={() => onPageChange(page - 1)}
              className="p-1.5 rounded-lg bg-[#080d19] border border-slate-800 text-slate-400 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              type="button"
              disabled={page >= pages || isLoading}
              onClick={() => onPageChange(page + 1)}
              className="p-1.5 rounded-lg bg-[#080d19] border border-slate-800 text-slate-400 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Check Inspection Detail Dialog (Section 13) */}
      {selectedCheck && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="check-detail-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
        >
          <div className="relative w-full max-w-md bg-[#0e1526] border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-5 animate-in fade-in zoom-in-95 duration-150">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    selectedCheck.is_successful
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  }`}
                >
                  {selectedCheck.is_successful ? (
                    <CheckCircle2 className="w-4 h-4" />
                  ) : (
                    <AlertTriangle className="w-4 h-4" />
                  )}
                </div>
                <div>
                  <h3 id="check-detail-title" className="text-sm font-bold text-white font-mono uppercase">
                    Probe Diagnostic Details
                  </h3>
                  <span className="text-[11px] text-slate-400 font-mono">
                    ID: {selectedCheck.id.slice(0, 12)}...
                  </span>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setSelectedCheck(null)}
                aria-label="Close dialog"
                className="p-1 text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Metrics Breakdown */}
            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-3 rounded-xl bg-[#080d19] border border-slate-800 space-y-1">
                <span className="text-slate-400 flex items-center gap-1 text-[11px]">
                  <Clock className="w-3 h-3 text-slate-500" />
                  Status Code
                </span>
                <span
                  className={`text-base font-bold ${
                    selectedCheck.status_code && selectedCheck.status_code < 400
                      ? 'text-emerald-400'
                      : 'text-rose-400'
                  }`}
                >
                  {selectedCheck.status_code ?? 'Timeout / Network Error'}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-[#080d19] border border-slate-800 space-y-1">
                <span className="text-slate-400 flex items-center gap-1 text-[11px]">
                  <Zap className="w-3 h-3 text-amber-400" />
                  Response Time
                </span>
                <span className="text-base font-bold text-white">
                  {selectedCheck.response_time_ms != null
                    ? `${Math.round(selectedCheck.response_time_ms)} ms`
                    : 'N/A'}
                </span>
              </div>
            </div>

            {/* Timestamp */}
            <div className="p-3 rounded-xl bg-[#080d19] border border-slate-800 text-xs font-mono space-y-1">
              <span className="text-slate-400 text-[11px]">Execution Timestamp</span>
              <p className="text-slate-200">
                {new Date(selectedCheck.checked_at).toISOString()} ({new Date(selectedCheck.checked_at).toLocaleString()})
              </p>
            </div>

            {/* Error Diagnostics if failed */}
            {!selectedCheck.is_successful && selectedCheck.error_message && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-mono space-y-1">
                <span className="font-semibold text-rose-400 flex items-center gap-1">
                  <Info className="w-3 h-3" />
                  Error Diagnostics
                </span>
                <p className="text-rose-200/90 break-words">{selectedCheck.error_message}</p>
              </div>
            )}

            {/* Close Button */}
            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => setSelectedCheck(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold font-mono"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

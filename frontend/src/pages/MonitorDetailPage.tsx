import { useState, useEffect, useCallback, FC } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { MonitorResponse, CheckResult } from '../types/monitor';
import { MonitorMetricsResponse } from '../types/metrics';
import { IncidentResponse } from '../types/incident';
import { monitorsApi } from '../api/monitors';
import { incidentsApi } from '../api/incidents';
import { LatencyChart } from '../components/LatencyChart';
import { CheckHistoryTable } from '../components/CheckHistoryTable';
import { MonitorModal } from '../components/MonitorModal';
import {
  ArrowLeft,
  Activity,
  Edit2,
  Trash2,
  ExternalLink,
  Loader2,
  Clock,
  BellRing,
  CheckCircle,
  AlertOctagon,
  Percent,
  Timer,
  Zap,
} from 'lucide-react';

export const MonitorDetailPage: FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [monitor, setMonitor] = useState<MonitorResponse | null>(null);
  const [activeIncident, setActiveIncident] = useState<IncidentResponse | null>(null);
  const [metricsData, setMetricsData] = useState<MonitorMetricsResponse | null>(null);
  const [metricWindow, setMetricWindow] = useState<'24h' | '7d' | '30d'>('24h');

  // Paginated check log state
  const [checks, setChecks] = useState<CheckResult[]>([]);
  const [totalChecks, setTotalChecks] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [checkStatusFilter, setCheckStatusFilter] = useState('all');

  const [isLoading, setIsLoading] = useState(true);
  const [isChecking, setIsChecking] = useState(false);
  const [isMetricsLoading, setIsMetricsLoading] = useState(false);
  const [isChecksLoading, setIsChecksLoading] = useState(false);

  // Edit modal
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // Fetch base monitor and active incident
  const fetchMonitor = useCallback(async () => {
    if (!id) return;
    try {
      const [mon, incs] = await Promise.all([
        monitorsApi.getMonitor(id),
        incidentsApi.listIncidents({ monitor_id: id, limit: 10 }),
      ]);
      setMonitor(mon);
      const active = incs.find((inc) => inc.status !== 'resolved') || null;
      setActiveIncident(active);
    } catch (err) {
      console.error('Failed to load monitor details:', err);
    }
  }, [id]);

  // Fetch metrics for chosen window
  const fetchMetrics = useCallback(
    async (win: '24h' | '7d' | '30d') => {
      if (!id) return;
      setIsMetricsLoading(true);
      try {
        const res = await monitorsApi.getMetrics(id, win);
        setMetricsData(res);
      } catch (err) {
        console.error('Failed to load metrics:', err);
      } finally {
        setIsMetricsLoading(false);
      }
    },
    [id]
  );

  // Fetch paginated check results
  const fetchChecks = useCallback(
    async (page: number, filter: string) => {
      if (!id) return;
      setIsChecksLoading(true);
      try {
        const res = await monitorsApi.getChecks(id, page, 10, filter);
        setChecks(res.items);
        setTotalChecks(res.total);
        setCurrentPage(res.page);
        setTotalPages(res.pages ?? Math.max(1, Math.ceil(res.total / (res.page_size || 10))));
      } catch (err) {
        console.error('Failed to load checks:', err);
      } finally {
        setIsChecksLoading(false);
      }
    },
    [id]
  );

  // Initial load
  useEffect(() => {
    setIsLoading(true);
    Promise.all([fetchMonitor(), fetchMetrics(metricWindow), fetchChecks(1, checkStatusFilter)]).finally(
      () => {
        setIsLoading(false);
      }
    );
  }, [fetchMonitor, fetchMetrics, fetchChecks, metricWindow, checkStatusFilter]);

  const handleWindowChange = (win: '24h' | '7d' | '30d') => {
    setMetricWindow(win);
    fetchMetrics(win);
  };

  const handlePageChange = (newPage: number) => {
    fetchChecks(newPage, checkStatusFilter);
  };

  const handleStatusFilterChange = (newFilter: string) => {
    setCheckStatusFilter(newFilter);
    fetchChecks(1, newFilter);
  };

  const handleTriggerCheck = async () => {
    if (!id) return;
    setIsChecking(true);
    try {
      await monitorsApi.triggerCheck(id);
      // Refresh metrics, checks, and monitor
      await Promise.all([
        fetchMonitor(),
        fetchMetrics(metricWindow),
        fetchChecks(currentPage, checkStatusFilter),
      ]);
    } catch (err) {
      console.error('Manual check failed:', err);
    } finally {
      setIsChecking(false);
    }
  };

  const handleDelete = async () => {
    if (!monitor) return;
    if (window.confirm(`Are you sure you want to permanently delete monitor "${monitor.name}"?`)) {
      try {
        await monitorsApi.deleteMonitor(monitor.id);
        navigate('/', { replace: true });
      } catch (err) {
        console.error('Failed to delete monitor:', err);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-slate-400 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
        <p className="text-sm font-medium">Loading monitor telemetry...</p>
      </div>
    );
  }

  if (!monitor) {
    return (
      <div className="py-20 text-center space-y-4">
        <p className="text-slate-400 text-sm">Monitor not found or you do not have permission.</p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 text-slate-200 text-xs font-semibold hover:bg-slate-700 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Link>
      </div>
    );
  }

  // Status derivation
  const isPaused = !monitor.is_active;
  const isDown = !isPaused && !!activeIncident;
  const isUp = !isPaused && !isDown;

  const summary = metricsData?.metrics;

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Top Breadcrumb & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Link>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleTriggerCheck}
            disabled={isChecking}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-xs font-semibold transition-all disabled:opacity-50"
          >
            {isChecking ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Executing Check...</span>
              </>
            ) : (
              <>
                <Activity className="w-4 h-4" />
                <span>Check Now</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={() => setIsEditModalOpen(true)}
            aria-label="Edit monitor"
            title="Edit monitor"
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <Edit2 className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={handleDelete}
            aria-label="Delete monitor"
            title="Delete monitor"
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Monitor Header Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                {monitor.name}
              </h1>

              {isPaused && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                  <span className="w-2 h-2 rounded-full bg-slate-500" />
                  PAUSED
                </span>
              )}
              {isDown && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                  DOWN
                </span>
              )}
              {isUp && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  HEALTHY
                </span>
              )}

              <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
                {monitor.method}
              </span>
            </div>

            <div className="flex items-center gap-2 text-xs font-mono text-slate-400 pt-1">
              <span className="truncate max-w-xl">{monitor.url}</span>
              <a
                href={monitor.url}
                target="_blank"
                rel="noreferrer"
                className="text-slate-500 hover:text-slate-300 transition-colors"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>

          {/* Quick config badges */}
          <div className="flex items-center gap-3 text-xs flex-wrap">
            <div className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center gap-1.5 text-slate-300">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              <span>Interval: {monitor.interval_seconds}s</span>
            </div>
            <div className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center gap-1.5 text-slate-300">
              <Timer className="w-3.5 h-3.5 text-slate-500" />
              <span>Timeout: {monitor.timeout_seconds}s</span>
            </div>
            <div className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center gap-1.5 text-slate-300">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
              <span>Expects: {monitor.expected_status_code}</span>
            </div>
            {monitor.webhook_url && (
              <div
                title={monitor.webhook_url}
                className="px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center gap-1.5 text-amber-300"
              >
                <BellRing className="w-3.5 h-3.5" />
                <span className="truncate max-w-[140px]">Webhook Enabled</span>
              </div>
            )}
          </div>
        </div>

        {/* Down Banner if active incident */}
        {isDown && activeIncident && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs sm:text-sm flex items-start gap-3">
            <AlertOctagon className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-400" />
            <div>
              <p className="font-semibold">Active Outage Incident</p>
              <p className="text-xs text-rose-200/80 mt-1">
                Cause: {activeIncident.cause} (Triggered:{' '}
                {new Date(activeIncident.started_at).toLocaleString()})
              </p>
            </div>
          </div>
        )}
      </div>

      {/* KPI Metric Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Uptime % */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Uptime ({metricWindow})</span>
            <Percent className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">
            {summary?.uptime_percentage != null
              ? `${summary.uptime_percentage.toFixed(1)}%`
              : 'N/A'}
          </div>
          <p className="mt-1 text-xs text-slate-400">
            {summary?.successful_checks ?? 0} pass / {summary?.total_checks ?? 0} total
          </p>
        </div>

        {/* Avg Latency */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Avg Latency</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">
            {summary?.avg_response_time_ms != null
              ? `${Math.round(summary.avg_response_time_ms)} ms`
              : 'N/A'}
          </div>
          <p className="mt-1 text-xs text-slate-400">Sliding window average</p>
        </div>

        {/* Percentiles (p50 / p95 / p99) */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Percentiles</span>
            <Timer className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-lg font-bold text-slate-200 space-y-0.5">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">p50:</span>
              <span className="font-mono">{summary?.p50_ms != null ? `${Math.round(summary.p50_ms)}ms` : '—'}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">p95:</span>
              <span className="font-mono">{summary?.p95_ms != null ? `${Math.round(summary.p95_ms)}ms` : '—'}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">p99:</span>
              <span className="font-mono">{summary?.p99_ms != null ? `${Math.round(summary.p99_ms)}ms` : '—'}</span>
            </div>
          </div>
        </div>

        {/* Failure Count */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Failed Checks</span>
            <AlertOctagon className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-3xl font-extrabold text-rose-400">
            {summary?.failed_checks ?? 0}
          </div>
          <p className="mt-1 text-xs text-slate-400">Non-2xx or timeouts</p>
        </div>
      </div>

      {/* Latency Trends Area Chart */}
      <LatencyChart
        timeSeries={metricsData?.time_series || []}
        currentWindow={metricWindow}
        onWindowChange={handleWindowChange}
        isLoading={isMetricsLoading}
      />

      {/* Check History Execution Table */}
      <CheckHistoryTable
        checks={checks}
        total={totalChecks}
        page={currentPage}
        pages={totalPages}
        statusFilter={checkStatusFilter}
        onPageChange={handlePageChange}
        onStatusFilterChange={handleStatusFilterChange}
        isLoading={isChecksLoading}
      />

      {/* Edit Modal */}
      <MonitorModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSuccess={(updated) => setMonitor(updated)}
        initialMonitor={monitor}
      />
    </div>
  );
};

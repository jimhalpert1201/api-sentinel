import { useState, useEffect, useCallback, useMemo, FC } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { MonitorResponse, CheckResult } from '../types/monitor';
import { IncidentResponse } from '../types/incident';
import { monitorsApi } from '../api/monitors';
import { incidentsApi } from '../api/incidents';
import { MonitorCard } from '../components/MonitorCard';
import { MonitorModal } from '../components/MonitorModal';
import {
  Plus,
  Search,
  CheckCircle2,
  AlertTriangle,
  PauseCircle,
  Radio,
  Loader2,
  RefreshCw,
  Zap,
  ShieldCheck,
  ShieldAlert,
} from 'lucide-react';

export const DashboardPage: FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [monitors, setMonitors] = useState<MonitorResponse[]>([]);
  const [incidents, setIncidents] = useState<IncidentResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'up' | 'down' | 'paused'>('all');

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingMonitor, setEditingMonitor] = useState<MonitorResponse | null>(null);

  const fetchData = useCallback(async (quiet = false) => {
    if (!quiet) setIsLoading(true);
    else setIsRefreshing(true);

    try {
      const [monitorsRes, incidentsRes] = await Promise.all([
        monitorsApi.listMonitors(0, 100),
        incidentsApi.listIncidents({ limit: 100 }),
      ]);
      setMonitors(monitorsRes);
      setIncidents(incidentsRes);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to fetch dashboard telemetry:', err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Active incidents map by monitor_id (only status !== 'resolved')
  const activeIncidentsByMonitorId = useMemo(() => {
    const map: Record<string, IncidentResponse> = {};
    incidents
      .filter((inc) => inc.status !== 'resolved')
      .forEach((inc) => {
        if (!map[inc.monitor_id] || new Date(inc.created_at) > new Date(map[inc.monitor_id].created_at)) {
          map[inc.monitor_id] = inc;
        }
      });
    return map;
  }, [incidents]);

  // Status Metrics
  const totalMonitors = monitors.length;
  const pausedMonitors = monitors.filter((m) => !m.is_active).length;
  const downMonitors = monitors.filter(
    (m) => m.is_active && !!activeIncidentsByMonitorId[m.id]
  ).length;
  const upMonitors = monitors.filter(
    (m) => m.is_active && !activeIncidentsByMonitorId[m.id]
  ).length;
  const totalActiveIncidents = Object.keys(activeIncidentsByMonitorId).length;

  // Filtered monitors
  const filteredMonitors = useMemo(() => {
    return monitors.filter((monitor) => {
      const matchesSearch =
        monitor.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        monitor.url.toLowerCase().includes(searchQuery.toLowerCase());

      if (!matchesSearch) return false;

      const isPaused = !monitor.is_active;
      const isDown = !isPaused && !!activeIncidentsByMonitorId[monitor.id];
      const isUp = !isPaused && !isDown;

      if (statusFilter === 'up') return isUp;
      if (statusFilter === 'down') return isDown;
      if (statusFilter === 'paused') return isPaused;
      return true;
    });
  }, [monitors, searchQuery, statusFilter, activeIncidentsByMonitorId]);

  const handleCreateNew = () => {
    setEditingMonitor(null);
    setIsModalOpen(true);
  };

  const handleEdit = (monitor: MonitorResponse) => {
    setEditingMonitor(monitor);
    setIsModalOpen(true);
  };

  const handleDelete = async (id: string) => {
    try {
      await monitorsApi.deleteMonitor(id);
      setMonitors((prev) => prev.filter((m) => m.id !== id));
    } catch (err) {
      console.error('Failed to delete monitor:', err);
    }
  };

  const handleModalSuccess = (savedMonitor: MonitorResponse) => {
    setMonitors((prev) => {
      const index = prev.findIndex((m) => m.id === savedMonitor.id);
      if (index >= 0) {
        const next = [...prev];
        next[index] = savedMonitor;
        return next;
      }
      return [savedMonitor, ...prev];
    });
  };

  const handleStatusToggle = (updated: MonitorResponse) => {
    setMonitors((prev) =>
      prev.map((m) => (m.id === updated.id ? updated : m))
    );
  };

  const handleCheckComplete = (_result: CheckResult) => {
    fetchData(true);
  };

  // Determine overall system operational state
  const isSystemHealthy = downMonitors === 0 && totalActiveIncidents === 0;

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* 1. Observability Header & Operational Greeting */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#0e1526] border border-slate-800/80 p-6 rounded-2xl shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 18 ? 'afternoon' : 'evening'}, {user?.username || 'Engineer'}
            </h2>
          </div>

          <div className="flex items-center gap-2 pt-1">
            {isSystemHealthy ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                <ShieldCheck className="w-3.5 h-3.5" />
                ALL SYSTEMS OPERATIONAL
              </span>
            ) : downMonitors > 0 ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30 font-mono animate-pulse">
                <ShieldAlert className="w-3.5 h-3.5" />
                {downMonitors} OUTAGE DETECTED
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 font-mono">
                <AlertTriangle className="w-3.5 h-3.5" />
                INVESTIGATING INCIDENT
              </span>
            )}

            <span className="text-xs text-slate-400 font-mono">
              Last synced: {lastUpdated.toLocaleTimeString()}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 self-start md:self-auto">
          <button
            type="button"
            onClick={() => fetchData(true)}
            disabled={isRefreshing}
            aria-label="Refresh telemetry"
            title="Refresh telemetry"
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors text-xs font-semibold"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            type="button"
            onClick={handleCreateNew}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 text-xs font-bold tracking-wide uppercase transition-colors shadow-md shadow-emerald-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>New Monitor</span>
          </button>
        </div>
      </div>

      {/* 2. Primary KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Fleet */}
        <div className="bg-[#0e1526] border border-slate-800/80 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider font-mono">Monitored Fleet</span>
            <Radio className="w-4 h-4 text-slate-500" />
          </div>
          <div className="text-3xl font-extrabold text-white tracking-tight">{totalMonitors}</div>
          <p className="mt-1 text-xs text-slate-400">{pausedMonitors} paused</p>
        </div>

        {/* Operational */}
        <div className="bg-[#0e1526] border border-slate-800/80 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-emerald-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider font-mono">Healthy</span>
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400 tracking-tight">{upMonitors}</div>
          <p className="mt-1 text-xs text-slate-400">Passing all assertions</p>
        </div>

        {/* Down Outages */}
        <div className="bg-[#0e1526] border border-slate-800/80 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-rose-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider font-mono">Down</span>
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div className="text-3xl font-extrabold text-rose-400 tracking-tight">{downMonitors}</div>
          <p className="mt-1 text-xs text-slate-400">Threshold breaches</p>
        </div>

        {/* Active Incidents */}
        <div className="bg-[#0e1526] border border-slate-800/80 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-amber-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider font-mono">Active Incidents</span>
            <Zap className="w-4 h-4" />
          </div>
          <div className="text-3xl font-extrabold text-amber-400 tracking-tight">{totalActiveIncidents}</div>
          <p className="mt-1 text-xs text-slate-400">Open or investigating</p>
        </div>
      </div>

      {/* 3. System Health Dot Matrix (Section 10 of Design Direction) */}
      {monitors.length > 0 && (
        <div className="bg-[#0e1526] border border-slate-800/80 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-white tracking-tight uppercase font-mono">
                Fleet Health Matrix
              </h3>
              <p className="text-xs text-slate-400">Instant visual distribution across all endpoints</p>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono">
              <span className="flex items-center gap-1.5 text-emerald-400">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                {upMonitors} Healthy
              </span>
              {downMonitors > 0 && (
                <span className="flex items-center gap-1.5 text-rose-400">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
                  {downMonitors} Down
                </span>
              )}
              {pausedMonitors > 0 && (
                <span className="flex items-center gap-1.5 text-slate-400">
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-500" />
                  {pausedMonitors} Paused
                </span>
              )}
            </div>
          </div>

          {/* Pip Grid */}
          <div className="p-4 rounded-xl bg-[#080d19] border border-slate-800/90 flex flex-wrap gap-2.5 items-center">
            {monitors.map((m) => {
              const isPaused = !m.is_active;
              const isDown = !isPaused && !!activeIncidentsByMonitorId[m.id];

              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => navigate(`/monitors/${m.id}`)}
                  title={`${m.name} (${m.url}) - ${isDown ? 'DOWN' : isPaused ? 'PAUSED' : 'HEALTHY'}`}
                  aria-label={`${m.name}: ${isDown ? 'DOWN' : isPaused ? 'PAUSED' : 'HEALTHY'}`}
                  className={`w-4 h-4 rounded-full transition-transform hover:scale-125 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#080d19] ${
                    isDown
                      ? 'bg-rose-500 shadow-sm shadow-rose-500/50 animate-pulse focus:ring-rose-400'
                      : isPaused
                      ? 'bg-slate-600 focus:ring-slate-400'
                      : 'bg-emerald-500 shadow-sm shadow-emerald-500/50 focus:ring-emerald-400'
                  }`}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* 4. Controls: Search, Filters & Quick Stats */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search monitors by name or URL..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#0e1526] border border-slate-800 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-sans"
          />
        </div>

        {/* Status Filter Buttons */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-[#0e1526] border border-slate-800 text-xs font-medium flex-wrap">
          <button
            type="button"
            onClick={() => setStatusFilter('all')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              statusFilter === 'all'
                ? 'bg-slate-800 text-white font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All ({totalMonitors})
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter('up')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              statusFilter === 'up'
                ? 'bg-emerald-500/10 text-emerald-400 font-semibold border border-emerald-500/20'
                : 'text-slate-400 hover:text-emerald-400'
            }`}
          >
            Healthy ({upMonitors})
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter('down')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              statusFilter === 'down'
                ? 'bg-rose-500/10 text-rose-400 font-semibold border border-rose-500/20'
                : 'text-slate-400 hover:text-rose-400'
            }`}
          >
            Down ({downMonitors})
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter('paused')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              statusFilter === 'paused'
                ? 'bg-slate-800 text-slate-300 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Paused ({pausedMonitors})
          </button>
        </div>
      </div>

      {/* 5. Monitors Grid */}
      {isLoading ? (
        <div className="py-24 flex flex-col items-center justify-center text-slate-400 gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
          <p className="text-sm font-medium">Loading monitor fleet...</p>
        </div>
      ) : filteredMonitors.length === 0 ? (
        <div className="py-20 text-center bg-[#0e1526]/50 border border-slate-800/80 rounded-2xl p-8">
          <div className="w-12 h-12 rounded-2xl bg-slate-800/80 text-slate-400 flex items-center justify-center mx-auto mb-4">
            <PauseCircle className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-white">No monitors found</h3>
          <p className="text-sm text-slate-400 mt-1 max-w-sm mx-auto">
            {searchQuery || statusFilter !== 'all'
              ? 'No monitors match the current search query or filter.'
              : 'Configure your first API endpoint to start automated uptime & latency checks.'}
          </p>
          {!searchQuery && statusFilter === 'all' && (
            <button
              type="button"
              onClick={handleCreateNew}
              className="mt-5 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 text-xs font-bold uppercase transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Create Monitor</span>
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredMonitors.map((monitor) => (
            <MonitorCard
              key={monitor.id}
              monitor={monitor}
              activeIncident={activeIncidentsByMonitorId[monitor.id]}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onCheckComplete={handleCheckComplete}
              onStatusToggle={handleStatusToggle}
            />
          ))}
        </div>
      )}

      {/* Create / Edit Guided Modal */}
      <MonitorModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleModalSuccess}
        initialMonitor={editingMonitor}
      />
    </div>
  );
};

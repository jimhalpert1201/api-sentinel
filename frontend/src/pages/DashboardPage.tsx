import { useState, useEffect, useCallback, useMemo, FC } from 'react';
import { MonitorResponse, CheckResult } from '../types/monitor';
import { IncidentResponse } from '../types/incident';
import { monitorsApi } from '../api/monitors';
import { incidentsApi } from '../api/incidents';
import { MonitorCard } from '../components/MonitorCard';
import { MonitorModal } from '../components/MonitorModal';
import {
  Plus,
  Search,
  Activity,
  CheckCircle,
  AlertTriangle,
  PauseCircle,
  Radio,
  Loader2,
  RefreshCw,
} from 'lucide-react';

export const DashboardPage: FC = () => {
  const [monitors, setMonitors] = useState<MonitorResponse[]>([]);
  const [incidents, setIncidents] = useState<IncidentResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
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
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
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
        // Keep the latest if multiple
        if (!map[inc.monitor_id] || new Date(inc.created_at) > new Date(map[inc.monitor_id].created_at)) {
          map[inc.monitor_id] = inc;
        }
      });
    return map;
  }, [incidents]);

  // KPI Calculations
  const totalMonitors = monitors.length;
  const pausedMonitors = monitors.filter((m) => !m.is_active).length;
  const downMonitors = monitors.filter(
    (m) => m.is_active && !!activeIncidentsByMonitorId[m.id]
  ).length;
  const upMonitors = monitors.filter(
    (m) => m.is_active && !activeIncidentsByMonitorId[m.id]
  ).length;
  const totalActiveIncidents = Object.keys(activeIncidentsByMonitorId).length;

  // Filtered monitors list
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
    // Optionally re-fetch quietly to update incident and status state
    fetchData(true);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Overview KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Monitors */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Monitors</span>
            <Radio className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{totalMonitors}</div>
          <p className="mt-1 text-xs text-slate-400">{pausedMonitors} paused</p>
        </div>

        {/* Up / Healthy */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-emerald-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Healthy</span>
            <CheckCircle className="w-4 h-4" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400">{upMonitors}</div>
          <p className="mt-1 text-xs text-slate-400">Passing all assertions</p>
        </div>

        {/* Down */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-rose-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Down</span>
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div className="text-3xl font-extrabold text-rose-400">{downMonitors}</div>
          <p className="mt-1 text-xs text-slate-400">Failed threshold checks</p>
        </div>

        {/* Active Incidents */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-amber-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Incidents</span>
            <Activity className="w-4 h-4" />
          </div>
          <div className="text-3xl font-extrabold text-amber-400">{totalActiveIncidents}</div>
          <p className="mt-1 text-xs text-slate-400">Open & acknowledged</p>
        </div>
      </div>

      {/* Control Bar: Search, Filters & Create Button */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        {/* Left: Search input */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search by monitor name or endpoint URL..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        {/* Right: Status Filters & Create Action */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Status filter tabs */}
          <div className="flex items-center p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs font-medium">
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

          <button
            type="button"
            onClick={() => fetchData(true)}
            disabled={isRefreshing}
            aria-label="Refresh dashboard data"
            title="Refresh dashboard data"
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
          </button>

          <button
            type="button"
            onClick={handleCreateNew}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 text-sm font-semibold transition-colors shadow-md shadow-emerald-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>Create Monitor</span>
          </button>
        </div>
      </div>

      {/* Monitors Grid */}
      {isLoading ? (
        <div className="py-24 flex flex-col items-center justify-center text-slate-400 gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
          <p className="text-sm font-medium">Loading monitor statuses...</p>
        </div>
      ) : filteredMonitors.length === 0 ? (
        <div className="py-20 text-center bg-slate-900/50 border border-slate-800/80 rounded-2xl p-8">
          <div className="w-12 h-12 rounded-2xl bg-slate-800/80 text-slate-400 flex items-center justify-center mx-auto mb-4">
            <PauseCircle className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-white">No monitors found</h3>
          <p className="text-sm text-slate-400 mt-1 max-w-sm mx-auto">
            {searchQuery || statusFilter !== 'all'
              ? 'No monitors match the current search query or status filter.'
              : 'Get started by creating your first endpoint uptime monitor.'}
          </p>
          {!searchQuery && statusFilter === 'all' && (
            <button
              type="button"
              onClick={handleCreateNew}
              className="mt-5 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 text-sm font-semibold transition-colors"
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

      {/* Create / Edit Monitor Modal */}
      <MonitorModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleModalSuccess}
        initialMonitor={editingMonitor}
      />
    </div>
  );
};

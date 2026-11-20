import { useState, useEffect, useCallback, useMemo, FC } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { IncidentResponse } from '../types/incident';
import { MonitorResponse } from '../types/monitor';
import { incidentsApi } from '../api/incidents';
import { monitorsApi } from '../api/monitors';
import { IncidentTimeline } from '../components/IncidentTimeline';
import {
  Bell,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Loader2,
  RefreshCw,
  ShieldAlert,
  MessageSquare,
  X,
} from 'lucide-react';

export const IncidentsPage: FC = () => {
  const [incidents, setIncidents] = useState<IncidentResponse[]>([]);
  const [monitors, setMonitors] = useState<MonitorResponse[]>([]);
  const [statusFilter, setStatusFilter] = useState<'all' | 'open' | 'acknowledged' | 'resolved'>('all');
  const [expandedIncidentIds, setExpandedIncidentIds] = useState<Set<string>>(new Set());

  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Acknowledge modal state
  const [ackIncident, setAckIncident] = useState<IncidentResponse | null>(null);
  const [ackNotes, setAckNotes] = useState('');
  const [isSubmittingAck, setIsSubmittingAck] = useState(false);

  const fetchData = useCallback(async (quiet = false) => {
    if (!quiet) setIsLoading(true);
    else setIsRefreshing(true);

    try {
      const [incidentsRes, monitorsRes] = await Promise.all([
        incidentsApi.listIncidents({ limit: 100 }),
        monitorsApi.listMonitors(0, 100),
      ]);
      setIncidents(incidentsRes);
      setMonitors(monitorsRes);
    } catch (err) {
      console.error('Failed to load incidents:', err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Monitor lookup map
  const monitorMap = useMemo(() => {
    const map: Record<string, MonitorResponse> = {};
    monitors.forEach((m) => {
      map[m.id] = m;
    });
    return map;
  }, [monitors]);

  // Toggle timeline expansion
  const toggleExpand = (id: string) => {
    setExpandedIncidentIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Duration helper
  const getDurationString = (startedAt: string, resolvedAt?: string | null) => {
    try {
      const start = new Date(startedAt).getTime();
      const end = resolvedAt ? new Date(resolvedAt).getTime() : Date.now();
      const diffMs = Math.max(0, end - start);
      const diffMins = Math.round(diffMs / 60000);

      if (diffMins < 60) {
        return `${diffMins} min${diffMins === 1 ? '' : 's'}`;
      }
      const diffHours = (diffMins / 60).toFixed(1);
      return `${diffHours} hour${diffHours === '1.0' ? '' : 's'}`;
    } catch {
      return 'Unknown';
    }
  };

  // Filtered incidents
  const filteredIncidents = useMemo(() => {
    return incidents.filter((inc) => {
      if (statusFilter === 'all') return true;
      return inc.status === statusFilter;
    });
  }, [incidents, statusFilter]);

  // Counts
  const openCount = incidents.filter((i) => i.status === 'open').length;
  const ackCount = incidents.filter((i) => i.status === 'acknowledged').length;
  const resCount = incidents.filter((i) => i.status === 'resolved').length;

  const handleOpenAckModal = (incident: IncidentResponse) => {
    setAckIncident(incident);
    setAckNotes('');
  };

  const handleConfirmAcknowledge = async () => {
    if (!ackIncident) return;
    setIsSubmittingAck(true);
    try {
      const updated = await incidentsApi.acknowledgeIncident(
        ackIncident.id,
        ackNotes.trim() || undefined
      );
      setIncidents((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
      // Automatically expand timeline to show acknowledgment entry
      setExpandedIncidentIds((prev) => new Set(prev).add(updated.id));
      toast.success('Incident acknowledged', {
        description: ackNotes.trim()
          ? `Operator notes: "${ackNotes.trim()}"`
          : 'Status changed to acknowledged',
      });
      setAckIncident(null);
    } catch (err) {
      console.error('Failed to acknowledge incident:', err);
      toast.error('Failed to acknowledge incident');
    } finally {
      setIsSubmittingAck(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Top Header & Refresh */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <ShieldAlert className="w-6 h-6 text-emerald-400" />
            <span>Incident Management</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Track threshold breaches, outages, recovery events, and webhook dispatch audits
          </p>
        </div>

        <button
          type="button"
          onClick={() => fetchData(true)}
          disabled={isRefreshing}
          aria-label="Refresh incident telemetry"
          title="Refresh incident telemetry"
          className="self-start sm:self-auto flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors text-xs font-semibold"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 p-1.5 rounded-2xl bg-[#0e1526] border border-slate-800 text-xs font-medium w-fit flex-wrap font-mono">
        <button
          type="button"
          onClick={() => setStatusFilter('all')}
          className={`px-3.5 py-1.5 rounded-xl transition-colors ${
            statusFilter === 'all'
              ? 'bg-slate-800 text-white font-semibold shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          All ({incidents.length})
        </button>
        <button
          type="button"
          onClick={() => setStatusFilter('open')}
          className={`px-3.5 py-1.5 rounded-xl transition-colors ${
            statusFilter === 'open'
              ? 'bg-rose-500/15 text-rose-400 font-semibold border border-rose-500/30'
              : 'text-slate-400 hover:text-rose-400'
          }`}
        >
          Open ({openCount})
        </button>
        <button
          type="button"
          onClick={() => setStatusFilter('acknowledged')}
          className={`px-3.5 py-1.5 rounded-xl transition-colors ${
            statusFilter === 'acknowledged'
              ? 'bg-amber-500/15 text-amber-400 font-semibold border border-amber-500/30'
              : 'text-slate-400 hover:text-amber-400'
          }`}
        >
          Acknowledged ({ackCount})
        </button>
        <button
          type="button"
          onClick={() => setStatusFilter('resolved')}
          className={`px-3.5 py-1.5 rounded-xl transition-colors ${
            statusFilter === 'resolved'
              ? 'bg-emerald-500/15 text-emerald-400 font-semibold border border-emerald-500/30'
              : 'text-slate-400 hover:text-emerald-400'
          }`}
        >
          Resolved ({resCount})
        </button>
      </div>

      {/* Incident List */}
      {isLoading ? (
        <div className="py-24 flex flex-col items-center justify-center text-slate-400 gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
          <p className="text-sm font-medium">Loading incident telemetry...</p>
        </div>
      ) : filteredIncidents.length === 0 ? (
        <div className="py-20 text-center bg-[#0e1526]/50 border border-slate-800/80 rounded-2xl p-8">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto mb-4 border border-emerald-500/20">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-white">No incidents found</h3>
          <p className="text-sm text-slate-400 mt-1 max-w-sm mx-auto">
            {statusFilter === 'all'
              ? 'No incidents have been recorded. All monitored endpoints are operational.'
              : `No incidents with status "${statusFilter}".`}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredIncidents.map((incident) => {
            const monitor = monitorMap[incident.monitor_id];
            const isExpanded = expandedIncidentIds.has(incident.id);
            const isResolved = incident.status === 'resolved';
            const isAck = incident.status === 'acknowledged';
            const isOpen = incident.status === 'open';

            return (
              <div
                key={incident.id}
                className="bg-[#0e1526] border border-slate-800/80 rounded-2xl p-5 shadow-sm space-y-4 transition-all"
              >
                {/* Incident Card Top Row */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      {/* Status badge */}
                      {isOpen && (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30 font-mono">
                          <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                          OPEN OUTAGE
                        </span>
                      )}
                      {isAck && (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 font-mono">
                          <span className="w-2 h-2 rounded-full bg-amber-500" />
                          ACKNOWLEDGED
                        </span>
                      )}
                      {isResolved && (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-mono">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          RESOLVED
                        </span>
                      )}

                      {/* Severity badge */}
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                          incident.severity === 'critical'
                            ? 'bg-rose-950 text-rose-400 border border-rose-700'
                            : incident.severity === 'major'
                            ? 'bg-amber-950 text-amber-400 border border-amber-700'
                            : 'bg-slate-800 text-slate-300 border border-slate-700'
                        }`}
                      >
                        {incident.severity}
                      </span>

                      {/* Target monitor link */}
                      {monitor ? (
                        <Link
                          to={`/monitors/${monitor.id}`}
                          className="inline-flex items-center gap-1 text-xs font-medium text-slate-300 hover:text-emerald-400 transition-colors font-mono"
                        >
                          <span className="underline decoration-slate-600 underline-offset-2">
                            {monitor.name}
                          </span>
                          <ExternalLink className="w-3 h-3 text-slate-500" />
                        </Link>
                      ) : (
                        <span className="text-xs font-mono text-slate-500">
                          Monitor {incident.monitor_id.slice(0, 8)}...
                        </span>
                      )}
                    </div>

                    {/* Incident cause text */}
                    <p className="text-sm text-white font-medium">{incident.cause}</p>
                  </div>

                  {/* Right Actions & Duration */}
                  <div className="flex items-center gap-3 self-start md:self-auto font-mono">
                    <div className="text-right text-xs text-slate-400 hidden sm:block">
                      <div className="flex items-center gap-1 text-slate-300">
                        <Clock className="w-3.5 h-3.5 text-slate-500" />
                        <span>Duration: {getDurationString(incident.started_at, incident.resolved_at)}</span>
                      </div>
                      <span className="text-[11px] text-slate-400">
                        {new Date(incident.started_at).toLocaleString()}
                      </span>
                    </div>

                    {/* Acknowledge Button */}
                    {isOpen && (
                      <button
                        type="button"
                        onClick={() => handleOpenAckModal(incident)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-400 text-xs font-semibold transition-colors font-mono"
                      >
                        <Bell className="w-3.5 h-3.5" />
                        <span>Acknowledge</span>
                      </button>
                    )}

                    {/* Timeline expand toggle */}
                    <button
                      type="button"
                      onClick={() => toggleExpand(incident.id)}
                      className="p-1.5 rounded-xl bg-[#080d19] border border-slate-800 text-slate-400 hover:text-white transition-colors"
                      title={isExpanded ? 'Hide audit timeline' : 'View audit timeline'}
                      aria-label={isExpanded ? 'Hide audit timeline' : 'View audit timeline'}
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Expanded Timeline Drawer */}
                {isExpanded && (
                  <div className="border-t border-slate-800/80 pt-4">
                    <IncidentTimeline incidentId={incident.id} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Acknowledge Incident Modal Dialog */}
      {ackIncident && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="ack-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
        >
          <div className="relative w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-5 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center border border-amber-500/20">
                  <AlertTriangle className="w-4 h-4" />
                </div>
                <h3 id="ack-modal-title" className="text-base font-bold text-white">
                  Acknowledge Incident
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setAckIncident(null)}
                aria-label="Close dialog"
                className="p-1 text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-300">
              Acknowledging this incident informs team members that an engineer is investigating the outage.
            </p>

            <div>
              <label htmlFor="ack-notes" className="block text-xs font-medium text-slate-300 mb-1">
                Investigation Notes (Optional)
              </label>
              <textarea
                id="ack-notes"
                rows={3}
                value={ackNotes}
                onChange={(e) => setAckNotes(e.target.value)}
                placeholder="e.g. Investigating downstream database latency spike..."
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700/80 rounded-xl text-white placeholder-slate-500 text-xs focus:outline-none focus:ring-2 focus:ring-amber-500 resize-none"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setAckIncident(null)}
                disabled={isSubmittingAck}
                className="px-4 py-2 rounded-xl text-slate-300 hover:text-white text-xs font-medium"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmAcknowledge}
                disabled={isSubmittingAck}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 text-xs font-semibold transition-colors disabled:opacity-50"
              >
                {isSubmittingAck ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Recording...</span>
                  </>
                ) : (
                  <>
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>Confirm Acknowledgment</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

import { useState, FC, MouseEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { MonitorResponse, CheckResult } from '../types/monitor';
import { IncidentResponse } from '../types/incident';
import { monitorsApi } from '../api/monitors';
import {
  Activity,
  Play,
  Pause,
  Edit2,
  Trash2,
  ExternalLink,
  Loader2,
  Clock,
  BellRing,
  AlertOctagon,
} from 'lucide-react';

interface MonitorCardProps {
  monitor: MonitorResponse;
  activeIncident?: IncidentResponse | null;
  onEdit: (monitor: MonitorResponse) => void;
  onDelete: (id: string) => void;
  onCheckComplete?: (result: CheckResult) => void;
  onStatusToggle?: (updated: MonitorResponse) => void;
}

export const MonitorCard: FC<MonitorCardProps> = ({
  monitor,
  activeIncident,
  onEdit,
  onDelete,
  onCheckComplete,
  onStatusToggle,
}) => {
  const navigate = useNavigate();
  const [isChecking, setIsChecking] = useState(false);
  const [isToggling, setIsToggling] = useState(false);
  const [lastCheckResult, setLastCheckResult] = useState<CheckResult | null>(null);

  // Status derivation:
  // ⚪ PAUSED if !monitor.is_active
  // 🔴 DOWN if active incident exists
  // 🟢 UP if active and no active incident
  const isPaused = !monitor.is_active;
  const isDown = !isPaused && !!activeIncident && activeIncident.status !== 'resolved';
  const isUp = !isPaused && !isDown;

  const handleTriggerCheck = async (e: MouseEvent) => {
    e.stopPropagation();
    setIsChecking(true);
    try {
      const result = await monitorsApi.triggerCheck(monitor.id);
      setLastCheckResult(result);
      if (onCheckComplete) {
        onCheckComplete(result);
      }
    } catch (err) {
      console.error('Manual check failed:', err);
    } finally {
      setIsChecking(false);
    }
  };

  const handleToggleActive = async (e: MouseEvent) => {
    e.stopPropagation();
    setIsToggling(true);
    try {
      const updated = await monitorsApi.updateMonitor(monitor.id, {
        is_active: !monitor.is_active,
      });
      if (onStatusToggle) {
        onStatusToggle(updated);
      }
    } catch (err) {
      console.error('Failed to toggle monitor status:', err);
    } finally {
      setIsToggling(false);
    }
  };

  const handleDelete = (e: MouseEvent) => {
    e.stopPropagation();
    if (window.confirm(`Are you sure you want to delete monitor "${monitor.name}"?`)) {
      onDelete(monitor.id);
    }
  };

  const handleCardClick = () => {
    navigate(`/monitors/${monitor.id}`);
  };

  return (
    <div
      onClick={handleCardClick}
      className="group relative bg-slate-900 border border-slate-800 hover:border-slate-700/80 rounded-2xl p-5 shadow-lg hover:shadow-xl transition-all cursor-pointer flex flex-col justify-between"
    >
      <div>
        {/* Top Header: Status Badge & HTTP Method */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
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

            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
              {monitor.method}
            </span>
          </div>

          {monitor.webhook_url && (
            <span
              title="Webhook alerting configured"
              className="text-amber-400/80 p-1 rounded-lg bg-amber-400/10 border border-amber-400/20"
            >
              <BellRing className="w-3.5 h-3.5" />
            </span>
          )}
        </div>

        {/* Monitor Title & URL */}
        <div className="space-y-1">
          <h3 className="font-semibold text-base text-white group-hover:text-emerald-400 transition-colors flex items-center gap-1.5">
            <span>{monitor.name}</span>
            <ExternalLink className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-slate-400" />
          </h3>
          <p className="text-xs font-mono text-slate-400 truncate max-w-sm" title={monitor.url}>
            {monitor.url}
          </p>
        </div>

        {/* Incident Alert Banner if Down */}
        {isDown && activeIncident && (
          <div className="mt-3 p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2">
            <AlertOctagon className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <div className="truncate">
              <span className="font-semibold">Incident: </span>
              <span>{activeIncident.cause}</span>
            </div>
          </div>
        )}

        {/* Metric / Ping summary pills */}
        <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
          <div className="p-2 rounded-xl bg-slate-950/70 border border-slate-800/80 flex items-center justify-between">
            <span className="text-slate-400 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Interval
            </span>
            <span className="font-medium text-slate-200">{monitor.interval_seconds}s</span>
          </div>

          <div className="p-2 rounded-xl bg-slate-950/70 border border-slate-800/80 flex items-center justify-between">
            <span className="text-slate-400">Response</span>
            {lastCheckResult ? (
              <span
                className={`font-mono font-medium ${
                  lastCheckResult.is_successful ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {lastCheckResult.response_time_ms != null
                  ? `${Math.round(lastCheckResult.response_time_ms)}ms`
                  : 'Fail'}
              </span>
            ) : (
              <span className="font-mono text-slate-400">{monitor.expected_status_code} OK</span>
            )}
          </div>
        </div>
      </div>

      {/* Footer Controls: Check Now & Action Buttons */}
      <div className="mt-5 pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
        <button
          type="button"
          onClick={handleTriggerCheck}
          disabled={isChecking}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-xs font-semibold transition-all disabled:opacity-50"
        >
          {isChecking ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Checking...</span>
            </>
          ) : (
            <>
              <Activity className="w-3.5 h-3.5" />
              <span>Check Now</span>
            </>
          )}
        </button>

        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={handleToggleActive}
            disabled={isToggling}
            aria-label={monitor.is_active ? 'Pause monitor' : 'Resume monitor'}
            title={monitor.is_active ? 'Pause monitor' : 'Resume monitor'}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            {monitor.is_active ? (
              <Pause className="w-4 h-4" />
            ) : (
              <Play className="w-4 h-4 text-emerald-400" />
            )}
          </button>

          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onEdit(monitor);
            }}
            aria-label="Edit monitor"
            title="Edit monitor"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <Edit2 className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={handleDelete}
            aria-label="Delete monitor"
            title="Delete monitor"
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};


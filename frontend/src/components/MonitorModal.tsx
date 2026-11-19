import { useState, useEffect, FormEvent, FC } from 'react';
import { MonitorResponse, MonitorCreate, MonitorUpdate } from '../types/monitor';
import { monitorsApi } from '../api/monitors';
import { X, Loader2, AlertCircle, Radio, BellRing } from 'lucide-react';
import axios from 'axios';

interface MonitorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (monitor: MonitorResponse) => void;
  initialMonitor?: MonitorResponse | null;
}

export const MonitorModal: FC<MonitorModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  initialMonitor,
}) => {
  const isEditing = !!initialMonitor;

  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [method, setMethod] = useState('GET');
  const [intervalSeconds, setIntervalSeconds] = useState(60);
  const [timeoutSeconds, setTimeoutSeconds] = useState(5);
  const [expectedStatusCode, setExpectedStatusCode] = useState(200);
  const [webhookUrl, setWebhookUrl] = useState('');
  const [isActive, setIsActive] = useState(true);

  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (initialMonitor) {
      setName(initialMonitor.name);
      setUrl(initialMonitor.url);
      setMethod(initialMonitor.method);
      setIntervalSeconds(initialMonitor.interval_seconds);
      setTimeoutSeconds(initialMonitor.timeout_seconds);
      setExpectedStatusCode(initialMonitor.expected_status_code);
      setWebhookUrl(initialMonitor.webhook_url || '');
      setIsActive(initialMonitor.is_active);
    } else {
      setName('');
      setUrl('');
      setMethod('GET');
      setIntervalSeconds(60);
      setTimeoutSeconds(5);
      setExpectedStatusCode(200);
      setWebhookUrl('');
      setIsActive(true);
    }
    setError(null);
  }, [initialMonitor, isOpen]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (timeoutSeconds > intervalSeconds) {
      setError('Timeout cannot be greater than the check interval.');
      return;
    }
    if (intervalSeconds < 10) {
      setError('Check interval must be at least 10 seconds.');
      return;
    }
    if (timeoutSeconds < 1) {
      setError('Timeout must be at least 1 second.');
      return;
    }

    setIsSubmitting(true);

    try {
      if (isEditing && initialMonitor) {
        const updatePayload: MonitorUpdate = {
          name,
          url,
          method,
          interval_seconds: intervalSeconds,
          timeout_seconds: timeoutSeconds,
          expected_status_code: expectedStatusCode,
          webhook_url: webhookUrl.trim() ? webhookUrl.trim() : null,
          is_active: isActive,
        };
        const updated = await monitorsApi.updateMonitor(initialMonitor.id, updatePayload);
        onSuccess(updated);
      } else {
        const createPayload: MonitorCreate = {
          name,
          url,
          method,
          interval_seconds: intervalSeconds,
          timeout_seconds: timeoutSeconds,
          expected_status_code: expectedStatusCode,
          webhook_url: webhookUrl.trim() ? webhookUrl.trim() : null,
          is_active: isActive,
        };
        const created = await monitorsApi.createMonitor(createPayload);
        onSuccess(created);
      }
      onClose();
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        if (err.response?.data?.detail) {
          setError(
            typeof err.response.data.detail === 'string'
              ? err.response.data.detail
              : JSON.stringify(err.response.data.detail)
          );
        } else {
          setError('Failed to save monitor. Please check your network connection.');
        }
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto"
    >
      <div className="relative w-full max-w-xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 sm:p-8 space-y-6 my-8 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
              <Radio className="w-5 h-5" />
            </div>
            <div>
              <h2 id="modal-title" className="text-lg font-bold text-white">
                {isEditing ? 'Edit Monitor' : 'Create New Monitor'}
              </h2>
              <p className="text-xs text-slate-400">Configure endpoint uptime checking & alerting</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close modal"
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div
            role="alert"
            className="flex items-center gap-3 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm"
          >
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span className="text-xs sm:text-sm">{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="monitor-name" className="block text-xs font-medium text-slate-300 mb-1">
              Monitor Name *
            </label>
            <input
              id="monitor-name"
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Production Gateway"
              className="w-full px-3.5 py-2 bg-slate-950 border border-slate-700/80 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <div className="sm:col-span-1">
              <label htmlFor="monitor-method" className="block text-xs font-medium text-slate-300 mb-1">
                Method
              </label>
              <select
                id="monitor-method"
                value={method}
                onChange={(e) => setMethod(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700/80 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
                <option value="HEAD">HEAD</option>
                <option value="PATCH">PATCH</option>
              </select>
            </div>

            <div className="sm:col-span-3">
              <label htmlFor="monitor-url" className="block text-xs font-medium text-slate-300 mb-1">
                Endpoint URL *
              </label>
              <input
                id="monitor-url"
                type="url"
                required
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://api.example.com/health"
                className="w-full px-3.5 py-2 bg-slate-950 border border-slate-700/80 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label htmlFor="monitor-interval" className="block text-xs font-medium text-slate-300 mb-1">
                Interval (seconds)
              </label>
              <input
                id="monitor-interval"
                type="number"
                min={10}
                required
                value={intervalSeconds}
                onChange={(e) => setIntervalSeconds(Number(e.target.value))}
                className="w-full px-3.5 py-2 bg-slate-950 border border-slate-700/80 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label htmlFor="monitor-timeout" className="block text-xs font-medium text-slate-300 mb-1">
                Timeout (seconds)
              </label>
              <input
                id="monitor-timeout"
                type="number"
                min={1}
                required
                value={timeoutSeconds}
                onChange={(e) => setTimeoutSeconds(Number(e.target.value))}
                className="w-full px-3.5 py-2 bg-slate-950 border border-slate-700/80 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label htmlFor="monitor-status" className="block text-xs font-medium text-slate-300 mb-1">
                Expected Status
              </label>
              <input
                id="monitor-status"
                type="number"
                required
                value={expectedStatusCode}
                onChange={(e) => setExpectedStatusCode(Number(e.target.value))}
                className="w-full px-3.5 py-2 bg-slate-950 border border-slate-700/80 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>

          {/* Webhook Alerting URL */}
          <div>
            <label htmlFor="monitor-webhook" className="block text-xs font-medium text-slate-300 mb-1">
              <span className="flex items-center gap-1.5">
                <BellRing className="w-3.5 h-3.5 text-amber-400" />
                <span>Incident Webhook URL (Optional)</span>
              </span>
            </label>
            <input
              id="monitor-webhook"
              type="url"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder="https://hooks.slack.com/services/... or Discord webhook"
              className="w-full px-3.5 py-2 bg-slate-950 border border-slate-700/80 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <p className="mt-1 text-[11px] text-slate-400">
              Notified automatically on incident trigger and resolution.
            </p>
          </div>

          {/* Active Status Toggle */}
          <div className="flex items-center gap-3 pt-2">
            <input
              id="monitor-active"
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="w-4 h-4 rounded text-emerald-500 bg-slate-950 border-slate-700 focus:ring-emerald-500 focus:ring-offset-slate-900"
            />
            <label htmlFor="monitor-active" className="text-xs font-medium text-slate-300">
              Active (scheduled background monitoring enabled)
            </label>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800 text-sm font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-2 px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 text-sm font-semibold transition-colors shadow-md shadow-emerald-500/20"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <span>{isEditing ? 'Update Monitor' : 'Create Monitor'}</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};


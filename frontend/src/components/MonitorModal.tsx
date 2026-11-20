import { useState, useEffect, FormEvent, FC } from 'react';
import { toast } from 'sonner';
import { MonitorResponse, MonitorCreate, MonitorUpdate } from '../types/monitor';
import { monitorsApi } from '../api/monitors';
import {
  X,
  Loader2,
  AlertCircle,
  Radio,
  BellRing,
  ArrowRight,
  ArrowLeft,
  Check,
  CheckCircle2,
  Clock,
  Timer,
  Globe,
} from 'lucide-react';
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
  const [step, setStep] = useState<1 | 2 | 3>(1);

  // Form State
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
    setStep(1);
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

  const validateStep1 = () => {
    if (!name.trim()) {
      setError('Monitor name is required.');
      return false;
    }
    if (!url.trim()) {
      setError('Endpoint URL is required.');
      return false;
    }
    try {
      new URL(url);
    } catch {
      setError('Please provide a valid HTTP or HTTPS endpoint URL.');
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
    if (timeoutSeconds > intervalSeconds) {
      setError('Timeout cannot be greater than the check interval.');
      return false;
    }
    if (intervalSeconds < 10) {
      setError('Check interval must be at least 10 seconds.');
      return false;
    }
    if (timeoutSeconds < 1) {
      setError('Timeout must be at least 1 second.');
      return false;
    }
    if (webhookUrl.trim()) {
      try {
        new URL(webhookUrl.trim());
      } catch {
        setError('Webhook URL must be a valid HTTP or HTTPS URL.');
        return false;
      }
    }
    return true;
  };

  const handleNext = () => {
    setError(null);
    if (step === 1) {
      if (validateStep1()) setStep(2);
    } else if (step === 2) {
      if (validateStep2()) setStep(3);
    }
  };

  const handleBack = () => {
    setError(null);
    if (step === 3) setStep(2);
    else if (step === 2) setStep(1);
  };

  const handleSubmit = async (e?: FormEvent) => {
    if (e) e.preventDefault();
    setError(null);

    if (!validateStep1() || !validateStep2()) {
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
        toast.success(`Monitor "${name}" updated`, {
          description: `Interval: ${intervalSeconds}s • Method: ${method}`,
        });
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
        toast.success(`Monitor "${name}" deployed`, {
          description: `Tracking ${url} every ${intervalSeconds}s`,
        });
      }
      onClose();
    } catch (err: unknown) {
      let errMsg = 'Failed to save monitor. Please check your network connection.';
      if (axios.isAxiosError(err)) {
        if (err.response?.data?.detail) {
          errMsg =
            typeof err.response.data.detail === 'string'
              ? err.response.data.detail
              : JSON.stringify(err.response.data.detail);
        }
      }
      setError(errMsg);
      toast.error(isEditing ? 'Failed to update monitor' : 'Failed to deploy monitor', {
        description: errMsg,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto"
    >
      <div className="relative w-full max-w-xl surface-card rounded-2xl p-6 sm:p-8 space-y-6 my-8 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
              <Radio className="w-5 h-5" />
            </div>
            <div>
              <h2 id="modal-title" className="text-base sm:text-lg font-bold text-white tracking-tight">
                {isEditing ? 'Configure Monitor' : 'Create New Monitor'}
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Guided Observability Setup (Step {step} of 3)
              </p>
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

        {/* Guided Step Indicator (Section 14) */}
        <div className="flex items-center justify-between px-2 text-xs font-mono">
          <div
            className={`flex items-center gap-2 ${step >= 1 ? 'text-emerald-400 font-bold' : 'text-slate-600'
              }`}
          >
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${step >= 1 ? 'bg-emerald-500/20 border border-emerald-500/40 text-emerald-300' : 'bg-slate-800 text-slate-500'}`}>
              1
            </span>
            <span>API Target</span>
          </div>

          <div className={`h-[1px] flex-1 mx-3 ${step >= 2 ? 'bg-emerald-500/40' : 'bg-slate-800'}`} />

          <div
            className={`flex items-center gap-2 ${step >= 2 ? 'text-emerald-400 font-bold' : 'text-slate-600'
              }`}
          >
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${step >= 2 ? 'bg-emerald-500/20 border border-emerald-500/40 text-emerald-300' : 'bg-slate-800 text-slate-500'}`}>
              2
            </span>
            <span>Health Rules</span>
          </div>

          <div className={`h-[1px] flex-1 mx-3 ${step === 3 ? 'bg-emerald-500/40' : 'bg-slate-800'}`} />

          <div
            className={`flex items-center gap-2 ${step === 3 ? 'text-emerald-400 font-bold' : 'text-slate-600'
              }`}
          >
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${step === 3 ? 'bg-emerald-500/20 border border-emerald-500/40 text-emerald-300' : 'bg-slate-800 text-slate-500'}`}>
              3
            </span>
            <span>Review</span>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div
            role="alert"
            className="flex items-center gap-3 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs sm:text-sm"
          >
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form Content by Step */}
        <div className="space-y-4">
          {/* STEP 1: API Target */}
          {step === 1 && (
            <div className="space-y-4 animate-in fade-in duration-150">
              <div>
                <label htmlFor="monitor-name" className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase font-mono">
                  Monitor Name *
                </label>
                <input
                  id="monitor-name"
                  type="text"
                  required
                  autoFocus
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Production Auth Gateway"
                  className="w-full px-3.5 py-2.5 bg-[#080d19] border border-slate-700/80 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-sans"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <div className="sm:col-span-1">
                  <label htmlFor="monitor-method" className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase font-mono">
                    Method
                  </label>
                  <select
                    id="monitor-method"
                    value={method}
                    onChange={(e) => setMethod(e.target.value)}
                    className="w-full px-3 py-2.5 bg-[#080d19] border border-slate-700/80 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono font-semibold"
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
                  <label htmlFor="monitor-url" className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase font-mono">
                    Endpoint URL *
                  </label>
                  <input
                    id="monitor-url"
                    type="url"
                    required
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://api.example.com/health"
                    className="w-full px-3.5 py-2.5 bg-[#080d19] border border-slate-700/80 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
                  />
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: Health Rules & Alerting */}
          {step === 2 && (
            <div className="space-y-4 animate-in fade-in duration-150">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label htmlFor="monitor-interval" className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase font-mono">
                    Interval (sec)
                  </label>
                  <input
                    id="monitor-interval"
                    type="number"
                    min={10}
                    required
                    value={intervalSeconds}
                    onChange={(e) => setIntervalSeconds(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-[#080d19] border border-slate-700/80 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
                  />
                  <p className="mt-1 text-[11px] text-slate-500">Min 10 seconds</p>
                </div>

                <div>
                  <label htmlFor="monitor-timeout" className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase font-mono">
                    Timeout (sec)
                  </label>
                  <input
                    id="monitor-timeout"
                    type="number"
                    min={1}
                    required
                    value={timeoutSeconds}
                    onChange={(e) => setTimeoutSeconds(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-[#080d19] border border-slate-700/80 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
                  />
                  <p className="mt-1 text-[11px] text-slate-500">&le; interval</p>
                </div>

                <div>
                  <label htmlFor="monitor-status" className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase font-mono">
                    Expected Code
                  </label>
                  <input
                    id="monitor-status"
                    type="number"
                    required
                    value={expectedStatusCode}
                    onChange={(e) => setExpectedStatusCode(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-[#080d19] border border-slate-700/80 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
                  />
                  <p className="mt-1 text-[11px] text-slate-500">Default: 200</p>
                </div>
              </div>

              {/* Webhook Alerting */}
              <div>
                <label htmlFor="monitor-webhook" className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase font-mono">
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
                  className="w-full px-3.5 py-2.5 bg-[#080d19] border border-slate-700/80 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
                />
                <p className="mt-1 text-[11px] text-slate-400">
                  Dispatches real-time JSON alert payloads on incident trigger and recovery.
                </p>
              </div>

              {/* Active Toggle */}
              <div className="flex items-center gap-3 pt-2">
                <input
                  id="monitor-active"
                  type="checkbox"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="w-4 h-4 rounded text-emerald-500 bg-[#080d19] border-slate-700 focus:ring-emerald-500 focus:ring-offset-[#0e1526]"
                />
                <label htmlFor="monitor-active" className="text-xs font-medium text-slate-300">
                  Active (enable immediate background monitoring schedule)
                </label>
              </div>
            </div>
          )}

          {/* STEP 3: Review Configuration (Section 14) */}
          {step === 3 && (
            <div className="space-y-4 animate-in fade-in duration-150">
              <div className="p-4 rounded-xl bg-[#080d19] border border-slate-800 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-slate-800 text-slate-200">
                      {method}
                    </span>
                    <span className="font-bold text-white text-sm">{name}</span>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${isActive ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'}`}>
                    {isActive ? 'ENABLED' : 'PAUSED'}
                  </span>
                </div>

                <div className="text-xs font-mono text-slate-400 flex items-center gap-2">
                  <Globe className="w-3.5 h-3.5 text-slate-500" />
                  <span className="truncate">{url}</span>
                </div>

                <div className="grid grid-cols-3 gap-2 pt-1 text-xs">
                  <div className="p-2 rounded-lg bg-[#0e1526] border border-slate-800/80">
                    <span className="text-slate-400 flex items-center gap-1 text-[11px]">
                      <Clock className="w-3 h-3 text-slate-500" />
                      Interval
                    </span>
                    <span className="font-mono font-semibold text-slate-200">{intervalSeconds}s</span>
                  </div>

                  <div className="p-2 rounded-lg bg-[#0e1526] border border-slate-800/80">
                    <span className="text-slate-400 flex items-center gap-1 text-[11px]">
                      <Timer className="w-3 h-3 text-slate-500" />
                      Timeout
                    </span>
                    <span className="font-mono font-semibold text-slate-200">{timeoutSeconds}s</span>
                  </div>

                  <div className="p-2 rounded-lg bg-[#0e1526] border border-slate-800/80">
                    <span className="text-slate-400 flex items-center gap-1 text-[11px]">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      Expects
                    </span>
                    <span className="font-mono font-semibold text-slate-200">{expectedStatusCode}</span>
                  </div>
                </div>

                {webhookUrl.trim() && (
                  <div className="p-2.5 rounded-lg bg-[#0e1526] border border-slate-800/80 text-xs">
                    <span className="text-amber-400 font-medium flex items-center gap-1 text-[11px]">
                      <BellRing className="w-3 h-3" />
                      Webhook Notification Enabled
                    </span>
                    <span className="font-mono text-slate-400 text-[11px] truncate block pt-0.5">
                      {webhookUrl}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer Navigation Actions */}
        <div className="flex items-center justify-between gap-3 pt-4 border-t border-white/[0.08]">
          <div>
            {step > 1 && (
              <button
                type="button"
                onClick={handleBack}
                disabled={isSubmitting}
                className="btn-tactile inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800 text-xs font-semibold"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back</span>
              </button>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="btn-tactile px-4 py-2 rounded-xl text-slate-400 hover:text-white text-xs font-medium"
            >
              Cancel
            </button>

            {step < 3 ? (
              <button
                type="button"
                onClick={handleNext}
                className="btn-tactile inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-emerald-400 text-xs font-bold font-mono tracking-wide uppercase border border-emerald-500/20"
              >
                <span>Continue</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                type="button"
                onClick={() => handleSubmit()}
                disabled={isSubmitting}
                className="btn-tactile inline-flex items-center gap-1.5 px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 text-xs font-bold font-mono tracking-wide uppercase shadow-[inset_0_1px_0_0_rgba(255,255,255,0.3),0_4px_12px_rgba(16,185,129,0.3)]"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <Check className="w-3.5 h-3.5" />
                    <span>{isEditing ? 'Update Monitor' : 'Deploy Monitor'}</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

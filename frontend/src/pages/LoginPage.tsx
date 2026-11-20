import { useState, FormEvent, FC } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import { Activity, AlertTriangle, AlertCircle, Loader2 } from 'lucide-react';
import axios from 'axios';

export const LoginPage: FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isRateLimited, setIsRateLimited] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const successMessage = (location.state as { message?: string })?.message;
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/';

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsRateLimited(false);
    setIsSubmitting(true);

    try {
      await login({ email, password });
      toast.success('Welcome back to API Sentinel', {
        description: 'Connected to telemetry engine',
      });
      navigate(from, { replace: true });
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 429) {
          setIsRateLimited(true);
          setError('Too many failed login attempts. Please wait 60 seconds before trying again.');
          toast.error('Rate limited (429)', {
            description: 'Too many attempts. Cooldown period is active.',
          });
        } else if (err.response?.data?.detail) {
          const detail =
            typeof err.response.data.detail === 'string'
              ? err.response.data.detail
              : 'Invalid email or password.';
          setError(detail);
          toast.error('Authentication failed', { description: detail });
        } else {
          setError('Unable to log in. Please check your network connection.');
          toast.error('Connection error');
        }
      } else {
        setError('An unexpected error occurred. Please try again.');
        toast.error('Unexpected error occurred');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#080d19] px-4 py-12">
      <div className="w-full max-w-md space-y-8 surface-card p-8 rounded-2xl">
        {/* Header */}
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-4 shadow-inner">
            <Activity className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">API Sentinel</h1>
          <p className="mt-2 text-sm text-slate-400">Sign in to monitor your services & incidents</p>
        </div>

        {/* Success Alert */}
        {successMessage && (
          <div
            role="status"
            className="flex items-center gap-3 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm"
          >
            <Activity className="w-5 h-5 flex-shrink-0" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Rate Limit Alert */}
        {isRateLimited && (
          <div
            role="alert"
            className="flex items-start gap-3 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-sm"
          >
            <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Rate Limit Exceeded</p>
              <p className="text-xs text-amber-200/80 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Generic Error Alert */}
        {error && !isRateLimited && (
          <div
            role="alert"
            className="flex items-center gap-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm"
          >
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-1.5">
                Email Address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="developer@example.com"
                className="w-full px-4 py-2.5 bg-slate-950 border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all text-sm"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-1.5">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-2.5 bg-slate-950 border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all text-sm"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="btn-tactile w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed text-slate-950 font-semibold text-sm shadow-[inset_0_1px_0_0_rgba(255,255,255,0.3),0_4px_12px_rgba(16,185,129,0.3)]"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Signing in...</span>
              </>
            ) : (
              <span>Sign In</span>
            )}
          </button>
        </form>

        {/* Footer */}
        <div className="text-center text-sm text-slate-400">
          Don't have an account?{' '}
          <Link to="/register" className="text-emerald-400 hover:text-emerald-300 font-medium">
            Register here
          </Link>
        </div>
      </div>
    </div>
  );
};


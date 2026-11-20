import { FC } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { TimeSeriesPoint } from '../types/metrics';

interface LatencyChartProps {
  timeSeries: TimeSeriesPoint[];
  currentWindow: '24h' | '7d' | '30d';
  onWindowChange: (window: '24h' | '7d' | '30d') => void;
  isLoading?: boolean;
}

export const LatencyChart: FC<LatencyChartProps> = ({
  timeSeries,
  currentWindow,
  onWindowChange,
  isLoading = false,
}) => {
  const formatXAxis = (tickItem: string) => {
    try {
      const date = new Date(tickItem);
      if (isNaN(date.getTime())) return tickItem;
      if (currentWindow === '24h') {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
      }
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    } catch {
      return tickItem;
    }
  };

  const chartData = timeSeries.map((pt) => ({
    timestamp: pt.timestamp,
    avgLatency: pt.avg_response_time_ms != null ? Number(pt.avg_response_time_ms.toFixed(2)) : null,
    uptime: pt.uptime_percentage != null ? Number(pt.uptime_percentage.toFixed(1)) : null,
    checks: pt.check_count,
  }));

  const hasData = chartData.some((pt) => pt.avgLatency != null);

  return (
    <div className="surface-card rounded-2xl p-6 space-y-4">
      {/* Top Header & Window Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-bold text-white tracking-tight uppercase font-mono">
            Response Time & Latency Trends
          </h3>
          <p className="text-xs text-slate-400">Sliding window average response time (ms)</p>
        </div>

        <div className="flex items-center p-1 rounded-xl bg-[#080d19] border border-white/[0.08] text-xs font-mono font-medium self-start sm:self-auto">
          {(['24h', '7d', '30d'] as const).map((window) => (
            <button
              key={window}
              type="button"
              onClick={() => onWindowChange(window)}
              className={`btn-tactile px-3 py-1.5 rounded-lg ${
                currentWindow === window
                  ? 'bg-slate-800 text-emerald-400 font-semibold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)]'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {window.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-72 w-full pt-4">
        {isLoading ? (
          <div className="h-full flex items-center justify-center text-slate-500 text-sm">
            Updating metrics graph...
          </div>
        ) : !hasData ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 text-sm gap-2">
            <p>No latency data recorded for this time window.</p>
            <p className="text-xs text-slate-600">Perform manual or scheduled checks to populate charts.</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="latencyGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis
                dataKey="timestamp"
                tickFormatter={formatXAxis}
                stroke="#64748b"
                tick={{ fill: '#64748b', fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: '#334155' }}
              />
              <YAxis
                stroke="#64748b"
                tick={{ fill: '#64748b', fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: '#334155' }}
                unit="ms"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#090d16',
                  borderColor: '#1e293b',
                  borderRadius: '0.75rem',
                  fontSize: '0.75rem',
                  boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)',
                }}
                labelStyle={{ color: '#94a3b8', marginBottom: '0.25rem' }}
                labelFormatter={(label) => {
                  try {
                    return new Date(label).toLocaleString();
                  } catch {
                    return String(label);
                  }
                }}
                formatter={(value: unknown) => [
                  value != null ? `${Number(value).toFixed(2)} ms` : 'No checks recorded',
                  'Avg Latency',
                ]}
              />
              <Area
                type="monotone"
                dataKey="avgLatency"
                stroke="#10b981"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#latencyGradient)"
                connectNulls={true}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};


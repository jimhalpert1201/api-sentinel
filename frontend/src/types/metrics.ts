export interface MetricSummary {
  uptime_percentage: number | null;
  avg_response_time_ms: number | null;
  p50_ms: number | null;
  p95_ms: number | null;
  p99_ms: number | null;
  total_checks: number;
  successful_checks: number;
  failed_checks: number;
}

export interface TimeSeriesPoint {
  timestamp: string;
  uptime_percentage: number | null;
  avg_response_time_ms: number | null;
  check_count: number;
}

export interface MonitorMetricsResponse {
  window: string;
  metrics: MetricSummary;
  time_series: TimeSeriesPoint[];
}


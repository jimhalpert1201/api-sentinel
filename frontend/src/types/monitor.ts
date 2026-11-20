export interface MonitorResponse {
  id: string;
  name: string;
  url: string;
  method: string;
  interval_seconds: number;
  timeout_seconds: number;
  expected_status_code: number;
  is_active: boolean;
  webhook_url?: string | null;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface MonitorCreate {
  name: string;
  url: string;
  method?: string;
  interval_seconds?: number;
  timeout_seconds?: number;
  expected_status_code?: number;
  is_active?: boolean;
  webhook_url?: string | null;
}

export interface MonitorUpdate {
  name?: string;
  url?: string;
  method?: string;
  interval_seconds?: number;
  timeout_seconds?: number;
  expected_status_code?: number;
  is_active?: boolean;
  webhook_url?: string | null;
}

export interface CheckResult {
  id: string;
  monitor_id: string;
  status_code?: number | null;
  response_time_ms?: number | null;
  is_successful: boolean;
  error_message?: string | null;
  checked_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages?: number;
}


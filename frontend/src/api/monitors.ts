import { apiClient } from './client';
import {
  MonitorResponse,
  MonitorCreate,
  MonitorUpdate,
  CheckResult,
  PaginatedResponse,
} from '../types/monitor';
import { MonitorMetricsResponse } from '../types/metrics';

export const monitorsApi = {
  listMonitors: async (skip = 0, limit = 100): Promise<MonitorResponse[]> => {
    const response = await apiClient.get<MonitorResponse[]>('/monitors', {
      params: { skip, limit },
    });
    return response.data;
  },

  getMonitor: async (id: string): Promise<MonitorResponse> => {
    const response = await apiClient.get<MonitorResponse>(`/monitors/${id}`);
    return response.data;
  },

  createMonitor: async (data: MonitorCreate): Promise<MonitorResponse> => {
    const response = await apiClient.post<MonitorResponse>('/monitors', data);
    return response.data;
  },

  updateMonitor: async (id: string, data: MonitorUpdate): Promise<MonitorResponse> => {
    const response = await apiClient.patch<MonitorResponse>(`/monitors/${id}`, data);
    return response.data;
  },

  deleteMonitor: async (id: string): Promise<void> => {
    await apiClient.delete(`/monitors/${id}`);
  },

  triggerCheck: async (id: string): Promise<CheckResult> => {
    const response = await apiClient.post<CheckResult>(`/monitors/${id}/check`);
    return response.data;
  },

  getMetrics: async (id: string, window: '24h' | '7d' | '30d' = '24h'): Promise<MonitorMetricsResponse> => {
    const response = await apiClient.get<MonitorMetricsResponse>(`/monitors/${id}/metrics`, {
      params: { window },
    });
    return response.data;
  },

  getChecks: async (
    id: string,
    page = 1,
    pageSize = 20,
    statusFilter = 'all'
  ): Promise<PaginatedResponse<CheckResult>> => {
    const isSuccessful =
      statusFilter === 'passed' ? true : statusFilter === 'failed' ? false : undefined;
    const response = await apiClient.get<PaginatedResponse<CheckResult>>(`/monitors/${id}/checks`, {
      params: {
        page,
        page_size: pageSize,
        ...(isSuccessful !== undefined ? { is_successful: isSuccessful } : {}),
      },
    });
    return response.data;
  },
};


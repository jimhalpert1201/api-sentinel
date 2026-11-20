import { apiClient } from './client';
import { IncidentResponse, IncidentEvent } from '../types/incident';

export const incidentsApi = {
  listIncidents: async (params?: {
    skip?: number;
    limit?: number;
    monitor_id?: string;
    status?: string;
  }): Promise<IncidentResponse[]> => {
    const response = await apiClient.get<IncidentResponse[]>('/incidents', { params });
    return response.data;
  },

  getIncident: async (id: string): Promise<IncidentResponse> => {
    const response = await apiClient.get<IncidentResponse>(`/incidents/${id}`);
    return response.data;
  },

  acknowledgeIncident: async (id: string, notes?: string): Promise<IncidentResponse> => {
    const response = await apiClient.patch<IncidentResponse>(`/incidents/${id}/acknowledge`, {
      description: notes || undefined,
    });
    return response.data;
  },

  getIncidentEvents: async (id: string): Promise<IncidentEvent[]> => {
    const response = await apiClient.get<IncidentEvent[]>(`/incidents/${id}/events`);
    return response.data;
  },
};


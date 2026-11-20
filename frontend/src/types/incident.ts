export type IncidentStatus = 'open' | 'acknowledged' | 'resolved';
export type IncidentSeverity = 'critical' | 'major' | 'minor';

export interface IncidentResponse {
  id: string;
  monitor_id: string;
  status: IncidentStatus;
  severity: IncidentSeverity;
  cause: string;
  started_at: string;
  acknowledged_at?: string | null;
  resolved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface IncidentEvent {
  id: string;
  incident_id: string;
  event_type: string;
  description: string;
  message?: string;
  created_at: string;
}


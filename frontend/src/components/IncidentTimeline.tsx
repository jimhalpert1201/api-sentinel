import { useState, useEffect, FC } from 'react';
import { IncidentEvent } from '../types/incident';
import { incidentsApi } from '../api/incidents';
import { AlertCircle, CheckCircle2, Clock, Loader2, MessageSquare } from 'lucide-react';

interface IncidentTimelineProps {
  incidentId: string;
}

export const IncidentTimeline: FC<IncidentTimelineProps> = ({ incidentId }) => {
  const [events, setEvents] = useState<IncidentEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const fetchEvents = async () => {
      setIsLoading(true);
      try {
        const data = await incidentsApi.getIncidentEvents(incidentId);
        if (isMounted) setEvents(data);
      } catch (err) {
        console.error('Failed to load incident events:', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };
    fetchEvents();
    return () => {
      isMounted = false;
    };
  }, [incidentId]);

  if (isLoading) {
    return (
      <div className="py-6 flex items-center justify-center text-slate-500 gap-2 text-xs">
        <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-500" />
        <span>Loading incident audit trail...</span>
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="py-4 text-center text-slate-500 text-xs">
        No event history logged for this incident yet.
      </div>
    );
  }

  return (
    <div className="space-y-4 pt-2">
      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
        Audit & Notification Timeline
      </h4>
      <div className="relative border-l border-slate-800 ml-3 space-y-4">
        {events.map((evt) => {
          const isTrigger =
            evt.event_type.includes('triggered') || evt.event_type.includes('created');
          const isAck = evt.event_type.includes('acknowledged');
          const isResolved = evt.event_type.includes('resolved');

          return (
            <div key={evt.id} className="relative pl-6">
              {/* Event bullet icon */}
              <div
                className={`absolute -left-3 top-0.5 w-6 h-6 rounded-full flex items-center justify-center text-xs border ${
                  isResolved
                    ? 'bg-emerald-950 border-emerald-500 text-emerald-400'
                    : isAck
                    ? 'bg-amber-950 border-amber-500 text-amber-400'
                    : isTrigger
                    ? 'bg-rose-950 border-rose-500 text-rose-400'
                    : 'bg-slate-900 border-slate-700 text-slate-400'
                }`}
              >
                {isResolved ? (
                  <CheckCircle2 className="w-3.5 h-3.5" />
                ) : isAck ? (
                  <MessageSquare className="w-3.5 h-3.5" />
                ) : isTrigger ? (
                  <AlertCircle className="w-3.5 h-3.5" />
                ) : (
                  <Clock className="w-3.5 h-3.5" />
                )}
              </div>

              {/* Event details */}
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-semibold text-slate-200 capitalize">
                    {evt.event_type.replace(/_/g, ' ')}
                  </span>
                  <span className="text-[11px] font-mono text-slate-400">
                    {new Date(evt.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-mono bg-slate-950/60 p-2 rounded-lg border border-slate-800/80">
                  {evt.description || evt.message || 'No details provided'}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};


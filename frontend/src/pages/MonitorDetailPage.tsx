import { FC } from 'react';
import { useParams } from 'react-router-dom';

export const MonitorDetailPage: FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Monitor Details</h1>
      <p className="text-slate-400">Loading monitor: {id}</p>
    </div>
  );
};

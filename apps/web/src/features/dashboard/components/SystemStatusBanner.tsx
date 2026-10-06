import React from 'react';
import { SystemHealth } from '../../../types/api';
import { Badge } from '../../../components/ui/Badge';

export interface SystemStatusBannerProps {
  health: SystemHealth | null;
  online: boolean;
  className?: string;
}

export const SystemStatusBanner: React.FC<SystemStatusBannerProps> = ({
  health,
  online,
  className = '',
}) => {
  return (
    <div
      className={`px-3.5 py-2 bg-ops-panel border border-ops-border rounded-xs flex items-center justify-between text-xs text-txt-secondary ${className}`}
    >
      <div className="flex items-center space-x-2.5">
        <span
          className={`w-2 h-2 rounded-full ${
            online ? 'bg-forest' : 'bg-danger'
          }`}
        />
        <div className="flex items-center space-x-2 font-mono text-[11px]">
          <span className="font-semibold text-txt-primary uppercase tracking-wider">System Pipeline:</span>
          <span className="text-txt-secondary">
            {online ? `FastAPI v${health?.version || '0.1.0'}` : 'Offline Fallback'}
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-2 font-mono text-[10px]">
        <Badge variant={health?.services?.database === 'connected' ? 'success' : 'neutral'} size="sm">
          PostGIS: {health?.services?.database || 'disconnected'}
        </Badge>
        <Badge variant={health?.services?.redis === 'connected' ? 'success' : 'neutral'} size="sm">
          Redis: {health?.services?.redis || 'disconnected'}
        </Badge>
        <Badge
          variant={health?.services?.celery_broker === 'connected' ? 'success' : 'neutral'}
          size="sm"
        >
          Celery: {health?.services?.celery_broker || 'disconnected'}
        </Badge>
      </div>
    </div>
  );
};

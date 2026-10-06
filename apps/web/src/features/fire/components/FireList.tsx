import React from 'react';
import { FireHotspotProperties } from '../../../types/domain';
import { Badge } from '../../../components/ui/Badge';
import { EmptyState } from '../../../components/feedback/EmptyState';
import { Skeleton } from '../../../components/feedback/Skeleton';
import { FlameIcon } from '../../../components/common/Icons';

export interface FireListProps {
  fires: FireHotspotProperties[];
  selectedFireId?: string | null;
  onSelectFire: (fire: FireHotspotProperties) => void;
  isLoading?: boolean;
}

export const FireList: React.FC<FireListProps> = ({
  fires,
  selectedFireId,
  onSelectFire,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="space-y-2 p-3">
        <Skeleton className="h-12 w-full" count={4} />
      </div>
    );
  }

  if (fires.length === 0) {
    return (
      <div className="p-4">
        <EmptyState
          title="No Active Fires"
          description="No thermal hotspot detections found within the observation window."
        />
      </div>
    );
  }

  return (
    <div className="divide-y divide-ops-border overflow-y-auto">
      {fires.map((fire) => {
        const isSelected = fire.id === selectedFireId;
        const confidenceBadgeVariant =
          fire.confidence === 'high'
            ? 'danger'
            : fire.confidence === 'nominal'
            ? 'warning'
            : 'neutral';

        return (
          <div
            key={fire.id}
            onClick={() => onSelectFire(fire)}
            className={`p-3 cursor-pointer transition-colors ${
              isSelected
                ? 'bg-ops-surface border-l-2 border-amber'
                : 'hover:bg-ops-surface/50 border-l-2 border-transparent'
            }`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="font-medium text-xs text-txt-primary flex items-center space-x-1.5">
                <FlameIcon className="w-3.5 h-3.5 text-amber" />
                <span className="font-mono text-[11px]">{fire.satellite || 'SATELLITE'}</span>
              </span>
              <Badge variant={confidenceBadgeVariant} size="sm">
                {fire.confidence?.toUpperCase() || 'NOMINAL'}
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-1.5 text-[11px] font-mono mt-1">
              <div>
                <span className="text-txt-muted mr-1">FRP:</span>
                <span className="text-amber font-semibold">
                  {fire.frp_mw !== null ? `${fire.frp_mw.toFixed(1)} MW` : 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-txt-muted mr-1">Temp:</span>
                <span className="text-txt-secondary">
                  {fire.brightness_temperature_kelvin !== null
                    ? `${fire.brightness_temperature_kelvin.toFixed(1)} K`
                    : 'N/A'}
                </span>
              </div>
              <div className="col-span-2 text-[10px] text-txt-muted truncate pt-0.5">
                Obs: {new Date(fire.detection_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} UTC
                {fire.latitude !== undefined && fire.longitude !== undefined && (
                  <span className="ml-2 text-txt-muted">
                    ({fire.latitude.toFixed(3)}°, {fire.longitude.toFixed(3)}°)
                  </span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

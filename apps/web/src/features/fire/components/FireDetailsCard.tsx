import React from 'react';
import { FireHotspotProperties } from '../../../types/domain';
import { Badge } from '../../../components/ui/Badge';
import { TargetIcon } from '../../../components/common/Icons';

export interface FireDetailsCardProps {
  fire: FireHotspotProperties | null;
  onClose: () => void;
  onSimulateFromFire?: (fire: FireHotspotProperties) => void;
  className?: string;
}

export const FireDetailsCard: React.FC<FireDetailsCardProps> = ({
  fire,
  onClose,
  onSimulateFromFire,
  className = '',
}) => {
  if (!fire) return null;

  return (
    <div
      className={`bg-ops-panel border border-ops-border rounded-xs p-3.5 shadow-2xl text-xs space-y-2.5 ${className}`}
    >
      <div className="flex items-center justify-between pb-2 border-b border-ops-border bg-ops-subtle -mx-3.5 -mt-3.5 p-3 rounded-t-xs">
        <div>
          <h4 className="font-semibold text-txt-primary uppercase tracking-wider font-mono text-[11px]">Hotspot Telemetry</h4>
          <span className="text-[10px] font-mono text-txt-muted">ID: {fire.id}</span>
        </div>
        <button
          onClick={onClose}
          className="text-txt-muted hover:text-txt-primary text-xs p-1 rounded-xs hover:bg-ops-surface"
          aria-label="Close details"
        >
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div className="space-y-1.5 font-mono text-[11px] text-txt-secondary">
        <div className="flex justify-between items-center py-0.5 border-b border-ops-border">
          <span className="text-txt-muted">Sensor:</span>
          <Badge variant="neutral" size="sm">{fire.satellite || 'MODIS/VIIRS'}</Badge>
        </div>
        <div className="flex justify-between items-center py-0.5 border-b border-ops-border">
          <span className="text-txt-muted">Confidence:</span>
          <Badge
            variant={fire.confidence === 'high' ? 'danger' : 'warning'}
            size="sm"
          >
            {fire.confidence?.toUpperCase() || 'NOMINAL'}
          </Badge>
        </div>
        <div className="flex justify-between items-center py-0.5 border-b border-ops-border">
          <span className="text-txt-muted">Coordinates:</span>
          <span className="text-txt-primary">
            {fire.latitude !== undefined && fire.longitude !== undefined
              ? `${fire.latitude.toFixed(4)}°N, ${fire.longitude.toFixed(4)}°E`
              : 'Point geometry'}
          </span>
        </div>
        <div className="flex justify-between items-center py-0.5 border-b border-ops-border">
          <span className="text-txt-muted">Radiative Power:</span>
          <span className="font-bold text-amber">
            {fire.frp_mw !== null ? `${fire.frp_mw.toFixed(1)} MW` : 'N/A'}
          </span>
        </div>
        <div className="flex justify-between items-center py-0.5 border-b border-ops-border">
          <span className="text-txt-muted">Brightness Temp:</span>
          <span className="text-txt-primary">
            {fire.brightness_temperature_kelvin !== null
              ? `${fire.brightness_temperature_kelvin.toFixed(1)} K`
              : 'N/A'}
          </span>
        </div>
        <div className="flex justify-between items-center py-0.5">
          <span className="text-txt-muted">Observed:</span>
          <span className="text-txt-secondary">
            {new Date(fire.detection_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} UTC
          </span>
        </div>
      </div>

      <div className="pt-2 border-t border-ops-border flex items-center space-x-2">
        {onSimulateFromFire && (
          <button
            className="flex-1 py-1.5 px-2.5 rounded-xs bg-forest hover:bg-forest-light text-txt-primary font-semibold text-[11px] transition-colors flex items-center justify-center space-x-1.5"
            onClick={() => onSimulateFromFire(fire)}
          >
            <TargetIcon className="w-3.5 h-3.5" />
            <span>Simulate Spread</span>
          </button>
        )}
        <button
          className="py-1.5 px-2.5 rounded-xs bg-ops-surface hover:bg-ops-panel text-txt-secondary border border-ops-border text-[11px] transition-colors"
          onClick={onClose}
        >
          Dismiss
        </button>
      </div>
    </div>
  );
};

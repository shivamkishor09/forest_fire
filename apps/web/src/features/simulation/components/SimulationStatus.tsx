import React from 'react';
import { SimulationJob, SimulationDetail } from '../../../types/domain';
import { Badge } from '../../../components/ui/Badge';

export interface SimulationStatusProps {
  job: SimulationJob | null;
  detail: SimulationDetail | null;
  className?: string;
}

export const SimulationStatus: React.FC<SimulationStatusProps> = ({
  job,
  detail,
  className = '',
}) => {
  if (!job && !detail) return null;

  const status = detail?.status || job?.status || 'QUEUED';
  const badgeVariant =
    status === 'COMPLETED'
      ? 'success'
      : status === 'RUNNING'
      ? 'warning'
      : status === 'FAILED'
      ? 'danger'
      : 'info';

  const progressPct = detail?.progress_pct ?? (status === 'COMPLETED' ? 100 : status === 'RUNNING' ? 50 : 10);
  const completedSteps = detail?.completed_steps;
  const totalSteps = detail?.total_steps;

  return (
    <div
      className={`bg-ops-panel border border-ops-border rounded-xs p-3.5 text-xs space-y-3 ${className}`}
    >
      <div className="flex items-center justify-between pb-2 border-b border-ops-border font-mono text-[11px] uppercase tracking-wider">
        <span className="font-semibold text-txt-primary">Execution Status</span>
        <Badge variant={badgeVariant} size="sm">
          {status}
        </Badge>
      </div>

      {/* Progress Bar for Active Jobs */}
      {(status === 'RUNNING' || status === 'QUEUED') && (
        <div className="space-y-1.5">
          <div className="flex justify-between text-[10px] text-txt-muted font-mono uppercase">
            <span>Progress:</span>
            <span>
              {completedSteps !== undefined && totalSteps !== undefined
                ? `Step ${completedSteps}/${totalSteps} (${progressPct.toFixed(0)}%)`
                : `${progressPct.toFixed(0)}%`}
            </span>
          </div>
          <div className="w-full bg-ops-bg h-1.5 rounded-xs overflow-hidden">
            <div
              className={`h-full transition-all duration-500 rounded-xs ${
                status === 'RUNNING' ? 'bg-forest' : 'bg-ops-surface'
              }`}
              style={{ width: `${Math.max(5, Math.min(100, progressPct))}%` }}
            />
          </div>
        </div>
      )}

      {/* Identifiers & Timing */}
      <div className="space-y-1 font-mono text-[11px] text-txt-muted">
        <div className="flex justify-between">
          <span className="uppercase text-[10px]">Job ID:</span>
          <span className="text-txt-primary truncate max-w-[140px]">
            {detail?.id || job?.simulation_id}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="uppercase text-[10px]">Horizon:</span>
          <span className="text-txt-primary">
            {detail?.duration_hours || job?.duration_hours || 12}h
          </span>
        </div>
        {detail?.engine_version && (
          <div className="flex justify-between">
            <span className="uppercase text-[10px]">Engine:</span>
            <span className="text-txt-secondary">{detail.engine_version}</span>
          </div>
        )}
      </div>

      {/* Completed Summary Metrics */}
      {status === 'COMPLETED' && detail?.metrics && (
        <div className="p-2.5 rounded-xs bg-ops-bg border border-ops-border space-y-1.5 font-mono text-[11px]">
          <div className="text-[10px] font-semibold text-txt-primary uppercase tracking-wider">
            Run Telemetry
          </div>
          <div className="flex justify-between">
            <span className="text-txt-muted">Total Burned:</span>
            <span className="text-danger font-semibold">
              {detail.metrics.total_area_burned_ha.toFixed(1)} ha
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-txt-muted">Peak Velocity:</span>
            <span className="text-amber font-semibold">
              {detail.metrics.peak_spread_velocity_kmh.toFixed(2)} km/h
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-txt-muted">Spread Dir:</span>
            <span className="text-txt-primary">
              {detail.metrics.dominant_spread_direction_deg.toFixed(0)}°
            </span>
          </div>
        </div>
      )}

      {/* Error alert */}
      {detail?.error_message && (
        <div className="text-danger text-[10px] p-2 bg-danger/10 border border-danger/40 rounded-xs font-mono">
          Error: {detail.error_message}
        </div>
      )}
    </div>
  );
};


import React from 'react';
import { SimulationStepProperties } from '../../../types/domain';
import { GeoJSONFeatureCollection, MultiPolygonGeometry } from '../../../types/geo';
import { BarChartIcon } from '../../../components/common/Icons';

export interface SimulationMetricChartProps {
  stepsData: GeoJSONFeatureCollection<MultiPolygonGeometry, SimulationStepProperties> | null;
  currentStepIndex: number;
  onSelectStep?: (index: number) => void;
  className?: string;
}

export const SimulationMetricChart: React.FC<SimulationMetricChartProps> = ({
  stepsData,
  currentStepIndex,
  onSelectStep,
  className = '',
}) => {
  const steps = stepsData?.features || [];

  if (steps.length === 0) {
    return (
      <div
        className={`bg-ops-panel border border-ops-border rounded-xs p-3.5 text-xs ${className}`}
      >
        <div className="flex items-center justify-between pb-2 border-b border-ops-border font-mono text-[11px] uppercase tracking-wider">
          <span className="font-semibold text-txt-primary">Spread Analytics</span>
          <span className="text-[10px] text-txt-muted font-mono">12h Run</span>
        </div>
        <p className="py-4 text-center text-txt-muted text-[11px] font-mono">
          Run or load a simulation to view cumulative burned area.
        </p>
      </div>
    );
  }

  // Calculate maximum values for scaling
  const maxArea = Math.max(...steps.map((s) => s.properties.cumulative_burned_area_ha || 0), 10);
  const maxVelocity = Math.max(...steps.map((s) => s.properties.spread_velocity_kmh || 0), 1);

  const selectedStep = steps[currentStepIndex]?.properties;

  return (
    <div
      className={`bg-ops-panel border border-ops-border rounded-xs p-3.5 text-xs ${className}`}
    >
      <div className="flex items-center justify-between pb-2 border-b border-ops-border mb-3 font-mono text-[11px] uppercase tracking-wider">
        <div className="flex items-center space-x-1.5">
          <BarChartIcon className="w-4 h-4 text-amber" />
          <span className="text-txt-primary font-semibold">Spread Metrics</span>
          <span className="text-[10px] text-txt-muted">
            ({steps.length} Timesteps)
          </span>
        </div>
        {selectedStep && (
          <div className="flex items-center space-x-3 text-[11px] font-mono">
            <span className="text-danger font-semibold">
              {selectedStep.cumulative_burned_area_ha.toFixed(1)} ha
            </span>
            {selectedStep.spread_velocity_kmh !== undefined && (
              <span className="text-amber font-semibold">
                {selectedStep.spread_velocity_kmh.toFixed(1)} km/h
              </span>
            )}
          </div>
        )}
      </div>

      {/* Legend & Instructions */}
      <div className="flex items-center justify-between text-[10px] text-txt-muted mb-2 px-1 font-mono">
        <div className="flex items-center space-x-3">
          <span className="flex items-center space-x-1">
            <span className="w-2.5 h-2.5 rounded-xs bg-danger inline-block" />
            <span className="uppercase">Area (ha)</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-amber inline-block" />
            <span className="uppercase">Rate (km/h)</span>
          </span>
        </div>
        <span className="text-txt-muted hidden sm:inline">Select bar to inspect</span>
      </div>

      {/* Responsive Bar & Point Visualizer */}
      <div className="h-32 flex items-end space-x-1.5 pt-3 pb-1 px-1 bg-ops-bg rounded-xs border border-ops-border">
        {steps.map((step, idx) => {
          const props = step.properties;
          const area = props.cumulative_burned_area_ha || 0;
          const velocity = props.spread_velocity_kmh || 0;

          const areaPct = Math.min(100, Math.max(8, (area / maxArea) * 100));
          const velocityPct = Math.min(100, Math.max(5, (velocity / maxVelocity) * 100));
          const isSelected = idx === currentStepIndex;

          const hourLabel =
            props.step_hour !== undefined
              ? `T+${props.step_hour}h`
              : props.elapsed_minutes !== undefined
              ? `T+${Math.round(props.elapsed_minutes / 60)}h`
              : `S${props.step_number}`;

          return (
            <button
              key={idx}
              onClick={() => onSelectStep?.(idx)}
              className={`flex-1 h-full flex flex-col justify-end items-center group relative focus:outline-none transition-all ${
                isSelected ? 'opacity-100' : 'opacity-60 hover:opacity-100'
              }`}
              title={`${hourLabel}: ${area.toFixed(1)} ha, ${velocity.toFixed(1)} km/h`}
              aria-label={`Step ${idx}: ${hourLabel}`}
            >
              {/* Selected indicator marker */}
              {isSelected && (
                <div className="absolute -top-1 w-full flex justify-center">
                  <div className="w-1.5 h-1.5 bg-amber rounded-full" />
                </div>
              )}

              {/* Bar column */}
              <div className="w-full max-w-[20px] relative flex flex-col justify-end items-center h-full">
                {/* Area Bar */}
                <div
                  style={{ height: `${areaPct}%` }}
                  className={`w-full rounded-t-xs transition-all ${
                    isSelected
                      ? 'bg-danger'
                      : 'bg-danger/60 group-hover:bg-danger'
                  }`}
                />

                {/* Velocity Marker Dot */}
                <div
                  style={{ bottom: `${velocityPct}%` }}
                  className={`absolute w-1.5 h-1.5 rounded-full border border-ops-bg pointer-events-none transition-all ${
                    isSelected
                      ? 'bg-amber ring-1 ring-amber'
                      : 'bg-amber'
                  }`}
                />
              </div>

              {/* Step Label */}
              <span
                className={`text-[9px] font-mono mt-1 ${
                  isSelected ? 'text-amber font-semibold' : 'text-txt-muted group-hover:text-txt-secondary'
                }`}
              >
                {hourLabel}
              </span>
            </button>
          );
        })}
      </div>

      {/* Axis Summary Footer */}
      <div className="mt-2 flex justify-between items-center text-[10px] font-mono text-txt-muted px-1">
        <span>Max Area: {maxArea.toFixed(1)} ha</span>
        <span>Peak: {maxVelocity.toFixed(1)} km/h</span>
      </div>
    </div>
  );
};


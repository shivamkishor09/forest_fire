import React, { useState } from 'react';
import { Button } from '../../../components/ui/Button';
import { SlidersIcon, WindIcon, RotateCcwIcon, ChevronDownIcon, ChevronUpIcon } from '../../../components/common/Icons';

export interface SimulationControlsProps {
  durationHours: number;
  onDurationChange: (hours: number) => void;
  stepMinutes: number;
  onStepMinutesChange: (minutes: number) => void;
  windSpeedMs?: number;
  onWindSpeedChange?: (speed: number) => void;
  windDirectionDeg?: number;
  onWindDirectionChange?: (deg: number) => void;
  fuelType?: string;
  onFuelTypeChange?: (fuel: string) => void;
  hasIgnition: boolean;
  isSubmitting?: boolean;
  onStartSimulation: () => void;
  onClearIgnition?: () => void;
  hasCompletedSimulation?: boolean;
  onReplaySimulation?: () => void;
  className?: string;
}

function getCardinalDirection(deg: number): string {
  const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
  const index = Math.round((deg % 360) / 45) % 8;
  return directions[index];
}

export const SimulationControls: React.FC<SimulationControlsProps> = ({
  durationHours,
  onDurationChange,
  stepMinutes,
  onStepMinutesChange,
  windSpeedMs = 7.5,
  onWindSpeedChange,
  windDirectionDeg = 225,
  onWindDirectionChange,
  fuelType = 'CONIFER_HIGH_FLAMMABILITY',
  onFuelTypeChange,
  hasIgnition,
  isSubmitting = false,
  onStartSimulation,
  onClearIgnition,
  hasCompletedSimulation = false,
  onReplaySimulation,
  className = '',
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const windKmh = (windSpeedMs * 3.6).toFixed(1);

  return (
    <div
      className={`bg-ops-panel border border-ops-border rounded-xs p-3.5 text-xs space-y-3.5 ${className}`}
    >
      <div className="font-semibold text-txt-primary pb-2 border-b border-ops-border flex items-center justify-between font-mono text-[11px] uppercase tracking-wider">
        <span className="flex items-center space-x-1.5">
          <SlidersIcon className="w-3.5 h-3.5 text-amber" />
          <span>Simulation Parameters</span>
        </span>
        <span className="text-[10px] text-txt-muted">Cellular Automata</span>
      </div>

      {/* Duration Selector */}
      <div className="space-y-1.5">
        <div className="flex justify-between items-center text-[11px]">
          <span className="text-txt-secondary font-medium uppercase font-mono text-[10px]">Spread Horizon:</span>
          <span className="font-mono font-bold text-amber bg-ops-bg px-2 py-0.5 rounded-xs border border-ops-border">
            {durationHours} Hours
          </span>
        </div>
        <input
          type="range"
          min="1"
          max="12"
          step="1"
          value={durationHours}
          onChange={(e) => onDurationChange(parseInt(e.target.value, 10))}
          className="w-full h-1.5 bg-ops-bg rounded-xs appearance-none cursor-pointer accent-forest"
        />
        <div className="flex justify-between text-[10px] text-txt-muted font-mono">
          <span>1h</span>
          <span>3h</span>
          <span>6h</span>
          <span>9h</span>
          <span>12h Max</span>
        </div>
      </div>

      {/* Step Interval */}
      <div className="space-y-1.5">
        <label className="text-txt-secondary font-medium font-mono text-[10px] uppercase block">
          Perimeter Output Interval:
        </label>
        <div className="grid grid-cols-3 gap-1.5">
          {[15, 30, 60].map((interval) => (
            <button
              key={interval}
              type="button"
              onClick={() => onStepMinutesChange(interval)}
              className={`py-1.5 rounded-xs text-[11px] font-mono font-semibold transition-colors border ${
                stepMinutes === interval
                  ? 'bg-forest/20 border-forest text-txt-primary'
                  : 'bg-ops-bg border-ops-border text-txt-secondary hover:text-txt-primary'
              }`}
            >
              {interval} min
            </button>
          ))}
        </div>
      </div>

      {/* Weather & Environmental Scenario Overrides Toggle */}
      <div className="pt-1 border-t border-ops-border">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="w-full flex items-center justify-between text-[11px] text-txt-secondary hover:text-txt-primary py-1 transition-colors"
        >
          <span className="flex items-center space-x-1.5 font-mono text-[11px] uppercase">
            <WindIcon className="w-3.5 h-3.5 text-txt-muted" />
            <span className="font-medium">Weather & Fuel Overrides</span>
          </span>
          <span className="text-[10px] font-mono text-txt-muted flex items-center space-x-1">
            <span>{showAdvanced ? 'Hide' : 'Configure'}</span>
            {showAdvanced ? <ChevronUpIcon className="w-3 h-3" /> : <ChevronDownIcon className="w-3 h-3" />}
          </span>
        </button>

        {showAdvanced && (
          <div className="mt-2.5 space-y-3 p-2.5 rounded-xs bg-ops-bg border border-ops-border">
            {/* Wind Speed */}
            <div className="space-y-1">
              <div className="flex justify-between text-[10px] font-mono">
                <span className="text-txt-muted uppercase">Wind Speed:</span>
                <span className="text-amber font-semibold">
                  {windSpeedMs} m/s ({windKmh} km/h)
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="25"
                step="0.5"
                value={windSpeedMs}
                onChange={(e) =>
                  onWindSpeedChange && onWindSpeedChange(parseFloat(e.target.value))
                }
                className="w-full h-1 bg-ops-surface rounded appearance-none cursor-pointer accent-forest"
              />
            </div>

            {/* Wind Direction */}
            <div className="space-y-1">
              <div className="flex justify-between text-[10px] font-mono">
                <span className="text-txt-muted uppercase">Wind Direction:</span>
                <span className="text-amber font-semibold">
                  {windDirectionDeg}° ({getCardinalDirection(windDirectionDeg)})
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="360"
                step="15"
                value={windDirectionDeg}
                onChange={(e) =>
                  onWindDirectionChange && onWindDirectionChange(parseInt(e.target.value, 10))
                }
                className="w-full h-1 bg-ops-surface rounded appearance-none cursor-pointer accent-forest"
              />
            </div>

            {/* Fuel Type */}
            <div className="space-y-1">
              <span className="text-[10px] text-txt-muted font-mono uppercase block">Fuel Classification:</span>
              <select
                value={fuelType}
                onChange={(e) => onFuelTypeChange && onFuelTypeChange(e.target.value)}
                className="w-full bg-ops-panel border border-ops-border rounded-xs px-2 py-1 text-[11px] text-txt-primary focus:outline-none focus:border-forest font-mono"
              >
                <option value="CONIFER_HIGH_FLAMMABILITY">Conifer Forest (High)</option>
                <option value="PINE_MODERATE_FLAMMABILITY">Pine Forest (Moderate)</option>
                <option value="DECIDUOUS_LOW_FLAMMABILITY">Deciduous (Low)</option>
                <option value="GRASSLAND_RAPID_SPREAD">Dry Grassland (Rapid)</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="pt-2 space-y-2">
        <Button
          variant="primary"
          size="md"
          className="w-full font-semibold uppercase tracking-wider font-mono text-xs"
          disabled={!hasIgnition || isSubmitting}
          isLoading={isSubmitting}
          onClick={onStartSimulation}
          aria-label="Initialize 12h Simulation"
        >
          {isSubmitting ? 'Dispatching Job...' : 'Initialize 12h Simulation'}
        </Button>

        {hasCompletedSimulation && onReplaySimulation && (
          <Button
            variant="secondary"
            size="sm"
            className="w-full font-mono text-[11px] flex items-center justify-center space-x-1"
            onClick={onReplaySimulation}
          >
            <RotateCcwIcon className="w-3.5 h-3.5" />
            <span>Replay Simulation</span>
          </Button>
        )}

        {hasIgnition && onClearIgnition && (
          <Button
            variant="secondary"
            size="sm"
            className="w-full font-mono text-[10px] text-txt-muted hover:text-danger"
            onClick={onClearIgnition}
            aria-label="Reset Ignition Point"
          >
            Reset Ignition Point
          </Button>
        )}

        {!hasIgnition && (
          <p className="text-[10px] text-amber/90 font-mono text-center mt-1.5">
            Select an ignition point to begin simulation.
          </p>
        )}
      </div>
    </div>
  );
};


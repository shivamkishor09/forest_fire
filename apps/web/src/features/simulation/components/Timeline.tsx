import React from 'react';
import { SimulationStepProperties } from '../../../types/domain';
import { GeoJSONFeatureCollection, MultiPolygonGeometry } from '../../../types/geo';
import { PlayIcon, PauseIcon, SkipBackIcon, SkipForwardIcon, RotateCcwIcon } from '../../../components/common/Icons';

export interface TimelineProps {
  stepsData: GeoJSONFeatureCollection<MultiPolygonGeometry, SimulationStepProperties> | null;
  currentStepIndex: number;
  onSelectStep: (index: number) => void;
  isPlaying: boolean;
  onTogglePlay: () => void;
  onStepForward: () => void;
  onStepBackward: () => void;
  onReplay?: () => void;
  className?: string;
}

export const Timeline: React.FC<TimelineProps> = ({
  stepsData,
  currentStepIndex,
  onSelectStep,
  isPlaying,
  onTogglePlay,
  onStepForward,
  onStepBackward,
  onReplay,
  className = '',
}) => {
  const steps = stepsData?.features || [];
  const hasSteps = steps.length > 0;
  const currentStep = hasSteps ? steps[currentStepIndex]?.properties : null;
  const currentHour = currentStep?.step_hour ?? currentStep?.step_number ?? 0;

  return (
    <div
      className={`bg-ops-panel border border-ops-border rounded-xs p-3.5 shadow-2xl text-xs select-none ${className}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2.5">
        {/* Playback Controls */}
        <div className="flex items-center space-x-1.5">
          <button
            onClick={onStepBackward}
            disabled={!hasSteps || currentStepIndex === 0}
            className="w-7 h-7 rounded-xs bg-ops-surface hover:bg-ops-panel text-txt-secondary flex items-center justify-center disabled:opacity-30 disabled:cursor-not-allowed transition-colors border border-ops-border"
            title="Previous Step"
            aria-label="Previous Step"
          >
            <SkipBackIcon className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onTogglePlay}
            disabled={!hasSteps}
            className="w-7 h-7 rounded-xs bg-forest hover:bg-forest-light text-txt-primary flex items-center justify-center disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            title={isPlaying ? 'Pause Simulation' : 'Play Timeline'}
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? <PauseIcon className="w-3.5 h-3.5" /> : <PlayIcon className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={onStepForward}
            disabled={!hasSteps || currentStepIndex >= steps.length - 1}
            className="w-7 h-7 rounded-xs bg-ops-surface hover:bg-ops-panel text-txt-secondary flex items-center justify-center disabled:opacity-30 disabled:cursor-not-allowed transition-colors border border-ops-border"
            title="Next Step"
            aria-label="Next Step"
          >
            <SkipForwardIcon className="w-3.5 h-3.5" />
          </button>
          {onReplay && (
            <button
              onClick={onReplay}
              disabled={!hasSteps}
              className="w-7 h-7 rounded-xs bg-ops-surface hover:bg-ops-panel text-txt-secondary flex items-center justify-center disabled:opacity-30 disabled:cursor-not-allowed transition-colors border border-ops-border"
              title="Replay from Beginning"
              aria-label="Replay"
            >
              <RotateCcwIcon className="w-3.5 h-3.5" />
            </button>
          )}

          <span className="text-txt-primary font-semibold font-mono uppercase tracking-wider ml-2 text-xs">
            Spread Timeline
          </span>
        </div>

        {/* Current Timestep Telemetry */}
        <div className="flex items-center space-x-3 font-mono text-[11px]">
          {currentStep ? (
            <>
              <span className="text-txt-muted">
                Burned: <strong className="text-danger font-semibold">{currentStep.cumulative_burned_area_ha.toFixed(1)} ha</strong>
              </span>
              {currentStep.spread_velocity_kmh !== undefined && (
                <span className="text-txt-muted hidden sm:inline">
                  Velocity: <strong className="text-amber font-semibold">{currentStep.spread_velocity_kmh.toFixed(1)} km/h</strong>
                </span>
              )}
              {currentStep.active_front_cells_count !== undefined && (
                <span className="text-txt-muted hidden md:inline">
                  Front: <strong className="text-txt-primary font-semibold">{currentStep.active_front_cells_count} cells</strong>
                </span>
              )}
              <span className="px-2 py-0.5 rounded-xs bg-ops-bg text-txt-primary border border-ops-border font-medium text-[10px]">
                T+{currentStep.elapsed_minutes}m (Step {currentStep.step_number ?? currentHour})
              </span>
            </>
          ) : (
            <span className="text-txt-muted font-mono">No Active Timestep</span>
          )}
        </div>
      </div>

      {/* Scrub Range Slider */}
      {hasSteps ? (
        <div>
          <input
            type="range"
            min="0"
            max={steps.length - 1}
            value={currentStepIndex}
            onChange={(e) => onSelectStep(parseInt(e.target.value, 10))}
            className="w-full h-1.5 bg-ops-bg rounded-xs appearance-none cursor-pointer accent-forest"
          />
          <div className="flex justify-between text-[10px] text-txt-muted font-mono mt-1">
            <span>T+0h (Ignition)</span>
            <span>T+3h</span>
            <span>T+6h</span>
            <span>T+9h</span>
            <span>T+12h (Final Perimeter)</span>
          </div>
        </div>
      ) : (
        <div className="py-2 px-3 rounded-xs bg-ops-bg border border-dashed border-ops-border text-center text-txt-muted text-[11px] font-mono">
          Timeline scrub disabled until a simulation job is executed.
        </div>
      )}
    </div>
  );
};


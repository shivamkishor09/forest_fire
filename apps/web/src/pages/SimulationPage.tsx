import React, { useState, useEffect } from 'react';
import { MapContainer } from '../features/map/components/MapContainer';
import { RegionLayer } from '../features/map/components/RegionLayer';
import { SimulationLayer } from '../features/map/components/SimulationLayer';
import { MapControls } from '../features/map/components/MapControls';
import { LayerControls } from '../features/map/components/LayerControls';
import { IgnitionSelector } from '../features/simulation/components/IgnitionSelector';
import { SimulationControls } from '../features/simulation/components/SimulationControls';
import { Timeline } from '../features/simulation/components/Timeline';
import { SimulationStatus } from '../features/simulation/components/SimulationStatus';
import { SimulationMetricChart } from '../features/simulation/components/SimulationMetricChart';
import { useSimulation } from '../features/simulation/hooks/useSimulation';
import { RegionSummary, IgnitionPoint } from '../types/domain';
import { GeoJSONFeature, PolygonGeometry, MultiPolygonGeometry } from '../types/geo';
import { ErrorAlert } from '../components/feedback/ErrorAlert';
import { isPointInGeometry, getBoundsFromGeoJSON } from '../features/map/utils/geoUtils';
import { useMapContext } from '../features/map/hooks/useMapContext';
import { TargetIcon, MapIcon, SlidersIcon, BarChartIcon } from '../components/common/Icons';

export interface SimulationPageProps {
  selectedRegion: RegionSummary | null;
  boundary: GeoJSONFeature<PolygonGeometry | MultiPolygonGeometry, RegionSummary> | null;
  initialIgnition?: IgnitionPoint | null;
}

const SimulationFocusControls: React.FC<{
  ignitionPoint: IgnitionPoint | null;
  boundary: GeoJSONFeature<PolygonGeometry | MultiPolygonGeometry, RegionSummary> | null;
}> = ({ ignitionPoint, boundary }) => {
  const { map } = useMapContext();

  const handleFocusIgnition = () => {
    if (map && ignitionPoint) {
      map.flyTo([ignitionPoint.latitude, ignitionPoint.longitude], 13);
    }
  };

  const handleFocusBoundary = () => {
    if (map && boundary?.geometry) {
      const bounds = getBoundsFromGeoJSON(boundary.geometry);
      if (bounds) {
        map.fitBounds(bounds, { padding: [40, 40] });
      }
    }
  };

  return (
    <div className="bg-ops-panel border border-ops-border rounded-xs shadow-md p-1 flex flex-col space-y-1">
      {ignitionPoint && (
        <button
          onClick={handleFocusIgnition}
          className="w-7 h-7 rounded-xs flex items-center justify-center text-txt-secondary hover:text-amber hover:bg-ops-surface transition-colors"
          title="Center on Ignition Point"
          aria-label="Center on Ignition Point"
        >
          <TargetIcon className="w-4 h-4" />
        </button>
      )}
      {boundary && (
        <button
          onClick={handleFocusBoundary}
          className="w-7 h-7 rounded-xs flex items-center justify-center text-txt-secondary hover:text-amber hover:bg-ops-surface transition-colors"
          title="Fit Region Boundary"
          aria-label="Fit Region Boundary"
        >
          <MapIcon className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

export const SimulationPage: React.FC<SimulationPageProps> = ({
  selectedRegion,
  boundary,
  initialIgnition,
}) => {
  const [boundaryWarning, setBoundaryWarning] = useState<string | null>(null);
  const [sidebarTab, setSidebarTab] = useState<'params' | 'metrics'>('params');

  const {
    ignitionPoint,
    setIgnitionPoint,
    durationHours,
    setDurationHours,
    stepMinutes,
    setStepMinutes,
    windSpeedMs,
    setWindSpeedMs,
    windDirectionDeg,
    setWindDirectionDeg,
    fuelType,
    setFuelType,
    activeJob,
    simulationDetail,
    stepsData,
    currentStepIndex,
    setCurrentStepIndex,
    isPlaying,
    setIsPlaying,
    isSubmitting,
    error,
    startSimulation,
    clearIgnition,
    stepForward,
    stepBackward,
    replaySimulation,
  } = useSimulation(selectedRegion?.id || 'reg-01', initialIgnition);

  // Global keyboard shortcuts for timeline navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const targetTag = (e.target as HTMLElement)?.tagName;
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(targetTag)) {
        return;
      }

      if (e.code === 'Space') {
        e.preventDefault();
        setIsPlaying((prev) => !prev);
      } else if (e.code === 'ArrowLeft') {
        e.preventDefault();
        stepBackward();
      } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        stepForward();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [setIsPlaying, stepBackward, stepForward]);

  const handleMapClick = (lat: number, lng: number) => {
    // Validate if the clicked point is within the selected region boundary
    if (boundary?.geometry && !isPointInGeometry({ latitude: lat, longitude: lng }, boundary.geometry)) {
      setBoundaryWarning(
        `Coordinate (${lat.toFixed(4)}°N, ${lng.toFixed(4)}°E) is outside region boundary '${selectedRegion?.name || 'Selected Region'}'.`
      );
      return;
    }

    setBoundaryWarning(null);
    setIgnitionPoint({ latitude: lat, longitude: lng });
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden relative bg-ops-bg">
      {/* Simulation Ribbon */}
      <div className="h-9 bg-ops-panel border-b border-ops-border px-4 flex items-center justify-between shrink-0 text-xs z-10 font-mono">
        <div className="flex items-center space-x-3">
          <span className="text-txt-muted uppercase tracking-wider text-[11px] font-semibold">Simulation Engine:</span>
          <span className="text-txt-primary font-semibold text-[11px]">Cellular Automata (12h Spread)</span>
          <span className="px-2 py-0.5 rounded-xs bg-ops-surface text-txt-primary border border-ops-border text-[10px] font-bold">
            {activeJob ? activeJob.status : 'READY'}
          </span>
        </div>

        <div className="text-txt-muted text-[11px] hidden md:block">
          Click map or input coordinates to place ignition origin.
        </div>
      </div>

      {/* Main Split Layout: Map + Controls */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Map Viewport */}
        <div className="flex-1 relative overflow-hidden">
          {(error || boundaryWarning) && (
            <div className="absolute top-4 left-1/2 -translate-x-1/2 z-30 w-full max-w-md px-4 space-y-2">
              {error && (
                <ErrorAlert
                  title="Simulation Warning"
                  message={error}
                />
              )}
              {boundaryWarning && (
                <ErrorAlert
                  title="Boundary Warning"
                  message={boundaryWarning}
                />
              )}
            </div>
          )}

          <MapContainer onMapClick={handleMapClick}>
            <RegionLayer boundaryFeature={boundary} />
            <SimulationLayer
              ignitionPoint={ignitionPoint}
              perimeterData={stepsData}
              currentStepIndex={currentStepIndex}
            />

            {/* Floating Controls */}
            <div className="absolute top-4 right-4 z-[400] flex flex-col space-y-2 pointer-events-auto">
              <LayerControls />
              <MapControls />
              <SimulationFocusControls ignitionPoint={ignitionPoint} boundary={boundary} />
            </div>

            {/* Floating 12-Hour Timeline Slider at bottom */}
            <div className="absolute bottom-5 left-1/2 -translate-x-1/2 z-[400] w-full max-w-2xl px-4 pointer-events-auto">
              <Timeline
                stepsData={stepsData}
                currentStepIndex={currentStepIndex}
                onSelectStep={setCurrentStepIndex}
                isPlaying={isPlaying}
                onTogglePlay={() => setIsPlaying(!isPlaying)}
                onStepForward={stepForward}
                onStepBackward={stepBackward}
                onReplay={replaySimulation}
              />
            </div>
          </MapContainer>
        </div>

        {/* Right Simulation Parameters & Analytics Sidebar */}
        <div className="w-80 bg-ops-panel border-l border-ops-border p-3.5 flex flex-col space-y-3.5 shrink-0 z-10 overflow-y-auto">
          {/* Navigation tab between Parameters and Spread Metrics */}
          <div className="flex bg-ops-bg border border-ops-border rounded-xs p-0.5 text-[11px] shrink-0 font-mono">
            <button
              onClick={() => setSidebarTab('params')}
              className={`flex-1 py-1.5 px-2 rounded-xs flex items-center justify-center space-x-1.5 font-medium transition-colors ${
                sidebarTab === 'params'
                  ? 'bg-forest text-txt-primary font-semibold'
                  : 'text-txt-secondary hover:text-txt-primary'
              }`}
            >
              <SlidersIcon className="w-3.5 h-3.5" />
              <span>PARAMETERS</span>
            </button>
            <button
              onClick={() => setSidebarTab('metrics')}
              className={`flex-1 py-1.5 px-2 rounded-xs flex items-center justify-center space-x-1.5 font-medium transition-colors ${
                sidebarTab === 'metrics'
                  ? 'bg-forest text-txt-primary font-semibold'
                  : 'text-txt-secondary hover:text-txt-primary'
              }`}
            >
              <BarChartIcon className="w-3.5 h-3.5" />
              <span>SPREAD METRICS</span>
            </button>
          </div>

          {sidebarTab === 'params' ? (
            <>
              <IgnitionSelector
                ignitionPoint={ignitionPoint}
                onSetIgnition={(pt) => {
                  setBoundaryWarning(null);
                  setIgnitionPoint(pt);
                }}
                onClearIgnition={clearIgnition}
              />

              <SimulationControls
                durationHours={durationHours}
                onDurationChange={setDurationHours}
                stepMinutes={stepMinutes}
                onStepMinutesChange={setStepMinutes}
                windSpeedMs={windSpeedMs}
                onWindSpeedChange={setWindSpeedMs}
                windDirectionDeg={windDirectionDeg}
                onWindDirectionChange={setWindDirectionDeg}
                fuelType={fuelType}
                onFuelTypeChange={setFuelType}
                hasIgnition={!!ignitionPoint}
                isSubmitting={isSubmitting}
                onStartSimulation={() => startSimulation('Interactive Spread Run')}
                onClearIgnition={clearIgnition}
                hasCompletedSimulation={activeJob?.status === 'COMPLETED'}
                onReplaySimulation={replaySimulation}
              />

              {(activeJob || simulationDetail) && (
                <SimulationStatus job={activeJob} detail={simulationDetail} />
              )}
            </>
          ) : (
            <>
              <SimulationMetricChart
                stepsData={stepsData}
                currentStepIndex={currentStepIndex}
                onSelectStep={setCurrentStepIndex}
              />

              {(activeJob || simulationDetail) && (
                <SimulationStatus job={activeJob} detail={simulationDetail} />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

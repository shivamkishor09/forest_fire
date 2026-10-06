import React, { useState } from 'react';
import { MapContainer } from '../features/map/components/MapContainer';
import { RegionLayer } from '../features/map/components/RegionLayer';
import { RiskLayer } from '../features/map/components/RiskLayer';
import { MapControls } from '../features/map/components/MapControls';
import { LayerControls } from '../features/map/components/LayerControls';
import { RiskLegend } from '../features/risk/components/RiskLegend';
import { RiskSummaryCard } from '../features/risk/components/RiskSummaryCard';
import { RiskDistributionChart } from '../features/risk/components/RiskDistributionChart';
import { RiskCellInspector } from '../features/risk/components/RiskCellInspector';
import { useRisk } from '../features/risk/hooks/useRisk';
import { RegionSummary, RiskPredictionProperties, IgnitionPoint } from '../types/domain';
import { GeoJSONFeature, PolygonGeometry, MultiPolygonGeometry } from '../types/geo';
import { LoadingSpinner } from '../components/feedback/LoadingSpinner';
import { ErrorAlert } from '../components/feedback/ErrorAlert';
import { TargetIcon, RefreshCwIcon } from '../components/common/Icons';

export interface FireRiskPageProps {
  selectedRegion: RegionSummary | null;
  boundary: GeoJSONFeature<PolygonGeometry | MultiPolygonGeometry, RegionSummary> | null;
  onNavigateToSimulation?: (ignition: IgnitionPoint) => void;
}

export const FireRiskPage: React.FC<FireRiskPageProps> = ({
  selectedRegion,
  boundary,
  onNavigateToSimulation,
}) => {
  const [forecastDate, setForecastDate] = useState<string>('2026-10-06');
  const [activeSideTab, setActiveSideTab] = useState<'summary' | 'distribution'>('summary');

  const {
    riskData,
    rawRiskData,
    summary,
    selectedCell,
    setSelectedCell,
    selectedClassFilter,
    setSelectedClassFilter,
    isLoading,
    error,
    reload,
    recomputeRisk,
  } = useRisk(selectedRegion?.id, forecastDate);

  const handleFocusHighestRisk = () => {
    if (!rawRiskData?.features?.length) return;
    let highest = rawRiskData.features[0];
    for (const f of rawRiskData.features) {
      if (f.properties.risk_probability > highest.properties.risk_probability) {
        highest = f;
      }
    }
    setSelectedCell(highest.properties);
    setSelectedClassFilter('ALL');
  };

  const handleSimulateFromCell = (cell: RiskPredictionProperties) => {
    if (!onNavigateToSimulation) return;

    let lat = 30.2104;
    let lon = 78.7523;

    const matchedFeature = rawRiskData?.features?.find(
      (f) => f.properties.cell_id === cell.cell_id
    );

    if (matchedFeature && matchedFeature.geometry.type === 'Polygon') {
      const ring = (matchedFeature.geometry as PolygonGeometry).coordinates[0];
      if (ring && ring.length > 0) {
        lon = ring.reduce((sum, p) => sum + p[0], 0) / ring.length;
        lat = ring.reduce((sum, p) => sum + p[1], 0) / ring.length;
      }
    }

    onNavigateToSimulation({ latitude: lat, longitude: lon });
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden relative bg-ops-bg">
      {/* Top Controls Ribbon */}
      <div className="h-10 bg-ops-subtle border-b border-ops-border px-4 flex flex-wrap items-center justify-between shrink-0 text-xs z-10 gap-2">
        <div className="flex items-center space-x-2">
          <span className="font-mono text-[11px] font-semibold text-txt-primary uppercase tracking-wide">
            24h Susceptibility Forecast:
          </span>
          <input
            type="date"
            value={forecastDate}
            onChange={(e) => setForecastDate(e.target.value)}
            className="bg-ops-panel border border-ops-border rounded-[2px] px-2 py-0.5 text-txt-primary font-mono text-xs focus:outline-none focus:border-forest"
          />
          <button
            onClick={recomputeRisk}
            disabled={isLoading || !selectedRegion}
            className="px-2.5 py-1 rounded-[2px] bg-forest hover:bg-forest-hover text-txt-primary font-semibold text-[11px] transition-colors disabled:opacity-40 flex items-center space-x-1 border border-forest-border"
            title="Execute XGBoost risk inference"
          >
            <RefreshCwIcon className="w-3 h-3" />
            <span>RUN MODEL</span>
          </button>
          <button
            onClick={handleFocusHighestRisk}
            disabled={isLoading || !summary}
            className="px-2.5 py-1 rounded-[2px] bg-ops-surface hover:bg-ops-hover text-txt-secondary border border-ops-border text-[11px] font-medium transition-colors disabled:opacity-40 flex items-center space-x-1"
            title="Locate cell with maximum fire risk"
          >
            <TargetIcon className="w-3 h-3 text-amber" />
            <span>LOCATE PEAK</span>
          </button>
        </div>

        <div className="flex items-center space-x-1">
          <span className="text-txt-muted font-mono text-[11px] mr-1">FILTER:</span>
          {['ALL', 'EXTREME', 'HIGH', 'MODERATE', 'LOW'].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setSelectedClassFilter(lvl)}
              className={`px-2 py-0.5 rounded-[2px] text-[10px] font-mono font-medium transition-colors border ${
                selectedClassFilter === lvl
                  ? 'bg-forest text-txt-primary font-bold border-forest'
                  : 'bg-ops-panel text-txt-muted hover:text-txt-primary border-ops-border'
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Main Map View */}
      <div className="flex-1 relative overflow-hidden">
        {isLoading && (
          <div className="absolute inset-0 z-30 bg-ops-bg/80 flex items-center justify-center">
            <LoadingSpinner label="Running 500m XGBoost risk inference..." />
          </div>
        )}

        {error && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-30 w-full max-w-md px-4">
            <ErrorAlert
              title="Risk Prediction Service"
              message={error}
              onRetry={reload}
            />
          </div>
        )}

        <MapContainer>
          <RegionLayer boundaryFeature={boundary} />
          <RiskLayer
            riskData={riskData}
            selectedCellId={selectedCell?.cell_id}
            onSelectCell={(cellProps: RiskPredictionProperties) => setSelectedCell(cellProps)}
          />

          {/* Unified Map Controls (Top-Right) */}
          <div className="absolute top-3 right-3 z-[400] flex flex-col space-y-2 pointer-events-auto">
            <LayerControls />
            <MapControls />
          </div>

          {/* Left Floating Info Panels */}
          <div className="absolute top-3 left-3 z-[400] flex flex-col space-y-2 pointer-events-auto max-w-xs">
            <div className="flex bg-ops-panel border border-ops-border rounded-[2px] p-0.5 text-[11px] font-mono">
              <button
                onClick={() => setActiveSideTab('summary')}
                className={`flex-1 py-1 rounded-[1px] text-center font-medium transition-colors ${
                  activeSideTab === 'summary'
                    ? 'bg-ops-surface text-txt-primary font-semibold'
                    : 'text-txt-muted hover:text-txt-primary'
                }`}
              >
                SUMMARY
              </button>
              <button
                onClick={() => setActiveSideTab('distribution')}
                className={`flex-1 py-1 rounded-[1px] text-center font-medium transition-colors ${
                  activeSideTab === 'distribution'
                    ? 'bg-ops-surface text-txt-primary font-semibold'
                    : 'text-txt-muted hover:text-txt-primary'
                }`}
              >
                DISTRIBUTION
              </button>
            </div>

            {activeSideTab === 'summary' ? (
              <RiskSummaryCard summary={summary} isLoading={isLoading} />
            ) : (
              <RiskDistributionChart
                summary={summary}
                selectedFilter={selectedClassFilter}
                onSelectFilter={setSelectedClassFilter}
              />
            )}

            {selectedCell && (
              <RiskCellInspector
                cell={selectedCell}
                onClose={() => setSelectedCell(null)}
                onSimulateFromCell={handleSimulateFromCell}
              />
            )}
          </div>

          {/* Bottom Left Legend */}
          <div className="absolute bottom-3 left-3 z-[400] pointer-events-auto">
            <RiskLegend />
          </div>
        </MapContainer>
      </div>
    </div>
  );
};


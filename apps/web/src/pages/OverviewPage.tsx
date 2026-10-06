import React from 'react';
import { MetricGrid } from '../features/dashboard/components/MetricGrid';
import { OperationalAttentionBanner } from '../features/dashboard/components/OperationalAttentionBanner';
import { MapContainer } from '../features/map/components/MapContainer';
import { RegionLayer } from '../features/map/components/RegionLayer';
import { FireLayer } from '../features/map/components/FireLayer';
import { RiskLayer } from '../features/map/components/RiskLayer';
import { MapControls } from '../features/map/components/MapControls';
import { LayerControls } from '../features/map/components/LayerControls';
import { MapLegend } from '../features/map/components/MapLegend';
import { useActiveFires } from '../features/fire/hooks/useActiveFires';
import { useRisk } from '../features/risk/hooks/useRisk';
import { RegionSummary } from '../types/domain';
import { GeoJSONFeature, PolygonGeometry, MultiPolygonGeometry } from '../types/geo';
import { NavTab } from '../components/layout/Navigation';

export interface OverviewPageProps {
  regions: RegionSummary[];
  selectedRegion: RegionSummary | null;
  boundary: GeoJSONFeature<PolygonGeometry | MultiPolygonGeometry, RegionSummary> | null;
  onNavigateTab: (tab: NavTab) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  regions,
  selectedRegion,
  boundary,
  onNavigateTab,
}) => {
  const { filteredFeatures, totalCount: activeFireCount } = useActiveFires(selectedRegion?.id);
  const { riskData, summary: riskSummary } = useRisk(selectedRegion?.id);

  const meanRisk = riskSummary?.mean_probability || 0.0042;
  const gridCells = riskSummary?.total_cells || 1400;
  const highRiskCells = riskSummary?.high_risk_cells || 0;
  const extremeRiskCells = riskSummary?.extreme_risk_cells || 0;
  const maxRisk = riskSummary?.mean_probability || 0.0042;

  const regionName = (selectedRegion?.name || 'Garhwal Forest Division').toUpperCase();

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-ops-bg">
      {/* Operational Summary Bar + Attention Banner */}
      <div className="bg-ops-subtle border-b border-ops-border p-2.5 shrink-0 space-y-2">
        <MetricGrid
          regionCount={regions.length}
          activeFireCount={activeFireCount}
          meanRisk={meanRisk}
          gridCells={gridCells}
          highRiskCount={highRiskCells + extremeRiskCells}
          maxRisk={maxRisk}
        />
        <OperationalAttentionBanner
          regionName={selectedRegion?.name}
          activeFireCount={activeFireCount}
          highRiskCellCount={highRiskCells}
          extremeRiskCellCount={extremeRiskCells}
          maxProbability={maxRisk}
          forecastDate={riskSummary?.target_date}
          onNavigateTab={onNavigateTab}
        />
      </div>

      {/* Hero GIS Map Viewport */}
      <div className="flex-1 relative overflow-hidden">
        <MapContainer>
          {/* GIS Layers */}
          <RegionLayer boundaryFeature={boundary} />
          <RiskLayer riskData={riskData} />
          <FireLayer
            firesData={
              filteredFeatures.length > 0
                ? { type: 'FeatureCollection', features: filteredFeatures }
                : null
            }
          />

          {/* Unified Map Controls (Top-Right) */}
          <div className="absolute top-3 right-3 z-[400] flex flex-col space-y-2 pointer-events-auto">
            <LayerControls />
            <MapControls />
          </div>

          {/* Professional Compact Region Overlay (Top-Left) */}
          <div className="absolute top-3 left-3 z-[400] bg-ops-panel/95 border border-ops-border rounded-[3px] p-2.5 text-xs pointer-events-auto shadow-md">
            <div className="text-[13px] font-bold font-mono tracking-wide text-txt-primary">
              {regionName}
            </div>
            <div className="text-[10px] font-mono text-txt-muted pb-2">
              500 m GRID · EPSG:4326
            </div>
            <div className="flex items-center space-x-1.5 pt-1.5 border-t border-ops-border font-mono text-[11px]">
              <button
                onClick={() => onNavigateTab('risk')}
                className="px-2.5 py-1 rounded-[2px] bg-ops-surface hover:bg-ops-hover text-txt-primary border border-ops-border transition-colors font-medium"
              >
                24H RISK
              </button>
              <button
                onClick={() => onNavigateTab('active_fires')}
                className={`px-2.5 py-1 rounded-[2px] border transition-colors font-medium ${
                  activeFireCount > 0
                    ? 'bg-danger/15 text-danger border-danger/40'
                    : 'bg-ops-surface hover:bg-ops-hover text-txt-primary border-ops-border'
                }`}
              >
                HOTSPOTS ({activeFireCount})
              </button>
              <button
                onClick={() => onNavigateTab('simulation')}
                className="px-2.5 py-1 rounded-[2px] bg-forest/20 hover:bg-forest/30 text-forest border border-forest/40 transition-colors font-semibold"
              >
                SIMULATE
              </button>
            </div>
          </div>

          {/* Professional GIS Legend (Bottom-Left) */}
          <div className="absolute bottom-3 left-3 z-[400] pointer-events-auto">
            <MapLegend />
          </div>
        </MapContainer>
      </div>
    </div>
  );
};


import React from 'react';
import { FlameIcon, AlertTriangleIcon, ActivityIcon, GridIcon } from '../../../components/common/Icons';

export interface MetricGridProps {
  regionCount: number;
  activeFireCount: number;
  meanRisk: number;
  gridCells: number;
  highRiskCount?: number;
  maxRisk?: number;
  className?: string;
}

export const MetricGrid: React.FC<MetricGridProps> = ({
  regionCount: _regionCount,
  activeFireCount,
  meanRisk,
  gridCells,
  highRiskCount = 0,
  maxRisk = 0,
  className = '',
}) => {
  const peakRiskFormatted =
    maxRisk > 0 ? `${(maxRisk * 100).toFixed(1)}%` : `${(meanRisk * 100).toFixed(1)}%`;
  const meanRiskFormatted = `${(meanRisk * 100).toFixed(2)}%`;

  return (
    <div
      className={`bg-ops-subtle border border-ops-border rounded-[4px] grid grid-cols-2 lg:grid-cols-4 divide-y lg:divide-y-0 lg:divide-x divide-ops-border ${className}`}
    >
      {/* 1. ACTIVE HOTSPOTS */}
      <div className="p-3 flex items-start justify-between">
        <div className="space-y-0.5">
          <div className="flex items-center space-x-1.5 text-[10px] font-mono font-semibold tracking-wider uppercase text-txt-muted">
            <FlameIcon className={`w-3.5 h-3.5 ${activeFireCount > 0 ? 'text-danger' : 'text-txt-muted'}`} />
            <span>Active Hotspots</span>
          </div>
          <div
            className={`text-2xl font-mono font-bold tracking-tight leading-none pt-1 ${
              activeFireCount > 0 ? 'text-danger' : 'text-txt-primary'
            }`}
          >
            {activeFireCount}
          </div>
          <div className="text-[11px] text-txt-muted pt-0.5">
            VIIRS / MODIS (24h Window)
          </div>
        </div>
      </div>

      {/* 2. ELEVATED RISK CELLS */}
      <div className="p-3 flex items-start justify-between">
        <div className="space-y-0.5">
          <div className="flex items-center space-x-1.5 text-[10px] font-mono font-semibold tracking-wider uppercase text-txt-muted">
            <AlertTriangleIcon className={`w-3.5 h-3.5 ${highRiskCount > 0 ? 'text-amber' : 'text-txt-muted'}`} />
            <span>Elevated Risk Cells</span>
          </div>
          <div
            className={`text-2xl font-mono font-bold tracking-tight leading-none pt-1 ${
              highRiskCount > 0 ? 'text-amber' : 'text-txt-primary'
            }`}
          >
            {highRiskCount}
          </div>
          <div className="text-[11px] text-txt-muted pt-0.5">
            500m Cells (High / Extreme)
          </div>
        </div>
      </div>

      {/* 3. PEAK FIRE RISK */}
      <div className="p-3 flex items-start justify-between">
        <div className="space-y-0.5">
          <div className="flex items-center space-x-1.5 text-[10px] font-mono font-semibold tracking-wider uppercase text-txt-muted">
            <ActivityIcon className="w-3.5 h-3.5 text-txt-muted" />
            <span>Peak Fire Risk</span>
          </div>
          <div
            className={`text-2xl font-mono font-bold tracking-tight leading-none pt-1 ${
              maxRisk > 0.75 ? 'text-danger' : maxRisk > 0.5 ? 'text-amber' : 'text-txt-primary'
            }`}
          >
            {peakRiskFormatted}
          </div>
          <div className="text-[11px] text-txt-muted pt-0.5">
            Sector Mean: {meanRiskFormatted}
          </div>
        </div>
      </div>

      {/* 4. SPATIAL PARTITIONS */}
      <div className="p-3 flex items-start justify-between">
        <div className="space-y-0.5">
          <div className="flex items-center space-x-1.5 text-[10px] font-mono font-semibold tracking-wider uppercase text-txt-muted">
            <GridIcon className="w-3.5 h-3.5 text-txt-muted" />
            <span>Spatial Coverage</span>
          </div>
          <div className="text-2xl font-mono font-bold tracking-tight leading-none pt-1 text-txt-primary">
            {(gridCells ?? 0).toLocaleString()}
          </div>
          <div className="text-[11px] text-txt-muted pt-0.5">
            500m Resolution · EPSG:4326
          </div>
        </div>
      </div>
    </div>
  );
};


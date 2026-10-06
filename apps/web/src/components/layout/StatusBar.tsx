import React from 'react';

export interface StatusBarProps {
  regionName?: string;
  totalCells?: number;
  activeLayerName?: string;
  className?: string;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  regionName = 'Uttarakhand Western Himalaya',
  totalCells = 11362,
  activeLayerName = '24h Susceptibility',
  className = '',
}) => {
  return (
    <footer
      className={`h-6 bg-ops-bg border-t border-ops-border px-4 flex items-center justify-between text-[10px] text-txt-muted font-mono shrink-0 z-20 select-none ${className}`}
    >
      <div className="flex items-center space-x-4">
        <span>SECTOR: <strong className="text-txt-primary font-medium">{regionName.toUpperCase()}</strong></span>
        <span className="hidden md:inline">COVERAGE: {(totalCells ?? 0).toLocaleString()} CELLS (500m)</span>
      </div>
      <div className="flex items-center space-x-4">
        <span>CRS: <strong className="text-txt-secondary font-medium">EPSG:4326</strong></span>
        <span className="text-forest font-semibold uppercase hidden sm:inline">
          ACTIVE LAYER: {activeLayerName}
        </span>
      </div>
    </footer>
  );
};


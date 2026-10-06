import React from 'react';
import { APP_CONFIG } from '../../../app/config';

export interface RiskLegendProps {
  className?: string;
}

export const RiskLegend: React.FC<RiskLegendProps> = ({ className = '' }) => {
  return (
    <div
      className={`bg-ops-panel/95 border border-ops-border rounded-[3px] p-2.5 shadow-md text-xs select-none w-52 ${className}`}
    >
      <div className="flex items-center justify-between mb-1.5 pb-1 border-b border-ops-border">
        <h4 className="font-mono text-[10px] font-semibold uppercase tracking-wider text-txt-primary">
          SUSCEPTIBILITY SCALE
        </h4>
        <span className="text-[10px] font-mono text-txt-muted">500m</span>
      </div>
      <div className="space-y-1 font-mono text-[10px]">
        {Object.entries(APP_CONFIG.riskColors).map(([key, config]) => (
          <div key={key} className="flex items-center justify-between">
            <span className="flex items-center space-x-1.5">
              <span
                className="w-2.5 h-2.5 rounded-[1px]"
                style={{ backgroundColor: config.fillColor }}
              />
              <span className="text-txt-secondary uppercase">{config.label}</span>
            </span>
            <span className="text-txt-muted text-[10px]">{config.threshold}</span>
          </div>
        ))}
      </div>
    </div>
  );
};


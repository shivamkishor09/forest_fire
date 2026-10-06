import React from 'react';
import { RiskSummary, RiskClass } from '../../../types/domain';
import { APP_CONFIG, RiskLevelKey } from '../../../app/config';

export interface RiskDistributionChartProps {
  summary: RiskSummary | null;
  selectedFilter?: string;
  onSelectFilter?: (level: string) => void;
  className?: string;
}

export const RiskDistributionChart: React.FC<RiskDistributionChartProps> = ({
  summary,
  selectedFilter = 'ALL',
  onSelectFilter = () => {},
  className = '',
}) => {
  if (!summary) {
    return (
      <div
        className={`p-3 bg-ops-panel border border-ops-border rounded-[3px] text-xs ${className}`}
        role="region"
        aria-label="Risk Distribution Chart"
      >
        <div className="flex items-center justify-between pb-1.5 border-b border-ops-border mb-2 font-mono">
          <span className="font-semibold text-txt-primary text-[10px] uppercase tracking-wider">Risk Distribution</span>
        </div>
        <p className="text-txt-muted text-center py-2 text-xs font-mono">
          Awaiting risk prediction summary...
        </p>
      </div>
    );
  }

  const totalCells = summary.total_cells || 1;
  const dist = summary.risk_distribution || { low: 0, moderate: 0, high: 0, extreme: 0 };

  const classes: { key: RiskLevelKey; classEnum: RiskClass; count: number }[] = [
    { key: 'LOW', classEnum: 'LOW', count: dist.low || 0 },
    { key: 'MODERATE', classEnum: 'MODERATE', count: dist.moderate || 0 },
    { key: 'HIGH', classEnum: 'HIGH', count: dist.high || 0 },
    { key: 'EXTREME', classEnum: 'EXTREME', count: dist.extreme || 0 },
  ];

  return (
    <div
      className={`p-3 bg-ops-panel/95 border border-ops-border rounded-[3px] shadow-lg text-xs ${className}`}
      role="region"
      aria-label="Risk Distribution Chart"
    >
      <div className="flex items-center justify-between pb-1.5 border-b border-ops-border mb-2 font-mono">
        <span className="font-semibold text-txt-primary text-[10px] uppercase tracking-wider">500m Cell Breakdown</span>
        <span className="text-[10px] text-txt-muted">
          {(summary.total_cells ?? 0).toLocaleString()} CELLS
        </span>
      </div>

      <div className="space-y-1.5">
        {classes.map(({ key, count }) => {
          const config = APP_CONFIG.riskColors[key];
          const pct = totalCells > 0 ? (count / totalCells) * 100 : 0;
          const isFilterActive = (selectedFilter || 'ALL').toUpperCase() === key;

          return (
            <button
              key={key}
              type="button"
              onClick={() => onSelectFilter(isFilterActive ? 'ALL' : key)}
              aria-label={`Filter map by ${config.label} risk tier`}
              className={`w-full text-left p-1.5 rounded-[2px] border transition-colors cursor-pointer ${
                isFilterActive
                  ? 'bg-ops-surface border-forest'
                  : 'bg-ops-subtle border-ops-border hover:bg-ops-surface'
              }`}
            >
              <div className="flex items-center justify-between text-[11px] mb-1">
                <span className="flex items-center space-x-1.5 font-medium">
                  <span
                    className="w-2.5 h-2.5 rounded-[1px] shrink-0"
                    style={{ backgroundColor: config.fillColor }}
                  />
                  <span className={isFilterActive ? 'text-txt-primary font-bold' : 'text-txt-secondary'}>
                    {config.label}
                  </span>
                </span>
                <span className="font-mono text-txt-primary">
                  {count.toLocaleString()}{' '}
                  <span className="text-txt-muted">({pct.toFixed(1)}%)</span>
                </span>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-ops-bg h-1 rounded-[1px] overflow-hidden">
                <div
                  className="h-full rounded-[1px] transition-all"
                  style={{
                    width: `${Math.max(1, pct)}%`,
                    backgroundColor: config.fillColor,
                  }}
                />
              </div>
            </button>
          );
        })}
      </div>

      <div className="mt-2 pt-1.5 border-t border-ops-border flex items-center justify-between text-[10px] text-txt-muted font-mono">
        <span>Click tier to filter</span>
        {selectedFilter !== 'ALL' && (
          <button
            onClick={() => onSelectFilter('ALL')}
            className="text-forest hover:underline font-semibold"
          >
            Clear Filter
          </button>
        )}
      </div>
    </div>
  );
};


import React from 'react';
import { RiskSummary } from '../../../types/domain';
import { Badge } from '../../../components/ui/Badge';
import { Skeleton } from '../../../components/feedback/Skeleton';

export interface RiskSummaryCardProps {
  summary: RiskSummary | null;
  isLoading?: boolean;
  className?: string;
}

export const RiskSummaryCard: React.FC<RiskSummaryCardProps> = ({
  summary,
  isLoading = false,
  className = '',
}) => {
  if (isLoading) {
    return (
      <div className={`p-3 bg-ops-panel border border-ops-border rounded-[3px] ${className}`}>
        <Skeleton className="h-4 w-32 mb-2" />
        <Skeleton className="h-8 w-full mb-2" />
        <Skeleton className="h-4 w-48" />
      </div>
    );
  }

  if (!summary) {
    return (
      <div className={`p-3 bg-ops-panel border border-ops-border rounded-[3px] text-xs text-txt-muted ${className}`}>
        Risk summary unavailable.
      </div>
    );
  }

  const totalCells = summary.total_cells || 1;
  const dist = summary.risk_distribution || { low: 0, moderate: 0, high: 0, extreme: 0 };
  const lowPct = Math.round(((dist.low || 0) / totalCells) * 100);
  const modPct = Math.round(((dist.moderate || 0) / totalCells) * 100);
  const highPct = Math.round(((dist.high || 0) / totalCells) * 100);
  const extPct = Math.round(((dist.extreme || 0) / totalCells) * 100);

  return (
    <div
      className={`p-3 bg-ops-panel/95 border border-ops-border rounded-[3px] shadow-lg text-xs ${className}`}
    >
      <div className="flex items-center justify-between pb-1.5 border-b border-ops-border mb-2">
        <div>
          <h4 className="font-semibold text-txt-primary">REGIONAL RISK</h4>
          <span className="text-[10px] font-mono text-txt-muted">
            TARGET: {summary.target_date || '2026-10-06'}
          </span>
        </div>
        <Badge variant={summary.extreme_risk_cells > 0 ? 'danger' : 'warning'} size="sm">
          MEAN: {(summary.mean_probability * 100).toFixed(1)}%
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-2.5">
        <div className="bg-ops-subtle p-2 rounded-[2px] border border-ops-border">
          <span className="text-[10px] text-txt-muted block">GRID CELLS</span>
          <span className="text-sm font-bold text-txt-primary font-mono">
            {(summary.total_cells ?? 0).toLocaleString()}
          </span>
        </div>
        <div className="bg-ops-subtle p-2 rounded-[2px] border border-ops-border">
          <span className="text-[10px] text-txt-muted block">ELEVATED CELLS</span>
          <span className="text-sm font-bold text-danger font-mono">
            {((summary.high_risk_cells ?? 0) + (summary.extreme_risk_cells ?? 0)).toLocaleString()}
          </span>
        </div>
      </div>

      {/* Distribution progress bar */}
      <div>
        <div className="flex justify-between text-[10px] font-mono text-txt-muted mb-1">
          <span>CLASS BREAKDOWN</span>
          <span>100% COVERAGE</span>
        </div>
        <div className="h-1.5 w-full rounded-[1px] overflow-hidden flex bg-ops-subtle">
          <div style={{ width: `${lowPct}%` }} className="bg-forest h-full" title={`Low: ${lowPct}%`} />
          <div style={{ width: `${modPct}%` }} className="bg-amber h-full" title={`Moderate: ${modPct}%`} />
          <div style={{ width: `${highPct}%` }} className="bg-[#E06D2E] h-full" title={`High: ${highPct}%`} />
          <div style={{ width: `${extPct}%` }} className="bg-danger h-full" title={`Extreme: ${extPct}%`} />
        </div>
        <div className="grid grid-cols-4 gap-1 text-[9px] font-mono text-txt-muted mt-1.5 text-center">
          <span className="text-forest">{lowPct}% Low</span>
          <span className="text-amber">{modPct}% Mod</span>
          <span className="text-[#E06D2E]">{highPct}% High</span>
          <span className="text-danger">{extPct}% Ext</span>
        </div>
      </div>
    </div>
  );
};


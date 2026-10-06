import React from 'react';
import { Button } from '../ui/Button';
import { LayersIcon } from '../common/Icons';

export interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  actionLabel,
  onAction,
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center rounded-xs border border-dashed border-ops-border bg-ops-panel/50 ${className}`}
    >
      <div className="mb-3 text-txt-muted select-none">
        {icon || <LayersIcon className="w-8 h-8 text-txt-muted" />}
      </div>
      <h4 className="text-sm font-semibold text-txt-primary">{title}</h4>
      {description && <p className="text-xs text-txt-secondary mt-1 max-w-sm">{description}</p>}
      {actionLabel && onAction && (
        <div className="mt-4">
          <Button variant="secondary" size="sm" onClick={onAction}>
            {actionLabel}
          </Button>
        </div>
      )}
    </div>
  );
};


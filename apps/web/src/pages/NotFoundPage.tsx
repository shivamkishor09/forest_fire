import React from 'react';
import { EmptyState } from '../components/feedback/EmptyState';
import { LayersIcon } from '../components/common/Icons';

export interface NotFoundPageProps {
  onReturnHome: () => void;
}

export const NotFoundPage: React.FC<NotFoundPageProps> = ({ onReturnHome }) => {
  return (
    <div className="flex-1 flex items-center justify-center p-8 bg-ops-bg">
      <EmptyState
        title="Sector Viewport Not Found"
        description="The requested operational interface or route does not exist."
        icon={<LayersIcon className="w-8 h-8 text-txt-muted" />}
        actionLabel="Return to Command Center"
        onAction={onReturnHome}
        className="max-w-md w-full bg-ops-panel border-ops-border p-6"
      />
    </div>
  );
};


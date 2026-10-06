import React from 'react';
import { Button } from '../ui/Button';
import { AlertTriangleIcon } from '../common/Icons';

export interface ErrorAlertProps {
  title?: string;
  message: string;
  code?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  title = 'Service Unavailable',
  message,
  code,
  onRetry,
  className = '',
}) => {
  return (
    <div
      className={`p-3 rounded-xs bg-danger/10 border border-danger/40 text-txt-primary flex flex-col space-y-2 ${className}`}
      role="alert"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <AlertTriangleIcon className="w-4 h-4 text-danger shrink-0" />
          <span className="font-semibold text-xs tracking-wide text-danger uppercase">{title}</span>
        </div>
        {code && (
          <span className="font-mono text-[10px] px-1.5 py-0.5 rounded-xs bg-danger/20 border border-danger/40 text-danger">
            {code}
          </span>
        )}
      </div>
      <p className="text-xs text-txt-secondary leading-relaxed">{message}</p>
      {onRetry && (
        <div className="pt-1 flex justify-end">
          <Button variant="danger" size="sm" onClick={onRetry}>
            Retry Request
          </Button>
        </div>
      )}
    </div>
  );
};


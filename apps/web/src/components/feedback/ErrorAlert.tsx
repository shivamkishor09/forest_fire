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
  title = 'Critical System Warning',
  message,
  code,
  onRetry,
  className = '',
}) => {
  return (
    <div
      className={`rounded-md overflow-hidden bg-[#121418] border-2 border-[#DC2626] shadow-[0_15px_40px_rgba(0,0,0,0.9)] ring-1 ring-red-500/40 text-white z-50 animate-in fade-in zoom-in-95 duration-150 ${className}`}
      role="alert"
    >
      {/* Industrial Hazard Top Header */}
      <div className="bg-[#B91C1C] px-3.5 py-2 flex items-center justify-between text-white border-b border-red-900 shadow-sm">
        <div className="flex items-center space-x-2.5">
          <div className="p-0.5 rounded bg-black/30 text-amber-300">
            <AlertTriangleIcon className="w-4 h-4 fill-amber-300/20" />
          </div>
          <span className="font-extrabold text-xs font-mono tracking-widest uppercase drop-shadow-sm">
            {title}
          </span>
        </div>
        {code ? (
          <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-black/40 border border-red-300/40 text-red-100 tracking-wider">
            {code}
          </span>
        ) : (
          <span className="font-mono text-[9px] font-bold px-1.5 py-0.5 rounded bg-black/30 text-red-200 tracking-wider uppercase">
            FAIL
          </span>
        )}
      </div>

      {/* Main Alert Body */}
      <div className="p-3.5 space-y-3 bg-[#121418]">
        <div className="p-2.5 rounded bg-[#090B0E] border border-red-900/60 font-mono text-xs text-zinc-100 leading-relaxed shadow-inner break-words">
          <div className="text-[10px] uppercase font-bold text-red-400 tracking-wider mb-1 flex items-center space-x-1">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
            <span>Diagnostics Telemetry:</span>
          </div>
          <p className="text-zinc-200 text-[11px] leading-normal">{message}</p>
        </div>

        {onRetry && (
          <div className="flex items-center justify-between pt-1">
            <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider">
              Manual Override:
            </span>
            <Button
              variant="danger"
              size="sm"
              onClick={onRetry}
              className="bg-[#DC2626] hover:bg-[#EF4444] text-white font-mono font-bold text-xs uppercase tracking-wider px-4 py-1.5 shadow-md border border-red-400/30 transition-all active:translate-y-0.5"
            >
              Retry Request
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};


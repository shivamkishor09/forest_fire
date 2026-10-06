import React from 'react';

export interface CardProps {
  children: React.ReactNode;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
  bodyClassName?: string;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  action,
  className = '',
  bodyClassName = '',
}) => {
  return (
    <div
      className={`bg-ops-panel border border-ops-border rounded-xs shadow-md overflow-hidden flex flex-col ${className}`}
    >
      {(title || action) && (
        <div className="px-3.5 py-2.5 border-b border-ops-border bg-ops-subtle flex items-center justify-between shrink-0">
          <div>
            {typeof title === 'string' ? (
              <h3 className="text-xs font-semibold text-txt-primary uppercase tracking-wider">
                {title}
              </h3>
            ) : (
              title
            )}
            {subtitle && <p className="text-[11px] text-txt-secondary mt-0.5">{subtitle}</p>}
          </div>
          {action && <div className="flex items-center space-x-2">{action}</div>}
        </div>
      )}
      <div className={`p-3.5 flex-1 ${bodyClassName}`}>{children}</div>
    </div>
  );
};

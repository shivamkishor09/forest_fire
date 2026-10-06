import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  variant = 'default',
}) => {
  const variantStyles = {
    default: 'border-ops-border bg-ops-panel text-txt-primary',
    success: 'border-ops-border bg-ops-panel text-txt-primary',
    warning: 'border-amber/40 bg-amber/10 text-txt-primary',
    danger: 'border-danger/40 bg-danger/10 text-txt-primary',
  };

  const badgeColors = {
    default: 'text-txt-muted',
    success: 'text-forest',
    warning: 'text-amber',
    danger: 'text-danger',
  };

  return (
    <div className={`p-3.5 rounded-xs border flex flex-col justify-between ${variantStyles[variant]}`}>
      <div className="flex items-center justify-between text-xs text-txt-secondary font-medium mb-1">
        <span>{title}</span>
        {icon && <span className={badgeColors[variant]}>{icon}</span>}
      </div>
      <div className="text-xl font-bold font-mono tracking-tight my-0.5 text-txt-primary">
        {value}
      </div>
      {subtitle && <div className="text-[11px] text-txt-muted mt-1 truncate">{subtitle}</div>}
    </div>
  );
};

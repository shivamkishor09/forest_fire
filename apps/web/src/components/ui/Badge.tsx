import React from 'react';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'neutral';
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  className = '',
}) => {
  const variantStyles = {
    default: 'bg-ops-surface text-txt-secondary border-ops-border',
    success: 'bg-forest/15 text-forest border-forest/30',
    warning: 'bg-amber/15 text-amber border-amber/30',
    danger: 'bg-danger/15 text-danger border-danger/30',
    info: 'bg-ops-surface text-txt-primary border-ops-border',
    neutral: 'bg-ops-panel text-txt-muted border-ops-border',
  };

  const sizeStyles = {
    sm: 'text-[10px] px-1.5 py-0.5 rounded-[2px]',
    md: 'text-[11px] px-2 py-0.5 rounded-[3px]',
  };

  return (
    <span
      className={`inline-flex items-center font-mono font-medium border ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {children}
    </span>
  );
};


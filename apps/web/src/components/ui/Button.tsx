import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'amber' | 'danger' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'secondary',
  size = 'md',
  isLoading = false,
  icon,
  className = '',
  disabled,
  ...props
}) => {
  const variantStyles = {
    primary:
      'bg-forest hover:bg-forest-hover text-txt-primary border-forest-border font-semibold shadow-none',
    amber:
      'bg-amber hover:bg-amber-hover text-ops-bg border-amber-border font-semibold shadow-none',
    secondary:
      'bg-ops-surface hover:bg-ops-hover text-txt-primary border-ops-border',
    danger:
      'bg-danger hover:bg-danger-hover text-txt-primary border-danger-border font-semibold shadow-none',
    ghost:
      'bg-transparent hover:bg-ops-surface text-txt-secondary hover:text-txt-primary border-transparent',
    outline:
      'bg-transparent hover:bg-ops-surface text-txt-primary border-ops-border',
  };

  const sizeStyles = {
    sm: 'text-[11px] px-2.5 py-1 rounded-[3px]',
    md: 'text-xs px-3 py-1.5 rounded-[4px]',
    lg: 'text-sm px-4 py-2 rounded-[4px]',
  };

  return (
    <button
      className={`inline-flex items-center justify-center font-medium border transition-colors focus:outline-none disabled:opacity-40 disabled:cursor-not-allowed select-none ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin mr-1.5" />
      ) : icon ? (
        <span className="mr-1.5">{icon}</span>
      ) : null}
      {children}
    </button>
  );
};


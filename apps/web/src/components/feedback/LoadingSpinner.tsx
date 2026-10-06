import React from 'react';

export interface LoadingSpinnerProps {
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  label = 'Loading spatial data...',
  size = 'md',
  className = '',
}) => {
  const sizeMap = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-2',
    lg: 'w-12 h-12 border-3',
  };

  return (
    <div className={`flex flex-col items-center justify-center space-y-3 p-6 ${className}`}>
      <div
        className={`${sizeMap[size]} border-forest/20 border-t-forest rounded-full animate-spin`}
        role="status"
        aria-label="loading"
      />
      {label && <p className="text-xs font-mono text-txt-secondary tracking-wide">{label}</p>}
    </div>
  );
};

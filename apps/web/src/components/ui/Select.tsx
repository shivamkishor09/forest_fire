import React from 'react';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  options: SelectOption[];
  label?: string;
}

export const Select: React.FC<SelectProps> = ({
  options,
  label,
  className = '',
  id,
  ...props
}) => {
  const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="flex flex-col space-y-1">
      {label && (
        <label htmlFor={selectId} className="text-xs font-medium text-txt-secondary">
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={`bg-ops-panel border border-ops-border rounded-xs px-2.5 py-1 text-xs text-txt-primary focus:outline-none focus:border-forest cursor-pointer transition-colors ${className}`}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value} disabled={opt.disabled}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
};

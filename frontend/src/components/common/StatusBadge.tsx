import React from 'react';
import { SEVERITY_COLORS } from '../../utils/constants';

interface Props {
  level: string;
  size?: 'sm' | 'md';
  pulse?: boolean;
}

export const StatusBadge: React.FC<Props> = ({ level, size = 'sm', pulse = false }) => {
  const color = SEVERITY_COLORS[level] || '#94a3b8';
  const sizeClasses = size === 'sm' ? 'text-[10px] px-2 py-0.5' : 'text-xs px-2.5 py-1';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-semibold uppercase tracking-wider
                  border ${sizeClasses} ${pulse && level === 'Critical' ? 'pulse-critical' : ''}`}
      style={{
        color,
        backgroundColor: `${color}15`,
        borderColor: `${color}30`,
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full animate-pulse"
        style={{ backgroundColor: color }}
      />
      {level}
    </span>
  );
};

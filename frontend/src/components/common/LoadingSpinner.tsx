import React from 'react';

export const LoadingSpinner: React.FC<{ message?: string }> = ({ message = 'Analyzing…' }) => {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12 animate-fade-in">
      {/* Animated rings */}
      <div className="relative w-16 h-16">
        <div className="absolute inset-0 rounded-full border-2 border-accent-blue/20 animate-ping" />
        <div className="absolute inset-1 rounded-full border-2 border-t-accent-blue border-r-accent-purple border-b-transparent border-l-transparent animate-spin" />
        <div className="absolute inset-3 rounded-full border-2 border-t-transparent border-r-transparent border-b-accent-teal border-l-accent-teal animate-spin-slow" />
        <div className="absolute inset-[18px] rounded-full bg-gradient-to-br from-accent-blue to-accent-purple opacity-60 animate-pulse" />
      </div>
      <div className="text-center">
        <p className="text-sm font-medium text-slate-300">{message}</p>
        <p className="text-xs text-slate-500 mt-1">Running AI detection pipeline…</p>
      </div>
    </div>
  );
};

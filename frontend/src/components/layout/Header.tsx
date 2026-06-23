import React from 'react';
import { Activity, Wifi, WifiOff, Download, Camera, Database } from 'lucide-react';
import type { HealthResponse, AnalysisResponse } from '../../types';
import { getExportUrl } from '../../api/client';
import { timeAgo } from '../../utils/formatters';

interface Props {
  health: HealthResponse | null;
  result: AnalysisResponse | null;
  activeTab: 'live' | 'analytics';
  onTabChange: (tab: 'live' | 'analytics') => void;
}

export const Header: React.FC<Props> = ({ health, result, activeTab, onTabChange }) => {
  const isOnline = health?.status === 'online';

  return (
    <header className="glass-card-elevated border-b border-white/[0.06] px-6 py-4 flex items-center justify-between shadow-2xl relative z-10">
      {/* Brand */}
      <div className="flex items-center gap-4 hover-lift cursor-pointer">
        <div className="relative">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-blue via-accent-purple to-accent-teal
                          flex items-center justify-center shadow-lg shadow-accent-blue/40 border border-white/20">
            <span className="text-xl">🅿️</span>
          </div>
          <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-navy-900 flex items-center justify-center">
            <div className={`w-2.5 h-2.5 rounded-full ${isOnline ? 'bg-severity-low drop-shadow-[0_0_5px_rgba(16,185,129,0.8)] animate-pulse' : 'bg-severity-critical drop-shadow-[0_0_5px_rgba(239,68,68,0.8)]'}`} />
          </div>
        </div>
        <div>
          <h1 className="text-lg font-black bg-gradient-to-r from-accent-blue via-accent-teal to-accent-cyan bg-clip-text text-transparent leading-tight drop-shadow-[0_2px_10px_rgba(6,182,212,0.4)]">
            AI-ParkSense
          </h1>
          <p className="text-[10px] text-slate-400 font-bold tracking-[0.1em] uppercase">
            Traffic Intelligence Dashboard
          </p>
        </div>
      </div>

      {/* View Toggle */}
      <div className="flex bg-navy-900/50 p-1 rounded-lg border border-white/5">
        <button
          onClick={() => onTabChange('live')}
          className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-xs font-semibold transition-all ${
            activeTab === 'live' 
              ? 'bg-accent-blue/20 text-accent-cyan shadow-[0_0_10px_rgba(6,182,212,0.2)]' 
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Camera className="w-3.5 h-3.5" />
          Live Camera
        </button>
        <button
          onClick={() => onTabChange('analytics')}
          className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-xs font-semibold transition-all ${
            activeTab === 'analytics' 
              ? 'bg-accent-purple/20 text-accent-purple shadow-[0_0_10px_rgba(168,85,247,0.2)]' 
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          City Analytics
        </button>
      </div>

      {/* Status */}
      <div className="flex items-center gap-5">
        {/* Connection */}
        <div className="flex items-center gap-2 text-xs">
          {isOnline ? (
            <Wifi className="w-3.5 h-3.5 text-severity-low" />
          ) : (
            <WifiOff className="w-3.5 h-3.5 text-severity-critical" />
          )}
          <span className={isOnline ? 'text-severity-low' : 'text-severity-critical'}>
            {isOnline ? 'Online' : 'Offline'}
          </span>
        </div>

        {/* Model status */}
        {health && (
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Activity className="w-3.5 h-3.5" />
            <span>YOLO {health.model_loaded ? '✓' : '✗'}</span>
          </div>
        )}

        {/* Last analysis */}
        {result && (
          <div className="flex items-center gap-4">
            <div className="text-xs text-slate-500">
              Last: <span className="text-slate-400">{timeAgo(result.timestamp)}</span>
            </div>
            <a 
              href={getExportUrl(result.id)}
              download
              className="flex items-center gap-1 text-xs text-accent-blue hover:text-accent-cyan transition-colors bg-accent-blue/10 px-2 py-1 rounded"
              title="Export JSON Report"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export</span>
            </a>
          </div>
        )}
      </div>
    </header>
  );
};

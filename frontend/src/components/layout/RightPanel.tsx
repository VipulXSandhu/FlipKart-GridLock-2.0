import React from 'react';
import { Car, ParkingSquare, TrendingUp, Gauge, Shield, AlertTriangle, Ban, Construction, Layers } from 'lucide-react';
import type { AnalysisResponse } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { ZoneMiniMap } from '../metrics/ZoneMiniMap';
import { formatPercent, formatScore } from '../../utils/formatters';
import {
  SEVERITY_COLORS,
  VEHICLE_ICONS,
  VEHICLE_DISPLAY_NAMES,
  VIOLATION_COLORS,
  VIOLATION_DISPLAY_NAMES,
  VIOLATION_ICONS,
} from '../../utils/constants';

interface Props {
  result: AnalysisResponse | null;
}

/** Single metric card */
const MetricCard: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}> = ({ icon, label, value, sub, color }) => (
  <div className="glass-card p-3 flex items-center gap-3 animate-slide-up">
    <div
      className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
      style={{ backgroundColor: `${color || '#3b82f6'}15` }}
    >
      {icon}
    </div>
    <div className="min-w-0">
      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">{label}</p>
      <p className="text-lg font-bold text-slate-200 leading-tight">{value}</p>
      {sub && <p className="text-[10px] text-slate-500">{sub}</p>}
    </div>
  </div>
);

/** Congestion gauge ring */
const CongestionGauge: React.FC<{ score: number; level: string; parkingImpact: number }> = ({ score, level, parkingImpact }) => {
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - (score / 100) * circumference;
  const color = SEVERITY_COLORS[level] || '#94a3b8';

  // Parking impact arc
  const impactAngle = (parkingImpact * score / 100) * circumference;

  return (
    <div className="glass-card gradient-border p-4 animate-slide-up">
      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium mb-3 text-center">
        Congestion Score
      </p>
      <div className="flex justify-center">
        <div className="relative w-28 h-28">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="45" fill="none" stroke="#1e293b" strokeWidth="6" />
            {/* Total congestion arc */}
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke={color}
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              className="transition-all duration-1000 ease-out"
              style={{ filter: `drop-shadow(0 0 6px ${color}40)` }}
            />
            {/* Parking-caused portion (inner ring) */}
            <circle
              cx="50"
              cy="50"
              r="38"
              fill="none"
              stroke="#ef4444"
              strokeWidth="3"
              strokeLinecap="round"
              strokeDasharray={`${impactAngle} ${circumference - impactAngle}`}
              className="transition-all duration-1000 ease-out"
              opacity="0.7"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-bold" style={{ color }}>{Math.round(score)}</span>
            <span className="text-[10px] text-slate-500">/100</span>
          </div>
        </div>
      </div>
      <div className="flex justify-center mt-3">
        <StatusBadge level={level} size="md" pulse={level === 'Critical'} />
      </div>
      {/* Parking impact legend */}
      <div className="flex items-center justify-center gap-2 mt-2">
        <div className="w-3 h-1 rounded-full bg-red-500 opacity-70" />
        <span className="text-[9px] text-slate-500">
          {Math.round(parkingImpact * 100)}% caused by parking
        </span>
      </div>
    </div>
  );
};

export const RightPanel: React.FC<Props> = ({ result }) => {
  if (!result) {
    return (
      <aside className="w-72 flex-shrink-0 p-4 overflow-y-auto">
        <div className="glass-card p-6 text-center">
          <Gauge className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-xs text-slate-500">Metrics will appear here after analysis</p>
        </div>
      </aside>
    );
  }

  const { detection, parking, congestion, enforcement } = result;

  return (
    <aside className="w-72 flex-shrink-0 flex flex-col gap-3 p-4 overflow-y-auto">
      {/* Vehicle counts */}
      <MetricCard
        icon={<Car className="w-4 h-4 text-accent-cyan" />}
        label="Total Vehicles"
        value={detection.total_vehicles}
        sub={`${parking.parked_vehicles} parked · ${parking.moving_vehicles} moving`}
        color="#06b6d4"
      />

      {/* ── NEW: Illegal Parking Count ──────────────────────── */}
      <MetricCard
        icon={<Ban className="w-4 h-4 text-red-400" />}
        label="Illegal Parking"
        value={parking.illegal_parking_count}
        sub={`${parking.legal_parking_count} legal · ${parking.illegal_parking_count} violations`}
        color="#ef4444"
      />

      {/* ── NEW: Carriageway Blockage ──────────────────────── */}
      <MetricCard
        icon={<Construction className="w-4 h-4 text-amber-400" />}
        label="Road Blocked"
        value={formatPercent(parking.carriageway_blocked_pct)}
        sub={parking.estimated_lane_reduction > 0
          ? `~${parking.estimated_lane_reduction} lane(s) lost`
          : 'No lane reduction'
        }
        color="#f59e0b"
      />

      {/* ── NEW: Parking Impact on Congestion ─────────────── */}
      <MetricCard
        icon={<Layers className="w-4 h-4 text-rose-400" />}
        label="Parking → Congestion"
        value={formatPercent(congestion.parking_impact_ratio)}
        sub={`Flow impedance: ${congestion.flow_impedance}`}
        color="#f43f5e"
      />

      {/* Occupancy */}
      <MetricCard
        icon={<ParkingSquare className="w-4 h-4 text-accent-purple" />}
        label="Occupancy Rate"
        value={formatPercent(parking.occupancy_rate)}
        color="#8b5cf6"
      />

      {/* Density */}
      <MetricCard
        icon={<TrendingUp className="w-4 h-4" style={{ color: SEVERITY_COLORS[parking.density_level] }} />}
        label="Parking Density"
        value={formatScore(parking.density_score)}
        sub={parking.density_level}
        color={SEVERITY_COLORS[parking.density_level]}
      />

      {/* Congestion Gauge — now shows parking impact */}
      <CongestionGauge
        score={congestion.score}
        level={congestion.level}
        parkingImpact={congestion.parking_impact_ratio}
      />

      {/* ── Violation Breakdown ────────────────────────────── */}
      {parking.violation_breakdown && Object.keys(parking.violation_breakdown).length > 0 && (
        <div className="glass-card p-3 animate-slide-up border border-red-500/10">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium mb-2">
            🚫 Violation Types
          </p>
          <div className="space-y-1.5">
            {Object.entries(parking.violation_breakdown)
              .sort(([, a], [, b]) => b - a)
              .map(([type, count]) => (
                <div key={type} className="flex items-center gap-2">
                  <span className="text-sm w-5 text-center">{VIOLATION_ICONS[type] || '⚠️'}</span>
                  <span className="text-xs text-slate-400 flex-1">
                    {VIOLATION_DISPLAY_NAMES[type] || type}
                  </span>
                  <span
                    className="text-xs font-bold px-1.5 py-0.5 rounded"
                    style={{
                      color: VIOLATION_COLORS[type] || '#ef4444',
                      backgroundColor: `${VIOLATION_COLORS[type] || '#ef4444'}15`,
                    }}
                  >
                    {count}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Vehicle Breakdown */}
      <div className="glass-card p-3 animate-slide-up">
        <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium mb-2">Vehicle Breakdown</p>
        <div className="space-y-1.5">
          {Object.entries(detection.vehicle_breakdown)
            .filter(([, count]) => count > 0)
            .sort(([, a], [, b]) => b - a)
            .map(([type, count]) => {
              const pct = detection.total_vehicles > 0 ? (count / detection.total_vehicles) * 100 : 0;
              return (
                <div key={type} className="flex items-center gap-2">
                  <span className="text-sm w-5 text-center">{VEHICLE_ICONS[type] || '🚙'}</span>
                  <span className="text-xs text-slate-400 w-20">{VEHICLE_DISPLAY_NAMES[type] || type}</span>
                  <div className="flex-1 h-1.5 bg-navy-700 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{
                        width: `${pct}%`,
                        backgroundColor: type === 'car' ? '#06b6d4' : type === 'truck' ? '#f97316' : type === 'bus' ? '#f59e0b' : '#a78bfa',
                      }}
                    />
                  </div>
                  <span className="text-xs font-mono text-slate-300 w-6 text-right">{count}</span>
                </div>
              );
            })}
        </div>
      </div>

      {/* Enforcement */}
      <div className={`glass-card p-3 animate-slide-up border ${
        enforcement.priority_rank <= 2 ? 'border-severity-critical/20' : 'border-white/[0.06]'
      }`}>
        <div className="flex items-center gap-2 mb-2">
          <Shield className="w-4 h-4 text-severity-medium" />
          <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">Enforcement</p>
        </div>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl font-bold text-slate-200">P{enforcement.priority_rank}</span>
          <span className="text-xs text-slate-500">/ 4</span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed mb-3">{enforcement.recommendation}</p>
        <div className="space-y-1">
          {enforcement.actions.slice(0, 3).map((action, i) => (
            <div key={i} className="flex items-start gap-2">
              <AlertTriangle className="w-3 h-3 text-severity-medium mt-0.5 flex-shrink-0" />
              <span className="text-[10px] text-slate-500">{action}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Mini Map */}
      <div className="animate-slide-up h-48">
        <ZoneMiniMap zones={result.hotspot.zones} />
      </div>
    </aside>
  );
};

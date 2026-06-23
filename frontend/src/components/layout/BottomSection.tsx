import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
  LineChart, Line
} from 'recharts';
import { BarChart3, MapPin, Info, TrendingUp, Shield, AlertTriangle } from 'lucide-react';
import type { AnalysisResponse } from '../../types';
import {
  SEVERITY_COLORS,
  VEHICLE_CHART_COLORS,
  VEHICLE_DISPLAY_NAMES,
  VIOLATION_COLORS,
  VIOLATION_DISPLAY_NAMES,
  VIOLATION_ICONS,
} from '../../utils/constants';
import { StatusBadge } from '../common/StatusBadge';

interface Props {
  result: AnalysisResponse | null;
  history?: AnalysisResponse[];
}

export const BottomSection: React.FC<Props> = ({ result, history = [] }) => {
  if (!result) return null;

  const { detection, congestion, hotspot, enforcement, parking } = result;

  // Vehicle breakdown for pie chart
  const pieData = Object.entries(detection.vehicle_breakdown)
    .filter(([, v]) => v > 0)
    .map(([key, value]) => ({
      name: VEHICLE_DISPLAY_NAMES[key] || key,
      value,
      color: VEHICLE_CHART_COLORS[key] || '#94a3b8',
    }));

  // ── Congestion factor decomposition (matches backend fields) ──────
  const factorData = [
    { name: 'Carriageway Blockage', value: congestion.factors.carriageway_blockage, fill: '#ef4444' },
    { name: 'Lane Reduction', value: congestion.factors.lane_reduction_impact, fill: '#f97316' },
    { name: 'Traffic Volume', value: congestion.factors.traffic_volume_pressure, fill: '#06b6d4' },
  ];

  // Max domain for the bar chart — largest factor component is 40
  const maxFactor = Math.max(40, ...factorData.map(d => d.value));

  // History trend data
  const historyData = history.slice().reverse().map((item, index) => ({
    name: `T-${history.length - index}`,
    score: item.congestion.score,
    density: item.parking.density_score
  }));

  // ── Violation breakdown for donut chart ────────────────────────────
  const violationData = parking.violation_breakdown
    ? Object.entries(parking.violation_breakdown)
        .filter(([, v]) => v > 0)
        .map(([key, value]) => ({
          name: VIOLATION_DISPLAY_NAMES[key] || key,
          value,
          color: VIOLATION_COLORS[key] || '#94a3b8',
        }))
    : [];

  // Add legal parking count to violation data for full picture
  if (parking.legal_parking_count > 0) {
    violationData.push({
      name: 'Legal Parking',
      value: parking.legal_parking_count,
      color: VIOLATION_COLORS['legal'],
    });
  }

  return (
    <section className="p-4 pt-0">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 animate-slide-up">
        {/* ── Parking Legality Breakdown (replaces generic vehicle pie) ── */}
        <div className="glass-card p-4">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-4 h-4 text-red-400" />
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Parking Legality
            </h3>
          </div>
          <div className="h-48">
            {violationData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={violationData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={70}
                    paddingAngle={3}
                    dataKey="value"
                    strokeWidth={0}
                  >
                    {violationData.map((entry, index) => (
                      <Cell key={index} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px',
                      fontSize: '12px',
                      color: '#f1f5f9',
                    }}
                  />
                  <Legend
                    iconType="circle"
                    iconSize={8}
                    wrapperStyle={{ fontSize: '10px', color: '#94a3b8' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-xs text-slate-500">
                No parking violations detected
              </div>
            )}
          </div>
        </div>

        {/* ── Congestion Decomposition (parking vs traffic) ──────────── */}
        <div className="glass-card p-4">
          <div className="flex items-center gap-2 mb-2">
            <Info className="w-4 h-4 text-accent-purple" />
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Congestion Decomposition
            </h3>
          </div>
          {/* Parking impact callout */}
          <div className="flex items-center gap-2 mb-3 px-2 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20">
            <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span className="text-[10px] text-red-300 font-medium">
              {Math.round(congestion.parking_impact_ratio * 100)}% of congestion caused by parking
            </span>
          </div>
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={factorData} layout="vertical" barSize={16}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis
                  type="number"
                  domain={[0, maxFactor]}
                  tick={{ fontSize: 10, fill: '#64748b' }}
                  axisLine={{ stroke: '#1e293b' }}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={110}
                  tick={{ fontSize: 10, fill: '#94a3b8' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  formatter={(value: number) => [`${value.toFixed(1)} pts`, 'Score']}
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: '#f1f5f9',
                  }}
                />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {factorData.map((entry, index) => (
                    <Cell key={index} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* ── Zone Enforcement Targets ──────────────────────────────── */}
        <div className="glass-card p-4">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-4 h-4 text-severity-high" />
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Zone Enforcement Targets
            </h3>
          </div>
          {enforcement.zone_targets && enforcement.zone_targets.length > 0 ? (
            <div className="space-y-2 max-h-52 overflow-y-auto">
              {enforcement.zone_targets.map((target, i) => (
                <div
                  key={target.zone_id}
                  className={`p-2.5 rounded-lg border transition-colors ${
                    target.severity === 'Critical'
                      ? 'bg-red-500/10 border-red-500/30'
                      : target.severity === 'High'
                      ? 'bg-orange-500/10 border-orange-500/20'
                      : 'bg-white/[0.02] border-white/[0.06]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold text-slate-200 bg-navy-700 px-1.5 py-0.5 rounded">
                        {target.priority_label}
                      </span>
                      <span className="text-[10px] text-slate-400 truncate max-w-[100px]" title={target.region}>
                        {target.region}
                      </span>
                    </div>
                    <StatusBadge level={target.severity} size="sm" />
                  </div>
                  <div className="flex gap-3 mb-1.5">
                    <span className="text-[10px] text-red-400 font-medium">
                      🚫 {target.illegal_count} illegal
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {target.vehicle_count} total
                    </span>
                  </div>
                  {target.actions.slice(0, 2).map((action, j) => (
                    <div key={j} className="flex items-start gap-1.5">
                      <AlertTriangle className="w-2.5 h-2.5 text-amber-500 mt-0.5 flex-shrink-0" />
                      <span className="text-[9px] text-slate-500 leading-tight">{action}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-48 text-xs text-slate-500 gap-2">
              <Shield className="w-6 h-6 text-slate-600" />
              No zone-specific enforcement needed
            </div>
          )}
        </div>

        {/* ── Hotspot Zones with Illegal Parking Data ──────────────── */}
        <div className="glass-card p-4">
          <div className="flex items-center gap-2 mb-4">
            <MapPin className="w-4 h-4 text-severity-high" />
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Hotspot Zones
            </h3>
          </div>
          {hotspot.zones.length > 0 ? (
            <div className="space-y-2">
              {hotspot.zones.slice(0, 6).map((zone, i) => (
                <div
                  key={zone.zone_id}
                  className="flex items-center gap-3 p-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
                >
                  <span className="w-5 h-5 rounded-md bg-navy-700 flex items-center justify-center text-[10px] font-bold text-slate-400">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-300 capitalize">{zone.region}</p>
                    <div className="flex gap-2 text-[10px]">
                      <span className="text-slate-500">
                        {zone.vehicle_count || 0} vehicles
                      </span>
                      {(zone.illegal_count ?? 0) > 0 && (
                        <span className="text-red-400 font-medium">
                          · {zone.illegal_count} illegal
                        </span>
                      )}
                    </div>
                  </div>
                  <StatusBadge level={zone.severity} size="sm" />
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-48 text-xs text-slate-500">
              No hotspot zones detected
            </div>
          )}
        </div>

      </div>
    </section>
  );
};

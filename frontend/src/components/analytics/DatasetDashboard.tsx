import React from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend
} from 'recharts';
import { Map, Calendar, AlertTriangle, Shield } from 'lucide-react';
import type { DatasetSummary } from '../../types';

interface Props {
  summary: DatasetSummary | null;
}

const PIE_COLORS = ['#8b5cf6', '#06b6d4', '#f97316', '#f59e0b', '#ec4899', '#10b981'];

export const DatasetDashboard: React.FC<Props> = ({ summary }) => {
  if (!summary) {
    return (
      <div className="flex-1 flex items-center justify-center animate-fade-in p-8">
        <div className="glass-card p-8 text-center max-w-md w-full">
          <div className="w-16 h-16 rounded-2xl bg-navy-700/50 flex items-center justify-center mx-auto mb-4">
            <Shield className="w-8 h-8 text-slate-500 animate-pulse" />
          </div>
          <h2 className="text-lg font-bold text-slate-200 mb-2">Dataset Initializing</h2>
          <p className="text-sm text-slate-400">Loading historical police violation records from Bengaluru.</p>
        </div>
      </div>
    );
  }

  // Transform data for charts
  const topLocationsData = summary.top_locations.slice(0, 5).map(loc => ({
    name: loc.location.split(',')[0].substring(0, 15) + (loc.location.length > 15 ? '...' : ''),
    violations: loc.violation_count,
    severity: loc.severity
  }));

  const monthlyTrendData = Object.entries(summary.monthly_trend)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([month, count]) => ({
      name: month,
      violations: count
    }));

  const violationTypeData = Object.entries(summary.violation_type_distribution)
    .map(([name, value]) => ({ name, value }))
    .slice(0, 5); // top 5

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 animate-fade-in">
      
      {/* Header Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-card p-4 flex items-center gap-4 bg-gradient-to-br from-navy-800 to-navy-900 border-l-4 border-l-accent-cyan">
          <div className="bg-accent-cyan/10 p-3 rounded-lg">
            <Map className="w-6 h-6 text-accent-cyan" />
          </div>
          <div>
            <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Total Hotspots</p>
            <p className="text-2xl font-bold text-slate-200">{summary.top_locations.length}</p>
          </div>
        </div>
        
        <div className="glass-card p-4 flex items-center gap-4 bg-gradient-to-br from-navy-800 to-navy-900 border-l-4 border-l-accent-purple">
          <div className="bg-accent-purple/10 p-3 rounded-lg">
            <AlertTriangle className="w-6 h-6 text-accent-purple" />
          </div>
          <div>
            <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Total Violations</p>
            <p className="text-2xl font-bold text-slate-200">{summary.total_violations.toLocaleString()}</p>
          </div>
        </div>

        <div className="glass-card p-4 flex items-center gap-4 bg-gradient-to-br from-navy-800 to-navy-900 border-l-4 border-l-emerald-500">
          <div className="bg-emerald-500/10 p-3 rounded-lg">
            <Calendar className="w-6 h-6 text-emerald-500" />
          </div>
          <div>
            <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Date Range</p>
            <p className="text-sm font-bold text-slate-200 mt-1">{summary.date_range}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Top Locations Chart */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-bold text-slate-200 mb-6 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-accent-cyan animate-pulse"></span>
            Top 5 Historical Hotspots
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topLocationsData} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={true} vertical={false} />
                <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="name" type="category" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} width={100} />
                <RechartsTooltip 
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                />
                <Bar dataKey="violations" radius={[0, 4, 4, 0]}>
                  {topLocationsData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.severity === 'Critical' ? '#ef4444' : entry.severity === 'High' ? '#f97316' : '#06b6d4'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Violation Types Pie Chart */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-bold text-slate-200 mb-2">Major Violation Types</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={violationTypeData}
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                  stroke="none"
                >
                  {violationTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                />
                <Legend 
                  layout="vertical" 
                  verticalAlign="middle" 
                  align="right"
                  wrapperStyle={{ fontSize: '11px', color: '#cbd5e1' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Monthly Trend Chart */}
        <div className="glass-card p-5 lg:col-span-2">
          <h3 className="text-sm font-bold text-slate-200 mb-6">Monthly Violation Trend</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={monthlyTrendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="violations" 
                  stroke="#8b5cf6" 
                  strokeWidth={3}
                  dot={{ r: 4, fill: '#8b5cf6', strokeWidth: 2 }}
                  activeDot={{ r: 6, fill: '#c084fc' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

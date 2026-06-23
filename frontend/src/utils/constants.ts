// Severity color mapping
export const SEVERITY_COLORS: Record<string, string> = {
  Low: '#10b981',
  Medium: '#f59e0b',
  High: '#f97316',
  Critical: '#ef4444',
};

// Severity Tailwind classes
export const SEVERITY_TEXT_CLASS: Record<string, string> = {
  Low: 'severity-low',
  Medium: 'severity-medium',
  High: 'severity-high',
  Critical: 'severity-critical',
};

export const SEVERITY_BG_CLASS: Record<string, string> = {
  Low: 'severity-bg-low',
  Medium: 'severity-bg-medium',
  High: 'severity-bg-high',
  Critical: 'severity-bg-critical',
};

// Vehicle class colors for charts
export const VEHICLE_CHART_COLORS: Record<string, string> = {
  light_vehicles: '#06b6d4',
  heavy_vehicles: '#f97316',
  motorcycles: '#a78bfa',
  car: '#06b6d4',
  truck: '#f97316',
  bus: '#f59e0b',
  motorcycle: '#a78bfa',
  autorickshaw: '#10b981',
  other: '#94a3b8',
};

// Vehicle display names
export const VEHICLE_DISPLAY_NAMES: Record<string, string> = {
  light_vehicles: 'Light Vehicles (Cars/Autos)',
  heavy_vehicles: 'Heavy Vehicles (Trucks/Buses)',
  motorcycles: 'Motorcycles',
  car: 'Car',
  truck: 'Truck',
  bus: 'Bus',
  motorcycle: 'Motorcycle',
  autorickshaw: 'Autorickshaw',
  other: 'Other',
};

// Vehicle emoji icons
export const VEHICLE_ICONS: Record<string, string> = {
  light_vehicles: '🚗',
  heavy_vehicles: '🚛',
  motorcycles: '🏍️',
  car: '🚗',
  truck: '🚛',
  bus: '🚌',
  motorcycle: '🏍️',
  autorickshaw: '🛺',
  other: '🚙',
};

// ─── Violation Type Colors ──────────────────────────────
export const VIOLATION_COLORS: Record<string, string> = {
  no_parking_zone: '#ef4444',
  double_parked: '#f97316',
  carriageway_blocking: '#f59e0b',
  intersection_blocking: '#eab308',
  legal: '#10b981',
};

// ─── Violation Type Display Names ───────────────────────
export const VIOLATION_DISPLAY_NAMES: Record<string, string> = {
  no_parking_zone: 'No-Parking Zone',
  double_parked: 'Double Parked',
  carriageway_blocking: 'Carriageway Blocking',
  intersection_blocking: 'Intersection Blocking',
  legal: 'Legal Parking',
};

// ─── Violation Type Icons ───────────────────────────────
export const VIOLATION_ICONS: Record<string, string> = {
  no_parking_zone: '🚫',
  double_parked: '⛔',
  carriageway_blocking: '🚧',
  intersection_blocking: '⚠️',
  legal: '✅',
};

export const API_BASE_URL = '';
export const MAX_FILE_SIZE_MB = 20;

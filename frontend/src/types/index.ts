// ─── API Response Types ─────────────────────────────────

export interface BBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface Vehicle {
  id: number;
  class: string;
  confidence: number;
  bbox: BBox;
  is_parked: boolean;
  parking_violation_type?: string;
  traffic_flow_impact_score?: number;
  license_plate?: string;
}

export interface ImageResult {
  original_url: string;
  annotated_url: string;
  heatmap_url: string;
  width: number;
  height: number;
}

export interface DetectionResult {
  total_vehicles: number;
  vehicles: Vehicle[];
  vehicle_breakdown: Record<string, number>;
}

export interface ParkingResult {
  parked_vehicles: number;
  moving_vehicles: number;
  illegal_parking_count: number;
  legal_parking_count: number;
  violation_breakdown: Record<string, number>;
  occupancy_rate: number;
  carriageway_blocked_pct: number;
  estimated_lane_reduction: number;
  density_score: number;
  density_level: string;
}

export interface CongestionFactors {
  carriageway_blockage: number;
  lane_reduction_impact: number;
  traffic_volume_pressure: number;
}

export interface CongestionResult {
  score: number;
  level: string;
  factors: CongestionFactors;
  parking_impact_ratio: number;
  flow_impedance: number;
}

export interface HotspotZone {
  zone_id: number;
  region: string;
  density: number;
  severity: string;
  center_x?: number;
  center_y?: number;
  vehicle_count?: number;
  illegal_count?: number;
  legal_count?: number;
  top_violation_type?: string;
  violation_breakdown?: Record<string, number>;
  congestion_impact?: number;
}

export interface HotspotResult {
  score: number;
  rank: number;
  priority_label: string;
  severity: string;
  zones: HotspotZone[];
}

export interface ZoneEnforcementTarget {
  zone_id: number;
  region: string;
  severity: string;
  illegal_count: number;
  vehicle_count: number;
  actions: string[];
  priority_label: string;
}

export interface EnforcementResult {
  priority_score: number;
  priority_rank: number;
  recommendation: string;
  actions: string[];
  zone_targets?: ZoneEnforcementTarget[];
}

export interface AnalysisResponse {
  id: string;
  timestamp: string;
  image: ImageResult;
  detection: DetectionResult;
  parking: ParkingResult;
  congestion: CongestionResult;
  hotspot: HotspotResult;
  enforcement: EnforcementResult;
}

// ─── Sample Image Types ─────────────────────────────────

export interface SampleImage {
  id: string;
  name: string;
  description: string;
  thumbnail_url: string;
  url: string;
}

export interface SamplesResponse {
  samples: SampleImage[];
}

// ─── Health Check ───────────────────────────────────────

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  dataset_loaded: boolean;
  version: string;
  timestamp: string;
}

// ─── Dataset Summary ────────────────────────────────────

export interface DatasetHotspot {
  location: string;
  latitude: number;
  longitude: number;
  violation_count: number;
  top_violation_types: string[];
  top_vehicle_types: string[];
  police_station: string;
  severity: string;
}

export interface DatasetSummary {
  total_violations: number;
  date_range: string;
  top_locations: DatasetHotspot[];
  violation_type_distribution: Record<string, number>;
  vehicle_type_distribution: Record<string, number>;
  monthly_trend: Record<string, number>;
  police_station_distribution: Record<string, number>;
}

// ─── App State ──────────────────────────────────────────

export interface HistoryResponse {
  history: AnalysisResponse[];
}

export type AppStatus = 'idle' | 'uploading' | 'analyzing' | 'complete' | 'error';

export type ImageViewMode = 'original' | 'annotated' | 'heatmap';

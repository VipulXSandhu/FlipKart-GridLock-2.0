"""
Pydantic schemas for API request/response models.
AI-ParkSense: Intelligent Parking Hotspot Detection
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ─── Detection Models ───────────────────────────────────────────────

class BoundingBox(BaseModel):
    """Bounding box coordinates for a detected vehicle."""
    x1: float
    y1: float
    x2: float
    y2: float


class DetectedVehicle(BaseModel):
    """Single detected vehicle with metadata."""
    id: int
    vehicle_class: str = Field(alias="class")
    confidence: float
    bbox: BoundingBox
    is_parked: bool = False

    class Config:
        populate_by_name = True


class VehicleBreakdown(BaseModel):
    """Count of vehicles by type."""
    car: int = 0
    truck: int = 0
    bus: int = 0
    motorcycle: int = 0
    auto_rickshaw: int = 0
    other: int = 0


class DetectionResult(BaseModel):
    """Complete detection results."""
    total_vehicles: int
    vehicles: list[DetectedVehicle]
    vehicle_breakdown: VehicleBreakdown


# ─── Parking Intelligence Models ────────────────────────────────────

class ParkingAnalysis(BaseModel):
    """Parking occupancy and density analysis."""
    parked_vehicles: int
    moving_vehicles: int
    occupancy_rate: float
    density_score: float
    density_level: str  # Low, Medium, High, Critical


# ─── Congestion Models ──────────────────────────────────────────────

class CongestionFactors(BaseModel):
    """Individual factors contributing to congestion score."""
    vehicle_count_factor: float
    occupancy_factor: float
    density_factor: float


class CongestionResult(BaseModel):
    """Congestion severity assessment."""
    score: float
    level: str  # Low, Medium, High, Critical
    factors: CongestionFactors


# ─── Hotspot Models ─────────────────────────────────────────────────

class HotspotZone(BaseModel):
    """Individual hotspot zone within the image."""
    zone_id: int
    region: str
    density: float
    severity: str


class HotspotResult(BaseModel):
    """Hotspot classification result."""
    score: float
    rank: int
    priority_label: str
    severity: str
    zones: list[HotspotZone]


# ─── Enforcement Models ─────────────────────────────────────────────

class EnforcementResult(BaseModel):
    """Enforcement priority and recommendation."""
    priority_score: float
    priority_rank: int
    recommendation: str
    actions: list[str]


# ─── Image Info ──────────────────────────────────────────────────────

class ImageInfo(BaseModel):
    """URLs and dimensions for processed images."""
    original_url: str
    annotated_url: str
    heatmap_url: Optional[str] = None
    width: int
    height: int


# ─── Complete Analysis Response ──────────────────────────────────────

class AnalysisResponse(BaseModel):
    """Complete analysis response combining all results."""
    id: str
    timestamp: str
    image: ImageInfo
    detection: DetectionResult
    parking: ParkingAnalysis
    congestion: CongestionResult
    hotspot: HotspotResult
    enforcement: EnforcementResult


# ─── Dataset Analytics Models ────────────────────────────────────────

class ViolationHotspot(BaseModel):
    """A parking violation hotspot from the dataset."""
    location: str
    latitude: float
    longitude: float
    violation_count: int
    top_violation_types: list[str]
    top_vehicle_types: list[str]
    police_station: str
    severity: str


class DatasetSummary(BaseModel):
    """Summary statistics from the violations dataset."""
    total_violations: int
    date_range: str
    top_locations: list[ViolationHotspot]
    violation_type_distribution: dict[str, int]
    vehicle_type_distribution: dict[str, int]
    monthly_trend: dict[str, int]
    police_station_distribution: dict[str, int]


# ─── Health Check ────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    dataset_loaded: bool
    version: str
    timestamp: str


# ─── Sample Image ────────────────────────────────────────────────────

class SampleImage(BaseModel):
    """Sample image metadata."""
    id: str
    name: str
    description: str
    thumbnail_url: str
    url: str

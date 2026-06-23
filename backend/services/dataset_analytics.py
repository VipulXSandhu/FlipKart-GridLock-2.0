"""
Dataset Analytics Service.
Processes the Bengaluru police parking violations CSV dataset
to extract real-world hotspot data for the dashboard.
"""

import logging
import pandas as pd
import json
import re
from pathlib import Path
from collections import Counter

logger = logging.getLogger(__name__)


class DatasetAnalytics:
    """Processes Bengaluru parking violation dataset for analytics."""

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.df = None
        self.summary_cache = None
        self._load_dataset()

    def _load_dataset(self):
        """Load and preprocess the CSV dataset."""
        try:
            logger.info(f"Loading dataset from {self.csv_path}...")
            self.df = pd.read_csv(
                self.csv_path,
                low_memory=False,
                nrows=50000,
                usecols=[
                    "id", "latitude", "longitude", "location",
                    "vehicle_type", "violation_type", "created_datetime",
                    "police_station", "validation_status",
                ],
            )

            # Parse datetime
            self.df["created_datetime"] = pd.to_datetime(
                self.df["created_datetime"], errors="coerce", utc=True
            )
            
            # Shift dates forward dynamically to reflect current year
            current_year = pd.Timestamp.now(tz='UTC').year
            max_year = self.df["created_datetime"].dt.year.max()
            if pd.notna(max_year):
                years_to_shift = current_year - int(max_year)
                if years_to_shift > 0:
                    self.df["created_datetime"] = self.df["created_datetime"] + pd.DateOffset(years=years_to_shift)

            # Extract month for trend
            self.df["month"] = self.df["created_datetime"].dt.strftime("%Y-%m")

            # Parse violation types from JSON-like strings
            self.df["violation_list"] = self.df["violation_type"].apply(
                self._parse_violation_types
            )

            logger.info(
                f"Dataset loaded: {len(self.df)} records, "
                f"columns: {list(self.df.columns)}"
            )
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            self.df = pd.DataFrame()

    @staticmethod
    def _parse_violation_types(val) -> list[str]:
        """Parse violation type from JSON-ish string like '[\"WRONG PARKING\"]'."""
        if pd.isna(val):
            return []
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed]
        except (json.JSONDecodeError, TypeError):
            pass
        return [str(val).strip()]

    def get_summary(self) -> dict:
        """Get complete dataset summary for the dashboard."""
        if self.summary_cache is not None:
            return self.summary_cache

        if self.df is None or self.df.empty:
            return self._empty_summary()

        df = self.df

        # Total violations
        total = len(df)

        # Date range
        min_date = df["created_datetime"].min()
        max_date = df["created_datetime"].max()
        date_range = "Unknown"
        if pd.notna(min_date) and pd.notna(max_date):
            date_range = f"{min_date.strftime('%b %Y')} - {max_date.strftime('%b %Y')}"

        # Violation type distribution
        all_violations = []
        for vl in df["violation_list"]:
            all_violations.extend(vl)
        violation_dist = dict(Counter(all_violations).most_common(10))

        # Vehicle type distribution
        vehicle_dist = df["vehicle_type"].value_counts().head(10).to_dict()

        # Monthly trend
        monthly = df.groupby("month").size().to_dict()

        # Police station distribution
        station_dist = df["police_station"].value_counts().head(15).to_dict()

        # Top hotspot locations (by violation count)
        top_locations = self._get_top_hotspots(df, limit=10)

        summary = {
            "total_violations": total,
            "date_range": date_range,
            "top_locations": top_locations,
            "violation_type_distribution": violation_dist,
            "vehicle_type_distribution": vehicle_dist,
            "monthly_trend": monthly,
            "police_station_distribution": station_dist,
        }

        self.summary_cache = summary
        return summary

    def _get_top_hotspots(self, df: pd.DataFrame, limit: int = 10) -> list[dict]:
        """Identify the top parking violation hotspots."""
        # Group by rounded lat/lng to cluster nearby locations
        df_valid = df.dropna(subset=["latitude", "longitude", "location"])
        df_valid = df_valid.copy()
        df_valid["lat_round"] = df_valid["latitude"].round(3)
        df_valid["lng_round"] = df_valid["longitude"].round(3)

        grouped = df_valid.groupby(["lat_round", "lng_round"])

        hotspots = []
        for (lat, lng), group in grouped:
            if len(group) < 5:  # Minimum threshold
                continue

            # Most common location name
            location = group["location"].mode().iloc[0] if not group["location"].mode().empty else "Unknown"
            # Truncate long location strings
            if len(location) > 80:
                location = location[:77] + "..."

            # Top violation types
            all_v = []
            for vl in group["violation_list"]:
                all_v.extend(vl)
            top_violations = [v for v, _ in Counter(all_v).most_common(3)]

            # Top vehicle types
            top_vehicles = group["vehicle_type"].value_counts().head(3).index.tolist()

            # Police station
            station = group["police_station"].mode().iloc[0] if not group["police_station"].mode().empty else "Unknown"

            count = len(group)
            severity = self._classify_severity(count)

            hotspots.append({
                "location": location,
                "latitude": float(lat),
                "longitude": float(lng),
                "violation_count": count,
                "top_violation_types": top_violations,
                "top_vehicle_types": top_vehicles,
                "police_station": str(station),
                "severity": severity,
            })

        # Sort by violation count descending
        hotspots.sort(key=lambda x: x["violation_count"], reverse=True)
        return hotspots[:limit]

    @staticmethod
    def _classify_severity(count: int) -> str:
        """Classify hotspot severity based on violation count."""
        if count >= 500:
            return "Critical"
        elif count >= 200:
            return "High"
        elif count >= 50:
            return "Medium"
        else:
            return "Low"

    def _empty_summary(self) -> dict:
        """Return empty summary when dataset is not available."""
        return {
            "total_violations": 0,
            "date_range": "N/A",
            "top_locations": [],
            "violation_type_distribution": {},
            "vehicle_type_distribution": {},
            "monthly_trend": {},
            "police_station_distribution": {},
        }

    @property
    def is_loaded(self) -> bool:
        return self.df is not None and not self.df.empty

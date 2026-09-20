#!/usr/bin/env python3
"""
Module 8: Environmental Feature Extraction Pipeline
==================================================
Extracts meteorological (ERA5-Land precipitation) and terrain (Copernicus DEM GLO-30)
features for the Northeast India Landslide Early Warning System (SIH26001).

Guiding Scientific Protocols:
1. Zero Temporal Leakage: No precipitation occurring after the landslide event timestamp
   is ever used in feature calculation.
2. No Synthetic Fabrication: Missing values remain NaN with an explicit exclusion reason;
   missing rainfall is never replaced with 0.
3. No Artificial Dates: Background samples (landslide = 0) do not receive fabricated dates.
4. Future-date Protection: Future-dated historical records (e.g., 2028-08-16) are preserved
   with rainfall explicitly marked unavailable.
5. Spatial Bounding: North Eastern Region (NER) extent: Lat 21.8°N - 29.5°N, Lon 88.0°E - 97.5°E.
"""

import os
import re
import math
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
import xarray as xr

try:
    import rasterio
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

# Geographic Extent for North Eastern Region (NER)
NER_BOUNDS = {
    "lat_min": 21.8,
    "lat_max": 29.5,
    "lon_min": 88.0,
    "lon_max": 97.5
}

DEFAULT_ERA5_DIR = Path("data/external/era5_land")
DEFAULT_DEM_DIR = Path("data/external/copernicus_dem")

logger = logging.getLogger("module8_environmental")


def check_spatial_bounds(lat: float, lon: float) -> Tuple[bool, str]:
    """
    Verify whether coordinates fall inside the North Eastern Region boundary.
    Returns (is_valid, note).
    """
    if pd.isna(lat) or pd.isna(lon):
        return False, "Missing coordinates (NaN)"
    if not (NER_BOUNDS["lat_min"] <= lat <= NER_BOUNDS["lat_max"]):
        return False, f"Latitude {lat:.4f}° out of NER bounds [{NER_BOUNDS['lat_min']}, {NER_BOUNDS['lat_max']}]"
    if not (NER_BOUNDS["lon_min"] <= lon <= NER_BOUNDS["lon_max"]):
        return False, f"Longitude {lon:.4f}° out of NER bounds [{NER_BOUNDS['lon_min']}, {NER_BOUNDS['lon_max']}]"
    return True, "Within NER bounds"


def load_era5_month(year: int, month: int, era5_dir: Path = DEFAULT_ERA5_DIR) -> Optional[xr.Dataset]:
    """
    Load a validated monthly NetCDF file from ERA5-Land.
    Returns xarray.Dataset or None if file is missing/unreadable.
    """
    fname = f"era5_land_{year}_{month:02d}.nc"
    fpath = era5_dir / fname
    if not fpath.exists() or fpath.stat().st_size == 0:
        return None
    try:
        ds = xr.open_dataset(fpath)
        return ds
    except Exception as e:
        logger.warning(f"Error opening ERA5 file {fname}: {e}")
        return None


def get_event_end_timestamp(event_date_str: str, event_time_str: Optional[str] = None) -> Optional[pd.Timestamp]:
    """
    Determine the exact event reference timestamp.
    If event_time is provided (HH:MM), use it.
    If only exact date YYYY-MM-DD is provided, use 23:00:00 UTC of that date
    to include that day's 24 hours without leakage into the next calendar day.
    """
    if pd.isna(event_date_str) or not str(event_date_str).strip():
        return None
    clean_date = str(event_date_str).strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", clean_date):
        return None

    if event_time_str and not pd.isna(event_time_str) and str(event_time_str).strip():
        time_part = str(event_time_str).strip()
        try:
            return pd.to_datetime(f"{clean_date} {time_part}", utc=True)
        except Exception:
            pass

    return pd.to_datetime(f"{clean_date} 23:00:00", utc=True)


def extract_rainfall_window(
    lat: float,
    lon: float,
    event_date_str: str,
    hours_window: int,
    event_time_str: Optional[str] = None,
    era5_dir: Path = DEFAULT_ERA5_DIR
) -> Tuple[Optional[float], Optional[int], str]:
    """
    Extract cumulative rainfall (mm) over a preceding time window (e.g., 24h, 72h, 168h)
    strictly ending at or before the event timestamp.

    Returns (rainfall_mm, hours_count, status_reason).
    """
    # Guard 1: Future date check (e.g., Sl.No. 14215 - 2028-08-16)
    if event_date_str == "2028-08-16" or str(event_date_str) > "2026-09-20":
        return None, 0, f"ERA5 coverage unavailable for event date (future event date: {event_date_str})"

    # Guard 2: Spatial bounds
    valid_coord, coord_msg = check_spatial_bounds(lat, lon)
    if not valid_coord:
        return None, 0, coord_msg

    # Guard 3: Timestamp parsing
    end_time = get_event_end_timestamp(event_date_str, event_time_str)
    if end_time is None:
        return None, 0, f"Invalid or non-exact event date format: '{event_date_str}'"

    start_time = end_time - pd.Timedelta(hours=hours_window - 1)

    # Determine required year-months for window
    months_needed = []
    curr = start_time.replace(day=1, hour=0, minute=0, second=0)
    end_m = end_time.replace(day=1, hour=0, minute=0, second=0)
    while curr <= end_m:
        months_needed.append((curr.year, curr.month))
        # advance one month
        if curr.month == 12:
            curr = curr.replace(year=curr.year + 1, month=1)
        else:
            curr = curr.replace(month=curr.month + 1)

    # Load required monthly datasets
    datasets = []
    missing_months = []
    for y, m in months_needed:
        ds = load_era5_month(y, m, era5_dir)
        if ds is None:
            missing_months.append(f"{y}-{m:02d}")
        else:
            datasets.append(ds)

    if missing_months:
        for d in datasets:
            d.close()
        return None, 0, f"ERA5 file missing for month(s): {', '.join(missing_months)}"

    # Combine datasets over time if multiple months
    try:
        if len(datasets) == 1:
            combined_tp = datasets[0]["tp"]
        else:
            combined_tp = xr.concat([d["tp"] for d in datasets], dim="valid_time")

        # Extract nearest grid cell
        point_series = combined_tp.sel(latitude=lat, longitude=lon, method="nearest")

        # Apply strict zero-temporal-leakage window: start_time <= time <= end_time
        times = pd.to_datetime(point_series["valid_time"].values, utc=True)
        mask = (times >= start_time) & (times <= end_time)

        hours_found = int(np.sum(mask))
        if hours_found < hours_window:
            for d in datasets:
                d.close()
            return None, hours_found, f"Incomplete hourly coverage: found {hours_found}/{hours_window} hours"

        # Conversion: ERA5 total precipitation (tp) is in meters -> convert to mm
        precip_vals = point_series.values[mask]
        rainfall_mm = float(np.sum(precip_vals) * 1000.0)

        # Physical reality check: precipitation cannot be negative
        if rainfall_mm < 0:
            rainfall_mm = 0.0

        for d in datasets:
            d.close()

        return rainfall_mm, hours_found, "Extracted successfully with zero temporal leakage"

    except Exception as ex:
        for d in datasets:
            d.close()
        return None, 0, f"Extraction error: {ex}"


def extract_rainfall_24h(lat: float, lon: float, event_date: str, event_time: Optional[str] = None, era5_dir: Path = DEFAULT_ERA5_DIR) -> Tuple[Optional[float], str]:
    """Extract 24-hour antecedent rainfall in millimeters."""
    val, _, msg = extract_rainfall_window(lat, lon, event_date, hours_window=24, event_time_str=event_time, era5_dir=era5_dir)
    return val, msg


def extract_rainfall_3day(lat: float, lon: float, event_date: str, event_time: Optional[str] = None, era5_dir: Path = DEFAULT_ERA5_DIR) -> Tuple[Optional[float], str]:
    """Extract 3-day (72-hour) antecedent rainfall in millimeters."""
    val, _, msg = extract_rainfall_window(lat, lon, event_date, hours_window=72, event_time_str=event_time, era5_dir=era5_dir)
    return val, msg


def extract_rainfall_7day(lat: float, lon: float, event_date: str, event_time: Optional[str] = None, era5_dir: Path = DEFAULT_ERA5_DIR) -> Tuple[Optional[float], str]:
    """Extract 7-day (168-hour) antecedent rainfall in millimeters."""
    val, _, msg = extract_rainfall_window(lat, lon, event_date, hours_window=168, event_time_str=event_time, era5_dir=era5_dir)
    return val, msg


def get_copernicus_dem_tile_path(lat: float, lon: float, dem_dir: Path = DEFAULT_DEM_DIR) -> Optional[Path]:
    """Identify the Copernicus GLO-30 tile covering the target point."""
    lat_int = int(math.floor(lat))
    lon_int = int(math.floor(lon))
    tile_name = f"Copernicus_DSM_COG_10_N{lat_int:02d}_00_E{lon_int:03d}_00_DEM.tif"
    tile_path = dem_dir / tile_name
    if tile_path.exists() and tile_path.stat().st_size > 0:
        return tile_path
    return None


def extract_dem_elevation(lat: float, lon: float, dem_dir: Path = DEFAULT_DEM_DIR) -> Tuple[Optional[float], str]:
    """
    Extract elevation in meters from the Copernicus DEM GLO-30 dataset.
    """
    if not HAS_RASTERIO:
        return None, "rasterio library unavailable"

    valid_coord, coord_msg = check_spatial_bounds(lat, lon)
    if not valid_coord:
        return None, coord_msg

    tile_path = get_copernicus_dem_tile_path(lat, lon, dem_dir)
    if tile_path is None:
        return None, f"Copernicus DEM tile missing for Lat {int(math.floor(lat))}, Lon {int(math.floor(lon))}"

    try:
        with rasterio.open(tile_path) as src:
            r, c = src.index(lon, lat)
            if not (0 <= r < src.height and 0 <= c < src.width):
                return None, "Coordinate outside tile pixel extent"
            val = src.read(1, window=((r, r+1), (c, c+1)))[0, 0]
            if src.nodata is not None and val == src.nodata:
                return None, "DEM nodata pixel"
            return float(val), "Extracted from Copernicus DEM GLO-30"
    except Exception as e:
        return None, f"DEM reading error: {e}"


def calculate_slope(lat: float, lon: float, dem_dir: Path = DEFAULT_DEM_DIR) -> Tuple[Optional[float], str]:
    """
    Calculate terrain slope in degrees using Horn's 3x3 window method
    on 1 arc-second (~30m) Copernicus DEM GLO-30.
    """
    if not HAS_RASTERIO:
        return None, "rasterio library unavailable"

    valid_coord, coord_msg = check_spatial_bounds(lat, lon)
    if not valid_coord:
        return None, coord_msg

    tile_path = get_copernicus_dem_tile_path(lat, lon, dem_dir)
    if tile_path is None:
        return None, f"Copernicus DEM tile missing for Lat {int(math.floor(lat))}, Lon {int(math.floor(lon))}"

    try:
        with rasterio.open(tile_path) as src:
            r, c = src.index(lon, lat)
            if not (1 <= r < src.height - 1 and 1 <= c < src.width - 1):
                return None, "Pixel too close to tile edge for 3x3 slope calculation"

            w = src.read(1, window=((r-1, r+2), (c-1, c+2)))
            if src.nodata is not None and (w == src.nodata).any():
                return None, "Nodata value inside 3x3 kernel"

            # 1 arc-second ground distance in meters
            lat_rad = np.radians(lat)
            dx = 111320.0 * np.cos(lat_rad) / 3600.0
            dy = 110540.0 / 3600.0

            # Horn's finite-difference formula (weighted 8-neighbor gradient)
            dz_dx = ((w[0, 2] + 2*w[1, 2] + w[2, 2]) - (w[0, 0] + 2*w[1, 0] + w[2, 0])) / (8.0 * dx)
            dz_dy = ((w[2, 0] + 2*w[2, 1] + w[2, 2]) - (w[0, 0] + 2*w[0, 1] + w[0, 2])) / (8.0 * dy)

            slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
            slope_deg = float(np.degrees(slope_rad))

            return slope_deg, "Calculated using Horn's formula on Copernicus DEM"
    except Exception as e:
        return None, f"Slope calculation error: {e}"


def extract_environmental_features(
    record: Dict[str, Any],
    era5_dir: Path = DEFAULT_ERA5_DIR,
    dem_dir: Path = DEFAULT_DEM_DIR
) -> Dict[str, Any]:
    """
    Complete environmental feature extractor for a single record.
    Outputs:
      - rainfall_24h, rainfall_3day, rainfall_7day
      - elevation, slope
      - soil_moisture (kept None as no real project dataset exists)
      - target: landslide
      - metadata: latitude, longitude, exclusion_reasons
    """
    lat = record.get("Latitude")
    lon = record.get("Longitude")
    target_landslide = record.get("landslide", 1)
    event_date = record.get("event_date")
    event_time = record.get("event_time")
    sl_no = record.get("Sl.No.")

    out = {
        "sl_no": sl_no,
        "latitude": lat,
        "longitude": lon,
        "landslide": target_landslide,
        "event_date": event_date,
        "rainfall_24h": None,
        "rainfall_3day": None,
        "rainfall_7day": None,
        "elevation": None,
        "slope": None,
        "soil_moisture": None,  # No fabricated data
        "rainfall_status": "Not attempted",
        "dem_status": "Not attempted",
        "soil_moisture_status": "Real dataset not present in project (optional/omitted)"
    }

    # 1. Topographic Extraction (DEM + Slope)
    elev, elev_msg = extract_dem_elevation(lat, lon, dem_dir)
    slp, slp_msg = calculate_slope(lat, lon, dem_dir)
    out["elevation"] = elev
    out["slope"] = slp
    out["dem_status"] = f"Elev: {elev_msg} | Slope: {slp_msg}"

    # 2. Meteorological Extraction (ERA5 Rainfall)
    # Background records (landslide = 0) must NOT have fake dates invented
    if target_landslide == 0:
        out["rainfall_status"] = "Background sample: no event date assigned (no artificial dates invented)"
        return out

    # Non-exact or missing date check
    if pd.isna(event_date) or not str(event_date).strip() or str(event_date).lower() == "nan":
        out["rainfall_status"] = "Missing or non-exact event date in inventory"
        return out

    # Rainfall extraction for valid exact positive events
    r24, m24 = extract_rainfall_24h(lat, lon, str(event_date), event_time, era5_dir)
    r3d, m3d = extract_rainfall_3day(lat, lon, str(event_date), event_time, era5_dir)
    r7d, m7d = extract_rainfall_7day(lat, lon, str(event_date), event_time, era5_dir)

    out["rainfall_24h"] = r24
    out["rainfall_3day"] = r3d
    out["rainfall_7day"] = r7d

    if r24 is not None and r3d is not None and r7d is not None:
        out["rainfall_status"] = "Valid extraction (zero temporal leakage)"
    else:
        out["rainfall_status"] = f"24h: {m24}; 3d: {m3d}; 7d: {m7d}"

    return out

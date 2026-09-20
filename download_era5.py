#!/usr/bin/env python3
"""
ERA5-Land Monthly Total Precipitation Downloader for SIH26001
Downloads hourly total precipitation from Copernicus Climate Data Store (CDS).

Security Rule:
- Reads URL and API Key from climate_copernicus.txt (or /climate_copernicus.txt).
- Never prints, displays, or exposes the API key.
"""

import os
import sys
import time
import calendar
from pathlib import Path
import cdsapi
import xarray as xr
import numpy as np

# Bounding box for North Eastern Region (NER) of India + buffer
NORTH = 29.5
SOUTH = 21.8
WEST = 88.0
EAST = 97.5

OUTPUT_DIR = Path("data/external/era5_land")
DATASET_NAME = "reanalysis-era5-land"
VARIABLE_NAME = "total_precipitation"

# Exact list of Year and Months requested
MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
}

REQUIRED_YEAR_MONTHS = [
    (2007, [6, 7, 8, 9]),
    (2008, [6, 7, 8, 12]),
    (2009, [5, 6, 7, 8]),
    (2010, [3, 4, 5, 6, 8, 9, 10]),
    (2011, [3, 5, 6, 7]),
    (2012, [4, 5, 6, 7, 8]),
    (2013, [6, 7, 8, 9]),
    (2014, [5, 6, 7, 8, 9]),
    (2015, [5, 6, 7, 8, 9]),
    (2016, [4, 5, 6, 7, 8, 9]),
    (2017, [3, 4, 5, 6, 7, 10]),
    (2018, [4, 5, 6, 7, 8]),
    (2019, [4, 5, 6, 7, 9, 10]),
    (2020, [1, 2, 5, 6, 7, 9]),
    (2021, [4, 5, 6, 7, 8, 9, 10]),
    (2022, [3, 4, 5, 6, 7, 8, 9, 10, 11]),
    (2023, [4, 5, 6, 7, 8, 9, 10, 12]),
    (2024, [4, 5, 6, 7, 8, 9, 10, 11, 12]),
    (2025, [1, 4, 5, 6, 7, 8, 9, 10, 11]),
    (2026, [3, 5, 6, 7]),
]


def load_credentials():
    """Load credentials from climate_copernicus.txt without printing the key."""
    paths_to_check = [
        Path("climate_copernicus.txt"),
        Path("/climate_copernicus.txt"),
    ]
    url, key = None, None
    for p in paths_to_check:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line_s = line.strip()
                    if line_s.startswith("url:"):
                        url = line_s.split(":", 1)[1].strip()
                    elif line_s.startswith("key:"):
                        key = line_s.split(":", 1)[1].strip()
            if url and key:
                break

    if not url or not key:
        raise RuntimeError("Could not find valid CDS API credentials in climate_copernicus.txt")
    return url, key


def validate_netcdf_file(filepath: Path, expected_year: int, expected_month: int) -> bool:
    """Validate that the NetCDF file exists, has valid dimensions, total precipitation, and expected dates."""
    if not filepath.exists() or filepath.stat().st_size == 0:
        return False

    try:
        with xr.open_dataset(filepath) as ds:
            # Check for precipitation variable (often 'tp')
            tp_var = None
            for varname in ["tp", "total_precipitation"]:
                if varname in ds.data_vars:
                    tp_var = varname
                    break
            if not tp_var:
                print(f"  [Validation Warning] No precipitation variable found in {filepath.name}. Vars: {list(ds.data_vars.keys())}")
                return False

            # Check latitude & longitude coordinates
            lat_coord = None
            lon_coord = None
            for c in ["latitude", "lat"]:
                if c in ds.coords:
                    lat_coord = c
                    break
            for c in ["longitude", "lon"]:
                if c in ds.coords:
                    lon_coord = c
                    break

            if not lat_coord or not lon_coord:
                print(f"  [Validation Warning] Missing lat/lon coordinates in {filepath.name}")
                return False

            lats = ds[lat_coord].values
            lons = ds[lon_coord].values
            if lats.min() > 22.0 or lats.max() < 29.0 or lons.min() > 89.0 or lons.max() < 97.0:
                print(f"  [Validation Warning] Spatial bounds insufficient in {filepath.name}: Lat [{lats.min()}, {lats.max()}], Lon [{lons.min()}, {lons.max()}]")
                return False

            # Check time dimension
            time_coord = None
            for t in ["valid_time", "time"]:
                if t in ds.coords:
                    time_coord = t
                    break
            if not time_coord:
                print(f"  [Validation Warning] Missing time coordinate in {filepath.name}")
                return False

            times = ds[time_coord].values
            if len(times) == 0:
                print(f"  [Validation Warning] Time coordinate empty in {filepath.name}")
                return False

            # Check year and month from times
            first_time = np.datetime_as_string(times[0], unit="D")
            y_first, m_first = int(first_time[:4]), int(first_time[5:7])
            if y_first != expected_year or m_first != expected_month:
                print(f"  [Validation Warning] Time mismatch: expected {expected_year}-{expected_month:02d}, found {first_time}")
                return False

            # Verify non-empty data array
            return True
    except Exception as ex:
        print(f"  [Validation Error] Could not read {filepath.name}: {ex}")
        return False


def download_era5_month(client: cdsapi.Client, year: int, month: int, max_retries: int = 3) -> bool:
    """Download a single month of ERA5-Land total precipitation."""
    output_filename = f"era5_land_{year}_{month:02d}.nc"
    target_path = OUTPUT_DIR / output_filename
    temp_path = OUTPUT_DIR / f"temp_{output_filename}"

    # Determine days in the month
    _, num_days = calendar.monthrange(year, month)
    days_list = [f"{d:02d}" for d in range(1, num_days + 1)]
    times_list = [f"{h:02d}:00" for h in range(24)]

    request_params = {
        "variable": VARIABLE_NAME,
        "year": str(year),
        "month": f"{month:02d}",
        "day": days_list,
        "time": times_list,
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": [NORTH, WEST, SOUTH, EAST],
    }

    for attempt in range(1, max_retries + 1):
        print(f"\n--> Requesting {year}-{month:02d} ({MONTH_NAMES[month]} {year}) [Attempt {attempt}/{max_retries}]...")
        try:
            if temp_path.exists():
                temp_path.unlink()

            client.retrieve(DATASET_NAME, request_params, str(temp_path))

            # Validate downloaded file
            if validate_netcdf_file(temp_path, year, month):
                temp_path.rename(target_path)
                print(f"    SUCCESS: Saved and validated {output_filename} ({target_path.stat().st_size / (1024*1024):.2f} MB)")
                return True
            else:
                print(f"    FAILED validation for {output_filename}")
                if temp_path.exists():
                    temp_path.unlink()
        except Exception as e:
            print(f"    Download error on attempt {attempt}: {e}")
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            if attempt < max_retries:
                time.sleep(5 * attempt)

    return False


def main():
    print("=" * 60)
    print("ERA5-LAND AUTOMATED DOWNLOADER — SIH26001")
    print(f"Spatial Extent: North={NORTH}, South={SOUTH}, West={WEST}, East={EAST}")
    print(f"Target Directory: {OUTPUT_DIR}")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    url, key = load_credentials()
    # Initialize CDS API client quietly to prevent any key leaking
    client = cdsapi.Client(url=url, key=key, quiet=False)

    successful = []
    skipped = []
    failed = []

    # Flatten task list
    total_months = sum(len(months) for _, months in REQUIRED_YEAR_MONTHS)
    print(f"Total months to process: {total_months}\n")

    current_idx = 0
    for year, months in REQUIRED_YEAR_MONTHS:
        for month in months:
            current_idx += 1
            filename = f"era5_land_{year}_{month:02d}.nc"
            target_path = OUTPUT_DIR / filename
            month_label = f"{year}-{month:02d} ({MONTH_NAMES[month]})"

            print(f"[{current_idx}/{total_months}] Checking {month_label}...")

            # Check if file already exists and is valid
            if target_path.exists() and validate_netcdf_file(target_path, year, month):
                print(f"    SKIPPED: {filename} already exists and is valid.")
                skipped.append(month_label)
                continue

            # Download
            ok = download_era5_month(client, year, month)
            if ok:
                successful.append(month_label)
            else:
                failed.append(month_label)

    print("\n" + "=" * 60)
    print("ERA5-LAND DOWNLOAD STATUS")
    print("=" * 60)
    print("\nSuccessful:")
    if successful:
        for item in successful:
            print(f"  - {item}")
    else:
        print("  None")

    print("\nSkipped because already present:")
    if skipped:
        for item in skipped:
            print(f"  - {item}")
    else:
        print("  None")

    print("\nFailed:")
    if failed:
        for item in failed:
            print(f"  - {item}")
    else:
        print("  None")

    print(f"\nTotal successful: {len(successful)}")
    print(f"Total skipped: {len(skipped)}")
    print(f"Total failed: {len(failed)}")
    print("=" * 60)


if __name__ == "__main__":
    main()

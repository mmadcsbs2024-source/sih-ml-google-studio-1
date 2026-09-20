#!/usr/bin/env python3
"""
download_copernicus_dem.py
==========================
Downloads and validates the official Copernicus DEM GLO-30 dataset
for the Northeast India study region:
  North: 29.5°N
  South: 21.8°N
  West:  88.0°E
  East:  97.5°E

Coverage required:
  Latitudes:  21°N to 29°N (9 integer 1° bands, covering 21.0°N - 30.0°N)
  Longitudes: 88°E to 97°E (10 integer 1° bands, covering 88.0°E - 98.0°E)
  Total tiles: 90 tiles (1° x 1° each at 30m / 1 arc-second resolution)

Target Directory:
  data/external/copernicus_dem/
"""

import os
import sys
import time
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import rasterio
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("download_dem.log", mode="a"),
    ],
)
logger = logging.getLogger("copernicus_dem")

OUTPUT_DIR = Path("data/external/copernicus_dem")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Bounding box constraints
BOUNDS_NORTH = 29.5
BOUNDS_SOUTH = 21.8
BOUNDS_WEST = 88.0
BOUNDS_EAST = 97.5

# Integer tile grid coordinates
LATS = range(21, 30)  # 21 to 29 inclusive (covers 21.0 to 30.0 N)
LONS = range(88, 98)  # 88 to 97 inclusive (covers 88.0 to 98.0 E)

BASE_URL = "https://copernicus-dem-30m.s3.amazonaws.com"


def get_tile_info(lat: int, lon: int):
    tile_id = f"Copernicus_DSM_COG_10_N{lat:02d}_00_E{lon:03d}_00_DEM"
    tif_name = f"{tile_id}.tif"
    url = f"{BASE_URL}/{tile_id}/{tif_name}"
    target_path = OUTPUT_DIR / tif_name
    return lat, lon, tile_id, tif_name, url, target_path


def validate_tile(file_path: Path):
    """
    Validates a GeoTIFF tile using rasterio.
    Returns (is_valid, metadata_dict, error_msg).
    """
    if not file_path.exists() or file_path.stat().st_size == 0:
        return False, {}, "File does not exist or has 0 bytes"

    try:
        with rasterio.open(file_path) as ds:
            crs = str(ds.crs)
            bounds = ds.bounds
            width, height = ds.width, ds.height
            res = ds.res
            nodata = ds.nodata

            # Read a downsampled overview or check full array if needed
            # Since COG has overviews, reading band 1 is fast
            arr = ds.read(1)
            if nodata is not None:
                valid_mask = arr != nodata
            else:
                valid_mask = ~np.isnan(arr)

            valid_pixels = int(np.count_nonzero(valid_mask))
            if valid_pixels == 0:
                return False, {}, "No valid elevation pixels found"

            valid_vals = arr[valid_mask]
            min_elev = float(valid_vals.min())
            max_elev = float(valid_vals.max())

            meta = {
                "crs": crs,
                "bounds": (bounds.left, bounds.bottom, bounds.right, bounds.top),
                "width": width,
                "height": height,
                "resolution": res,
                "nodata": nodata,
                "valid_pixels": valid_pixels,
                "total_pixels": arr.size,
                "min_elev": min_elev,
                "max_elev": max_elev,
                "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
            }

            # Check essential geospatial parameters
            if "4326" not in crs and "WGS 84" not in crs:
                return False, meta, f"Unexpected CRS: {crs}"
            if width < 1000 or height < 1000:
                return False, meta, f"Unexpected dimensions: {width}x{height}"

            return True, meta, ""
    except Exception as e:
        return False, {}, str(e)


def download_single_tile(item):
    lat, lon, tile_id, tif_name, url, target_path = item

    # Check if existing file is already valid
    if target_path.exists():
        is_valid, meta, err = validate_tile(target_path)
        if is_valid:
            logger.info(f"[EXISTS & VALID] {tif_name} ({meta['size_mb']} MB, elev {meta['min_elev']:.1f}m - {meta['max_elev']:.1f}m)")
            return True, tile_id, meta, "Already downloaded and valid"

    tmp_path = target_path.with_suffix(".tmp")
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[DOWNLOADING] {tile_id} (Attempt {attempt}/{max_retries})...")
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(tmp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)

            # Validate before moving into place
            is_valid, meta, err = validate_tile(tmp_path)
            if is_valid:
                tmp_path.replace(target_path)
                logger.info(f"[SUCCESS] {tif_name} ({meta['size_mb']} MB, elev {meta['min_elev']:.1f}m - {meta['max_elev']:.1f}m)")
                return True, tile_id, meta, ""
            else:
                logger.warning(f"[CORRUPT] {tif_name} validation failed: {err}")
                if tmp_path.exists():
                    tmp_path.unlink()
        except Exception as e:
            logger.warning(f"[RETRY {attempt}] Error downloading {tile_id}: {e}")
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
            time.sleep(2 * attempt)

    return False, tile_id, {}, f"Failed to download after {max_retries} attempts"


def run():
    logger.info("=" * 60)
    logger.info("COPERNICUS DEM GLO-30 DOWNLOADER & VALIDATOR")
    logger.info(f"Target Region: North={BOUNDS_NORTH}, South={BOUNDS_SOUTH}, West={BOUNDS_WEST}, East={BOUNDS_EAST}")
    logger.info(f"Target Directory: {OUTPUT_DIR.resolve()}")
    logger.info("=" * 60)

    tile_items = [get_tile_info(lat, lon) for lat in LATS for lon in LONS]
    total_tiles = len(tile_items)
    logger.info(f"Total required tiles: {total_tiles}")

    # Concurrently download with ThreadPoolExecutor
    workers = 12
    logger.info(f"Starting downloads with {workers} parallel workers...")
    start_time = time.time()

    successful = 0
    failed = 0
    failed_items = []
    tile_metadata = {}

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(download_single_tile, item): item for item in tile_items}
        for future in as_completed(futures):
            ok, tile_id, meta, msg = future.result()
            if ok:
                successful += 1
                tile_metadata[tile_id] = meta
            else:
                failed += 1
                failed_items.append((tile_id, msg))

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"DOWNLOAD SUMMARY: {successful}/{total_tiles} succeeded in {elapsed:.1f}s, {failed} failed")

    # Global Validation & Coverage Check
    logger.info("=" * 60)
    logger.info("VERIFYING COMPLETE COVERAGE...")

    min_west = 180.0
    max_east = -180.0
    min_south = 90.0
    max_north = -90.0
    all_valid = True
    invalid_tiles = []

    for item in tile_items:
        _, _, tile_id, tif_name, _, target_path = item
        ok, meta, err = validate_tile(target_path)
        if not ok:
            all_valid = False
            invalid_tiles.append((tile_id, err))
            logger.error(f"[INVALID/MISSING] {tile_id}: {err}")
        else:
            left, bottom, right, top = meta["bounds"]
            min_west = min(min_west, left)
            max_east = max(max_east, right)
            min_south = min(min_south, bottom)
            max_north = max(max_north, top)

    logger.info(f"Collective Bounds: South={min_south:.2f}, North={max_north:.2f}, West={min_west:.2f}, East={max_east:.2f}")
    
    # Verify required coverage
    coverage_ok = (
        min_south <= BOUNDS_SOUTH and
        max_north >= BOUNDS_NORTH and
        min_west <= BOUNDS_WEST and
        max_east >= BOUNDS_EAST
    )

    logger.info("=" * 60)
    logger.info("COPERNICUS DEM STATUS")
    logger.info("Source: Copernicus DEM GLO-30")
    logger.info("Dataset: COP-DEM_GLO-30-DGED (Cloud Optimized GeoTIFF)")
    logger.info(f"Tiles found: {total_tiles}")
    logger.info(f"Tiles downloaded: {successful}")
    logger.info(f"Tiles valid: {total_tiles - len(invalid_tiles)}")
    logger.info(f"Tiles invalid: {len(invalid_tiles)}")
    logger.info("CRS: EPSG:4326 (WGS 84)")
    logger.info("Resolution: 1 arc-second (~30 meters, 0.00027778 deg)")
    logger.info(f"Coverage: North {max_north:.2f} | South {min_south:.2f} | West {min_west:.2f} | East {max_east:.2f}")
    
    if coverage_ok and all_valid:
        logger.info("Missing coverage: None (100% complete)")
        logger.info("STATUS: READY FOR ELEVATION EXTRACTION")
    else:
        logger.error(f"Missing coverage: {len(invalid_tiles)} tiles missing or invalid")
        logger.error("STATUS: BLOCKED")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()

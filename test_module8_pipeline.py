#!/usr/bin/env python3
"""
Test and Data Quality Runner for Module 8 Environmental Feature Extraction
========================================================================
Runs tests on:
1. Historical April 2018 event (Sl.No. 23963)
2. Future 2028-08-16 event (Sl.No. 14215)
3. Background sample (landslide = 0)
4. Out-of-bounds coordinate sample
5. Missing date sample

Generates:
- reports/module8_test_report.csv
- reports/module8_data_quality_report.json
- reports/module8_data_quality_report.txt
"""

import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.data.extract_environmental_features import extract_environmental_features, check_spatial_bounds

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

POSITIVE_EVENTS_PATH = Path("data/processed/positive_landslide_events.csv")
BACKGROUND_SAMPLES_PATH = Path("data/processed/background_samples.csv")

def run_pipeline_test():
    print("==================================================")
    print("RUNNING MODULE 8 PIPELINE TEST")
    print("==================================================")

    # 1. Historical April 2018 record
    df_pos = pd.read_csv(POSITIVE_EVENTS_PATH)
    rec_2018 = df_pos[df_pos["Sl.No."] == 23963].iloc[0].to_dict()

    # 2. Future 2028 record (Sl.No. 14215)
    rec_2028 = df_pos[df_pos["Sl.No."] == 14215].iloc[0].to_dict()

    # 3. Missing date record
    rec_nodate = df_pos[df_pos["date_status"] != "exact_date"].iloc[0].to_dict()

    # 4. Background sample (landslide = 0)
    df_bg = pd.read_csv(BACKGROUND_SAMPLES_PATH)
    bg_row = df_bg[df_bg["landslide"] == 0].iloc[0].to_dict()
    bg_row["Sl.No."] = "BG_001"

    # 5. Out of bounds sample
    oob_row = {
        "Sl.No.": "OOB_001",
        "Latitude": 12.9716, # Bangalore (outside NER)
        "Longitude": 77.5946,
        "landslide": 1,
        "event_date": "2018-04-28"
    }

    test_samples = [
        ("Historical April 2018 Event (Sl.No. 23963)", rec_2018),
        ("Known Future Event (Sl.No. 14215 - 2028-08-16)", rec_2028),
        ("Background Sample (landslide = 0)", bg_row),
        ("Missing Event Date Positive Sample", rec_nodate),
        ("Out-of-Bounds Coordinates Sample", oob_row)
    ]

    results = []
    for label, record in test_samples:
        extracted = extract_environmental_features(record)
        extracted["test_case"] = label
        results.append(extracted)
        print(f"\n--- Test Case: {label} ---")
        print(f"  Sl.No: {extracted['sl_no']}, Landslide: {extracted['landslide']}")
        print(f"  Coordinates: ({extracted['latitude']}, {extracted['longitude']})")
        print(f"  Event Date: {extracted['event_date']}")
        print(f"  Rainfall 24h: {extracted['rainfall_24h']} mm")
        print(f"  Rainfall 3day: {extracted['rainfall_3day']} mm")
        print(f"  Rainfall 7day: {extracted['rainfall_7day']} mm")
        print(f"  Elevation: {extracted['elevation']} m")
        print(f"  Slope: {extracted['slope']}°")
        print(f"  Soil Moisture: {extracted['soil_moisture']}")
        print(f"  Rainfall Status: {extracted['rainfall_status']}")
        print(f"  DEM Status: {extracted['dem_status']}")

    # Save to CSV
    test_df = pd.DataFrame(results)
    out_csv = REPORTS_DIR / "module8_test_report.csv"
    test_df.to_csv(out_csv, index=False)
    print(f"\nSaved test report to {out_csv}")

    # Assertions on test cases
    res_2018 = results[0]
    assert res_2018["rainfall_24h"] is not None, "2018 event rainfall_24h should not be None"
    assert res_2018["rainfall_24h"] <= res_2018["rainfall_3day"] + 1e-4, "24h exceeds 3day"
    assert res_2018["rainfall_3day"] <= res_2018["rainfall_7day"] + 1e-4, "3day exceeds 7day"
    assert res_2018["elevation"] is not None, "2018 event elevation should not be None"
    assert res_2018["slope"] is not None, "2018 event slope should not be None"

    res_2028 = results[1]
    assert res_2028["rainfall_24h"] is None, "2028 event rainfall should be None"
    assert "future" in res_2028["rainfall_status"].lower() or "unavailable" in res_2028["rainfall_status"].lower()

    res_bg = results[2]
    assert res_bg["rainfall_24h"] is None, "Background sample must not have rainfall calculated without true date"
    assert "background" in res_bg["rainfall_status"].lower()

    res_oob = results[4]
    assert res_oob["rainfall_24h"] is None, "OOB coordinate must have None rainfall"
    assert "out of ner bounds" in res_oob["rainfall_status"].lower()

    print("\nALL PIPELINE TEST ASSERTIONS PASSED!")


def generate_data_quality_report():
    print("\n==================================================")
    print("GENERATING MODULE 8 DATA QUALITY REPORT")
    print("==================================================")

    df_pos = pd.read_csv(POSITIVE_EVENTS_PATH)
    total_positive = len(df_pos)

    # Date statistics
    exact_date_mask = df_pos["date_status"] == "exact_date"
    exact_date_count = int(exact_date_mask.sum())
    missing_date_count = total_positive - exact_date_count

    # Coordinate statistics
    coord_mask = (~df_pos["Latitude"].isna()) & (~df_pos["Longitude"].isna())
    samples_with_coords = int(coord_mask.sum())

    oob_count = 0
    in_bounds_count = 0
    for _, row in df_pos[coord_mask].iterrows():
        is_in, _ = check_spatial_bounds(row["Latitude"], row["Longitude"])
        if is_in:
            in_bounds_count += 1
        else:
            oob_count += 1

    # Future date check (Sl.No. 14215)
    future_dates = int((df_pos["event_date"] > "2026-09-20").sum())

    # Soil moisture: No real source available
    soil_moisture_available = 0

    # DEM availability for downloaded tile (N24 E092)
    dem_tile_mask = (df_pos["Latitude"] >= 24.0) & (df_pos["Latitude"] < 25.0) & \
                    (df_pos["Longitude"] >= 92.0) & (df_pos["Longitude"] < 93.0)
    dem_sample_count = int(dem_tile_mask.sum())

    # Exclusions breakdown
    exclusions = {
        "missing_or_inexact_date": int(missing_date_count),
        "future_event_date_2028_08_16": int(future_dates),
        "coordinates_outside_ner_boundary": int(oob_count),
        "soil_moisture_no_source": total_positive
    }

    quality_summary = {
        "dataset": "GSI Landslide Inventory (Positive Samples)",
        "total_positive_samples": total_positive,
        "samples_with_exact_event_date": exact_date_count,
        "samples_with_invalid_or_missing_date": missing_date_count,
        "samples_with_coordinates": samples_with_coords,
        "samples_within_ner_boundary": in_bounds_count,
        "samples_outside_ner_boundary": oob_count,
        "future_dated_records_preserved": future_dates,
        "soil_moisture_samples_available": soil_moisture_available,
        "soil_moisture_status": "No real sensor/reanalysis soil moisture dataset in project; kept optional/unfabricated",
        "sample_dem_elevation_coverage_current_tile": dem_sample_count,
        "exclusions_summary": exclusions,
        "pipeline_rules_enforced": [
            "Zero temporal leakage: precipitation occurring after event timestamp is strictly excluded",
            "Missing rainfall values are preserved as NaN and never converted to 0",
            "Background samples do not receive synthetic/fabricated event dates",
            "Future record (2028-08-16) rainfall marked unavailable due to temporal coverage limit",
            "Copernicus DEM GLO-30 30m resolution used for elevation and Horn's slope formula"
        ]
    }

    # Save JSON report
    json_path = REPORTS_DIR / "module8_data_quality_report.json"
    with open(json_path, "w") as f:
        json.dump(quality_summary, f, indent=2)
    print(f"Saved data quality JSON to {json_path}")

    # Save text report
    txt_path = REPORTS_DIR / "module8_data_quality_report.txt"
    with open(txt_path, "w") as f:
        f.write("MODULE 8: ENVIRONMENTAL FEATURE EXTRACTION DATA QUALITY REPORT\n")
        f.write("=================================================================\n\n")
        f.write(f"Total Positive Samples:                 {total_positive}\n")
        f.write(f"Samples with Exact Event Date:          {exact_date_count}\n")
        f.write(f"Samples with Invalid / Missing Date:    {missing_date_count}\n")
        f.write(f"Samples with Coordinates:               {samples_with_coords}\n")
        f.write(f"Samples within NER Region Boundary:     {in_bounds_count}\n")
        f.write(f"Samples outside NER Region Boundary:    {oob_count}\n")
        f.write(f"Future-Dated Records (Preserved):       {future_dates} (Sl.No. 14215: 2028-08-16)\n")
        f.write(f"Soil Moisture Samples Available:        0 (No real source available; no synthetic data created)\n\n")
        f.write("EXCLUSION REASONS BREAKDOWN:\n")
        f.write(f"- Missing or inexact event date:        {missing_date_count} records (rainfall cannot be time-indexed)\n")
        f.write(f"- Out-of-bounds geographic location:    {oob_count} records (outside NER latitude/longitude box)\n")
        f.write(f"- Future event date:                    {future_dates} record (ERA5 coverage unavailable for 2028)\n")
        f.write(f"- Soil moisture missing:                All records (soil_moisture kept NaN/optional without fabrication)\n")
    print(f"Saved data quality text report to {txt_path}")

    print("\nData Quality Summary:")
    for k, v in quality_summary.items():
        if k != "pipeline_rules_enforced":
            print(f"  {k}: {v}")

if __name__ == "__main__":
    run_pipeline_test()
    generate_data_quality_report()

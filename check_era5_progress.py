#!/usr/bin/env python3
"""
ERA5-Land Download Status & Progress Checker for SIH26001.
Safely inspects downloading progress without interrupting the background process.
"""

import os
import sys
import re
import shutil
import subprocess
from pathlib import Path

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

ERA5_DIR = Path("data/external/era5_land")
LOG_PATH = Path("logs/era5_download.log")

def get_downloader_process():
    try:
        res = subprocess.run(["pgrep", "-f", "python.*download_era5.py"], capture_output=True, text=True)
        pids = [int(p.strip()) for p in res.stdout.strip().split() if p.strip()]
        # Exclude self PID
        pids = [p for p in pids if p != os.getpid()]
        if pids:
            return pids[0]
    except Exception:
        pass
    return None

def main():
    total_required = sum(len(m) for _, m in REQUIRED_YEAR_MONTHS)
    valid_files = []
    missing_files = []

    for y, months in REQUIRED_YEAR_MONTHS:
        for m in months:
            fname = f"era5_land_{y}_{m:02d}.nc"
            fpath = ERA5_DIR / fname
            if fpath.exists() and fpath.stat().st_size > 100_000:
                valid_files.append((y, m, fname))
            else:
                missing_files.append((y, m, fname))

    pid = get_downloader_process()
    process_status = "RUNNING" if pid else "STOPPED"

    # Disk usage
    disk_stat = shutil.disk_usage("/")
    free_gb = disk_stat.free / (1024**3)

    # Inspect log for current activity and failure counts
    current_month = "None"
    failed_count = 0
    if LOG_PATH.exists():
        with open(LOG_PATH, "r", errors="ignore") as lf:
            lines = lf.readlines()
            for line in reversed(lines):
                m = re.search(r"Checking (\d{4}-\d{2})", line)
                if m and current_month == "None":
                    current_month = m.group(1)
                m2 = re.search(r"Requesting (\d{4}-\d{2})", line)
                if m2 and current_month == "None":
                    current_month = m2.group(1)
                if "FAILED validation" in line or "Download error" in line:
                    failed_count += 1

    # Check for active temp file
    temp_files = list(ERA5_DIR.glob("temp_era5_land_*.nc"))
    if temp_files and current_month == "None":
        m = re.search(r"temp_era5_land_(\d{4}_\d{2})", temp_files[0].name)
        if m:
            current_month = m.group(1).replace("_", "-")

    if current_month == "None" and missing_files:
        current_month = f"{missing_files[0][0]}-{missing_files[0][1]:02d}"

    print("ERA5 DOWNLOAD STATUS")
    print("--------------------")
    print(f"Required: {total_required}")
    print(f"Valid: {len(valid_files)}")
    print(f"Remaining: {len(missing_files)}")
    print(f"Failed: {failed_count}")
    print(f"Current: {current_month}")
    print(f"PID: {pid if pid else 'None'}")
    print(f"Disk free: {free_gb:.1f} GB")
    print(f"Log: {LOG_PATH}")
    print(f"Process: {process_status}")

if __name__ == "__main__":
    main()

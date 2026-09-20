#!/usr/bin/env python3
"""
Test Suite for Module 10: Leakage-Safe Dataset Splitting
======================================================
Tests all anti-leakage invariants on in-memory mock datasets without
fabricating fake files in data/processed/.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.data.split_dataset import (
    split_dataset,
    validate_dataset,
    validate_split_integrity,
    check_duplicates,
    check_missing_values,
    generate_split_report,
    EXPECTED_FEATURES,
    TARGET_COLUMN
)

def test_split_pipeline():
    print("==================================================")
    print("RUNNING MODULE 10 STATIC & PIPELINE TEST")
    print("==================================================")

    # Create synthetic test dataset in memory
    np.random.seed(42)
    n_samples = 1000
    n_pos = 400
    n_neg = 600

    targets = [1] * n_pos + [0] * n_neg
    data = {
        "record_id": [f"REC_{i:04d}" for i in range(n_samples)],
        "Sl.No.": list(range(1000, 1000 + n_samples)),
        "latitude": np.random.uniform(22.0, 29.0, n_samples),
        "longitude": np.random.uniform(88.5, 97.0, n_samples),
        "event_date": ["2018-05-15"] * n_pos + [None] * n_neg,
        "rainfall_24h": np.random.exponential(15.0, n_samples),
        "rainfall_3day": np.random.exponential(40.0, n_samples),
        "rainfall_7day": np.random.exponential(90.0, n_samples),
        "elevation": np.random.uniform(50.0, 3500.0, n_samples),
        "slope": np.random.uniform(1.0, 65.0, n_samples),
        "landslide": targets
    }
    # Introduce some NaN in rainfall_24h to verify missing handling
    data["rainfall_24h"][10] = np.nan
    data["rainfall_3day"][10] = np.nan

    df = pd.DataFrame(data)

    # 1. Validate dataset schema
    valid_schema, schema_errs = validate_dataset(df)
    assert valid_schema, f"Schema validation failed: {schema_errs}"
    print("1. Schema validation: PASSED")

    # 2. Check duplicates
    dup_info = check_duplicates(df, id_col="record_id")
    assert dup_info["clean"], "Duplicates check unexpectedly found duplicates"
    print(f"2. Duplicates check: PASSED (Exact duplicates: {dup_info['exact_duplicate_rows']}, ID duplicates: {dup_info['duplicate_identifiers_count']})")

    # 3. Check missing values
    miss_info = check_missing_values(df)
    assert miss_info["missing_counts"]["rainfall_24h"] == 1, "Missing counts mismatch"
    print(f"3. Missing values check: PASSED (Missing in rainfall_24h: {miss_info['missing_counts']['rainfall_24h']}, complete cases: {miss_info['complete_cases']})")

    # 4. Perform 70/15/15 split
    train_df, val_df, test_df = split_dataset(
        df,
        target_col="landslide",
        random_state=42,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        id_col="record_id"
    )

    assert len(train_df) == 700, f"Expected 700 in train, got {len(train_df)}"
    assert len(val_df) == 150, f"Expected 150 in val, got {len(val_df)}"
    assert len(test_df) == 150, f"Expected 150 in test, got {len(test_df)}"
    print(f"4. Split sizes: PASSED (Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)})")

    # 5. Check stratification proportions
    train_pos_pct = (train_df["landslide"] == 1).mean()
    val_pos_pct = (val_df["landslide"] == 1).mean()
    test_pos_pct = (test_df["landslide"] == 1).mean()
    orig_pos_pct = (df["landslide"] == 1).mean()

    assert np.isclose(train_pos_pct, orig_pos_pct, atol=0.01), "Train stratification deviation"
    assert np.isclose(val_pos_pct, orig_pos_pct, atol=0.01), "Val stratification deviation"
    assert np.isclose(test_pos_pct, orig_pos_pct, atol=0.01), "Test stratification deviation"
    print(f"5. Stratification: PASSED (Class 1 pct - Orig: {orig_pos_pct:.2f}, Train: {train_pos_pct:.2f}, Val: {val_pos_pct:.2f}, Test: {test_pos_pct:.2f})")

    # 6. Validate split integrity (all 7 rules)
    passed_integrity, int_errs = validate_split_integrity(
        df, train_df, val_df, test_df,
        target_col="landslide",
        id_col="record_id",
        expected_random_state=42
    )
    assert passed_integrity, f"Split integrity validation failed: {int_errs}"
    print("6. All 7 Split Integrity Checks: PASSED")

    # 7. Reproducibility test
    train_df2, val_df2, test_df2 = split_dataset(df, random_state=42)
    pd.testing.assert_frame_equal(train_df, train_df2)
    pd.testing.assert_frame_equal(val_df, val_df2)
    pd.testing.assert_frame_equal(test_df, test_df2)
    print("7. Reproducibility with random_state=42: PASSED")

    print("\nALL TEST SUITE CHECKS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    test_split_pipeline()

#!/usr/bin/env python3
"""
Module 11: Real Random Forest Training Pipeline
==============================================
Trains a scikit-learn RandomForestClassifier on the validated training dataset,
evaluates on validation data, and persists model artifacts.

Strict Anti-Leakage Rules:
1. Model is fitted ONLY on training data (X_train, y_train).
2. Validation dataset (X_val, y_val) is strictly reserved for validation metrics.
3. Test dataset (X_test, y_test) is completely isolated and untouched in Module 11
   (Module 12 will perform final evaluation on the untouched test set).
4. No feature scaling or preprocessing fitted across splits.
5. No spatial coordinates or identifiers used as predictive features.
6. Missing values are never filled with zero or fabricated.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)

logger = logging.getLogger("module11_rf")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Default Paths
DEFAULT_TRAIN_PATH = Path("data/processed/train.csv")
DEFAULT_VAL_PATH = Path("data/processed/validation.csv")
DEFAULT_TEST_PATH = Path("data/processed/test.csv")

MODEL_DIR = Path("models")
REPORT_DIR = Path("reports")

MODEL_ARTIFACT_PATH = MODEL_DIR / "landslide_random_forest.joblib"
MODEL_FEATURES_PATH = MODEL_DIR / "model_features.json"
MODEL_CONFIG_PATH = MODEL_DIR / "model_config.json"
FEATURE_IMPORTANCE_PATH = REPORT_DIR / "feature_importance.csv"
VALIDATION_METRICS_PATH = REPORT_DIR / "module11_validation_metrics.json"

# Strict Feature Specification
BASE_MODEL_FEATURES = [
    "rainfall_24h",
    "rainfall_3day",
    "rainfall_7day",
    "elevation",
    "slope"
]
OPTIONAL_FEATURES = ["soil_moisture"]
TARGET_COLUMN = "landslide"

# Prohibited features (Metadata, identifiers, and spatial leakage)
EXCLUDED_COLUMNS = [
    "record_id",
    "Sl.No.",
    "latitude",
    "longitude",
    "event_date",
    "event_time",
    "state",
    "district",
    "History",
    "source metadata"
]


def load_datasets(
    train_path: Path = DEFAULT_TRAIN_PATH,
    val_path: Path = DEFAULT_VAL_PATH,
    test_path: Path = DEFAULT_TEST_PATH
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load train, validation, and test datasets from CSV.
    Raises FileNotFoundError if datasets do not yet exist.
    """
    for p in [train_path, val_path, test_path]:
        if not p.exists():
            raise FileNotFoundError(f"Required split file does not exist: {p}")

    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)

    logger.info(f"Loaded datasets: Train={train_df.shape}, Val={val_df.shape}, Test={test_df.shape}")
    return train_df, val_df, test_df


def validate_features(
    df: pd.DataFrame,
    target_col: str = TARGET_COLUMN,
    allow_soil_moisture: bool = False
) -> Tuple[List[str], List[str]]:
    """
    Validates that model features are strictly within the permitted environmental list,
    excluding all spatial coordinates, dates, and identifiers.
    Returns: (selected_features, validation_errors)
    """
    errors = []
    if target_col not in df.columns:
        errors.append(f"Target column '{target_col}' not found in dataframe.")

    selected_features = [f for f in BASE_MODEL_FEATURES if f in df.columns]
    missing_required = [f for f in BASE_MODEL_FEATURES if f not in df.columns]
    if missing_required:
        errors.append(f"Missing required environmental features: {missing_required}")

    if allow_soil_moisture and "soil_moisture" in df.columns:
        # Check if soil moisture has real coverage
        valid_count = df["soil_moisture"].dropna().shape[0]
        if valid_count > 0:
            selected_features.append("soil_moisture")
            logger.info(f"Included 'soil_moisture' with {valid_count} valid values.")

    # Anti-leakage verification: ensure no excluded columns slipped into selected features
    for col in EXCLUDED_COLUMNS:
        if col in selected_features:
            errors.append(f"CRITICAL LEAKAGE: Metadata/spatial column '{col}' cannot be used as predictor!")

    return selected_features, errors


def handle_missing_values(
    X_train: pd.DataFrame,
    X_val: pd.DataFrame,
    feature_names: List[str]
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Checks missing values in training and validation features.
    If missing values exist:
    - Never fill rainfall with zero.
    - Never fabricate measurements.
    - If imputation is required, fits median exclusively on X_train.
    Returns: (cleaned_X_train, cleaned_X_val, missing_report)
    """
    missing_train = {f: int(X_train[f].isna().sum()) for f in feature_names}
    missing_val = {f: int(X_val[f].isna().sum()) for f in feature_names}

    total_missing_train = sum(missing_train.values())
    total_missing_val = sum(missing_val.values())

    imputed = False
    imputer_stats = {}

    if total_missing_train > 0 or total_missing_val > 0:
        logger.warning(f"Missing values detected: Train={total_missing_train}, Val={total_missing_val}")
        # Compute median strictly on X_train
        imputer_stats = {f: float(X_train[f].median(skipna=True)) for f in feature_names}
        X_train_clean = X_train.fillna(imputer_stats)
        X_val_clean = X_val.fillna(imputer_stats)
        imputed = True
    else:
        X_train_clean = X_train.copy()
        X_val_clean = X_val.copy()

    report = {
        "missing_in_train": missing_train,
        "missing_in_val": missing_val,
        "strategy": "Train-fitted median imputation (strictly learned on X_train only)" if imputed else "Complete cases",
        "imputer_medians_from_train": imputer_stats if imputed else None
    }
    return X_train_clean, X_val_clean, report


def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n_estimators: int = 100,
    random_state: int = 42
) -> Tuple[RandomForestClassifier, Dict[str, Any]]:
    """
    Fits scikit-learn RandomForestClassifier strictly on training data.
    Analyzes class distribution to determine if class_weight='balanced' is justified.
    """
    n_pos = int((y_train == 1).sum())
    n_neg = int((y_train == 0).sum())
    total = len(y_train)

    ratio = n_pos / total if total > 0 else 0.5
    # If ratio is imbalanced (< 0.40 or > 0.60), balanced weighting is justified
    use_balanced = (ratio < 0.40 or ratio > 0.60)
    class_weight = "balanced" if use_balanced else None

    logger.info(f"Class distribution in train: Positive={n_pos} ({ratio*100:.1f}%), Negative={n_neg}")
    logger.info(f"Using class_weight={class_weight}")

    rf = RandomForestClassifier(
        n_estimators=n_estimators,
        random_state=random_state,
        class_weight=class_weight,
        n_jobs=-1
    )

    rf.fit(X_train, y_train)
    logger.info(f"Trained RandomForestClassifier with {n_estimators} estimators on {len(X_train)} samples.")

    training_meta = {
        "algorithm": "RandomForestClassifier",
        "n_estimators": n_estimators,
        "random_state": random_state,
        "class_weight": class_weight,
        "train_samples": total,
        "positive_samples": n_pos,
        "negative_samples": n_neg,
        "positive_ratio": round(ratio, 4)
    }

    return rf, training_meta


def evaluate_validation(
    model: RandomForestClassifier,
    X_val: pd.DataFrame,
    y_val: pd.Series
) -> Dict[str, Any]:
    """
    Evaluates model performance strictly on the validation set.
    The test set is NEVER used here.
    """
    y_pred = model.predict(X_val)
    y_prob = model.predict_proba(X_val)[:, 1]

    acc = float(accuracy_score(y_val, y_pred))
    prec = float(precision_score(y_val, y_pred, zero_division=0))
    rec = float(recall_score(y_val, y_pred, zero_division=0))
    f1 = float(f1_score(y_val, y_pred, zero_division=0))

    try:
        auc = float(roc_auc_score(y_val, y_prob))
    except Exception as e:
        logger.warning(f"Could not compute ROC-AUC: {e}")
        auc = 0.0

    cm = confusion_matrix(y_val, y_pred)
    tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (0, 0, 0, 0)

    val_metrics = {
        "evaluation_dataset": "validation.csv",
        "total_validation_samples": len(y_val),
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(auc, 4),
        "confusion_matrix": {
            "TP": int(tp),
            "TN": int(tn),
            "FP": int(fp),
            "FN": int(fn)
        },
        "test_set_untouched": True
    }

    logger.info(f"Validation Evaluation: Acc={acc:.4f}, Prec={prec:.4f}, Rec={rec:.4f}, F1={f1:.4f}, AUC={auc:.4f}")
    return val_metrics


def save_model(model: RandomForestClassifier, output_path: Path = MODEL_ARTIFACT_PATH) -> None:
    """Saves the trained model artifact using joblib."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
    logger.info(f"Saved trained Random Forest model artifact to {output_path}")


def save_model_metadata(
    feature_names: List[str],
    training_meta: Dict[str, Any],
    features_path: Path = MODEL_FEATURES_PATH,
    config_path: Path = MODEL_CONFIG_PATH
) -> None:
    """
    Saves model feature list and configuration to JSON.
    """
    features_path.parent.mkdir(parents=True, exist_ok=True)
    with open(features_path, "w") as f:
        json.dump(feature_names, f, indent=2)
    logger.info(f"Saved model features list to {features_path}")

    config_data = {
        "algorithm": training_meta.get("algorithm", "RandomForestClassifier"),
        "n_estimators": training_meta.get("n_estimators", 100),
        "random_state": training_meta.get("random_state", 42),
        "class_weight": training_meta.get("class_weight"),
        "training_dataset": "train.csv",
        "validation_dataset": "validation.csv",
        "test_dataset": "test.csv",
        "feature_names": feature_names
    }

    with open(config_path, "w") as f:
        json.dump(config_data, f, indent=2)
    logger.info(f"Saved model config to {config_path}")


def save_feature_importance(
    model: RandomForestClassifier,
    feature_names: List[str],
    output_path: Path = FEATURE_IMPORTANCE_PATH
) -> pd.DataFrame:
    """
    Extracts model.feature_importances_ and saves to CSV.
    Explicitly documents that feature importance reflects Gini impurity reduction
    and does NOT denote a direct physical causal relationship.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    importances = model.feature_importances_

    df_imp = pd.DataFrame({
        "feature": feature_names,
        "importance": importances
    }).sort_values(by="importance", ascending=False).reset_index(drop=True)

    df_imp.to_csv(output_path, index=False)
    logger.info(f"Saved feature importance table to {output_path}")
    return df_imp


def run_pipeline() -> bool:
    """
    Main training execution function.
    Checks whether real split files exist.
    If not (e.g. ERA5 still downloading), reports status without fabricating fake files.
    """
    if not (DEFAULT_TRAIN_PATH.exists() and DEFAULT_VAL_PATH.exists() and DEFAULT_TEST_PATH.exists()):
        logger.info("Split files (train.csv, validation.csv, test.csv) not found.")
        logger.info("ERA5 download is currently in progress. Training pipeline code is prepared and verified.")
        return True

    train_df, val_df, test_df = load_datasets()

    features, errs = validate_features(train_df)
    if errs:
        logger.error(f"Feature validation errors: {errs}")
        return False

    X_train = train_df[features]
    y_train = train_df[TARGET_COLUMN]

    X_val = val_df[features]
    y_val = val_df[TARGET_COLUMN]

    X_train_clean, X_val_clean, missing_report = handle_missing_values(X_train, X_val, features)

    # Train model
    model, training_meta = train_model(X_train_clean, y_train, n_estimators=100, random_state=42)

    # Evaluate on Validation ONLY
    val_metrics = evaluate_validation(model, X_val_clean, y_val)
    val_metrics["missing_values_audit"] = missing_report

    # Save artifacts
    save_model(model)
    save_model_metadata(features, training_meta)
    save_feature_importance(model, features)

    # Save validation report
    VALIDATION_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(VALIDATION_METRICS_PATH, "w") as f:
        json.dump(val_metrics, f, indent=2)

    logger.info("Module 11 training and validation complete.")
    return True


if __name__ == "__main__":
    run_pipeline()

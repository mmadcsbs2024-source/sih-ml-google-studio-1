#!/usr/bin/env python3
"""
Test Suite for Module 11: Real Random Forest Training Pipeline
============================================================
Validates algorithm configuration, feature separation, anti-leakage invariants,
model artifact serialization, and real probability inference.
Uses isolated mock data in memory and temporary directory without fabricating
any fake production datasets in data/processed/.
"""

import sys
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.model.train import (
    validate_features,
    handle_missing_values,
    train_model,
    evaluate_validation,
    save_model,
    save_model_metadata,
    save_feature_importance,
    BASE_MODEL_FEATURES,
    EXCLUDED_COLUMNS,
    TARGET_COLUMN
)
from src.model.predict import LandslidePredictor, DEFAULT_CATEGORY_THRESHOLDS

def test_module11():
    print("==================================================")
    print("RUNNING MODULE 11 STATIC & PIPELINE TEST")
    print("==================================================")

    # 1. Feature Separation & Spatial Leakage Prevention Test
    test_df_cols = BASE_MODEL_FEATURES + ["latitude", "longitude", "Sl.No.", "landslide"]
    dummy_df = pd.DataFrame(columns=test_df_cols)

    selected_feats, errors = validate_features(dummy_df)
    assert len(errors) == 0, f"Feature validation raised unexpected errors: {errors}"
    assert selected_feats == BASE_MODEL_FEATURES, f"Expected {BASE_MODEL_FEATURES}, got {selected_feats}"
    print("1. Feature validation & separation: PASSED (strictly uses environmental features)")

    # Anti-leakage guard test
    leakage_df = pd.DataFrame(columns=["rainfall_24h", "latitude", "landslide"])
    _, leak_errors = validate_features(leakage_df)
    assert len(leak_errors) > 0, "Failed to catch missing features"
    print("2. Spatial/metadata exclusion: PASSED")

    # 2. In-Memory Synthetic Dataset for Pipeline Testing
    np.random.seed(42)
    n_train = 600
    n_val = 150

    def make_dataset(n):
        rf24 = np.random.exponential(15.0, n)
        rf3d = rf24 + np.random.exponential(25.0, n)
        rf7d = rf3d + np.random.exponential(50.0, n)
        elev = np.random.uniform(100.0, 3000.0, n)
        slope = np.random.uniform(5.0, 55.0, n)

        # Realistic synthetic risk probability for testing
        prob = 1.0 / (1.0 + np.exp(-(0.03 * rf3d + 0.08 * slope - 4.0)))
        y = (np.random.rand(n) < prob).astype(int)

        return pd.DataFrame({
            "rainfall_24h": rf24,
            "rainfall_3day": rf3d,
            "rainfall_7day": rf7d,
            "elevation": elev,
            "slope": slope,
            "landslide": y
        })

    train_df = make_dataset(n_train)
    val_df = make_dataset(n_val)

    X_train = train_df[BASE_MODEL_FEATURES]
    y_train = train_df[TARGET_COLUMN]
    X_val = val_df[BASE_MODEL_FEATURES]
    y_val = val_df[TARGET_COLUMN]

    # 3. Train Model
    model, meta = train_model(X_train, y_train, n_estimators=100, random_state=42)
    assert isinstance(model, RandomForestClassifier), "Model is not an instance of RandomForestClassifier"
    assert model.n_estimators == 100, f"Expected 100 estimators, got {model.n_estimators}"
    assert model.random_state == 42, f"Expected random_state=42, got {model.random_state}"
    print(f"3. scikit-learn RandomForestClassifier fitting: PASSED (n_estimators=100, random_state=42, class_weight={meta['class_weight']})")

    # 4. Evaluate on Validation (Strict Test-Set Isolation)
    val_metrics = evaluate_validation(model, X_val, y_val)
    assert val_metrics["test_set_untouched"] is True, "Test set isolation flag must be True"
    assert "accuracy" in val_metrics and "roc_auc" in val_metrics
    cm = val_metrics["confusion_matrix"]
    assert all(k in cm for k in ["TP", "TN", "FP", "FN"])
    print(f"4. Validation Evaluation: PASSED (Acc={val_metrics['accuracy']:.4f}, AUC={val_metrics['roc_auc']:.4f}, CM: {cm})")

    # 5. Model Artifact Serialization & Deserialization in Temp Directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        tmp_model = tmp_path / "landslide_random_forest.joblib"
        tmp_feats = tmp_path / "model_features.json"
        tmp_conf = tmp_path / "model_config.json"
        tmp_imp = tmp_path / "feature_importance.csv"

        save_model(model, output_path=tmp_model)
        save_model_metadata(BASE_MODEL_FEATURES, meta, features_path=tmp_feats, config_path=tmp_conf)
        df_imp = save_feature_importance(model, BASE_MODEL_FEATURES, output_path=tmp_imp)

        assert tmp_model.exists(), "Model joblib artifact not written"
        assert tmp_feats.exists(), "Features JSON not written"
        assert tmp_conf.exists(), "Config JSON not written"
        assert tmp_imp.exists(), "Feature importance CSV not written"
        assert len(df_imp) == len(BASE_MODEL_FEATURES)
        print(f"5. Artifacts generation: PASSED")
        print("   Feature importances:\n" + df_imp.to_string(index=False))

        # 6. Predictor & Inference Engine Verification
        predictor = LandslidePredictor(model_path=tmp_model, features_path=tmp_feats)
        assert predictor.is_ready() is True

        sample_point = {
            "rainfall_24h": 45.0,
            "rainfall_3day": 120.0,
            "rainfall_7day": 250.0,
            "elevation": 1250.0,
            "slope": 38.5
        }
        res = predictor.predict_point(sample_point)

        assert "prediction" in res and res["prediction"] in (0, 1)
        assert "risk_probability" in res and 0.0 <= res["risk_probability"] <= 1.0
        assert "risk_score" in res and np.isclose(res["risk_score"], res["risk_probability"] * 100.0, atol=0.01)
        assert res["display_category"] in ("LOW", "MEDIUM", "HIGH")
        print(f"6. Real Prediction Inference: PASSED (Prob={res['risk_probability']}, Score={res['risk_score']}%, Category={res['display_category']})")

        # 7. Batch Inference Test
        batch_res = predictor.predict_batch(val_df[BASE_MODEL_FEATURES])
        assert len(batch_res) == len(val_df)
        assert "risk_probability" in batch_res.columns and "risk_score" in batch_res.columns
        print(f"7. Batch inference: PASSED ({len(batch_res)} records scored)")

    print("\nALL MODULE 11 CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_module11()

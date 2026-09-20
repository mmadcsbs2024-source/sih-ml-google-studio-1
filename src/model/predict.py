#!/usr/bin/env python3
"""
Module 11: Real Random Forest Inference & Prediction Engine
==========================================================
Provides real scikit-learn model inference for landslide susceptibility and
risk scoring across the Northeast India region.

No manual formulas, mock predictions, or hard-coded scores:
- Purely evaluates the scikit-learn RandomForestClassifier.
- Returns class-1 probability as `risk_probability` (0.0 to 1.0).
- Scales probability directly to percentage: `risk_score = risk_probability * 100.0`.
- Optional display categories (LOW, MEDIUM, HIGH) with configurable thresholds,
  explicitly flagged as heuristic display aids, not validated hazard standards.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Union, Optional

import numpy as np
import pandas as pd
import joblib

logger = logging.getLogger("module11_predict")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DEFAULT_MODEL_PATH = Path("models/landslide_random_forest.joblib")
DEFAULT_FEATURES_PATH = Path("models/model_features.json")

# Default display category thresholds (configurable presentation aids)
DEFAULT_CATEGORY_THRESHOLDS = {
    "LOW": (0.0, 35.0),
    "MEDIUM": (35.0, 70.0),
    "HIGH": (70.0, 100.0)
}


class LandslidePredictor:
    """
    Production-ready predictor loading the trained RandomForestClassifier artifact.
    """

    def __init__(
        self,
        model_path: Path = DEFAULT_MODEL_PATH,
        features_path: Path = DEFAULT_FEATURES_PATH
    ):
        self.model_path = Path(model_path)
        self.features_path = Path(features_path)
        self.model = None
        self.feature_names = None

        if self.model_path.exists() and self.features_path.exists():
            self._load()

    def _load(self):
        """Loads model weights and required feature names."""
        self.model = joblib.load(self.model_path)
        with open(self.features_path, "r") as f:
            self.feature_names = json.load(f)
        logger.info(f"Loaded model from {self.model_path} with features: {self.feature_names}")

    def is_ready(self) -> bool:
        """Checks if model artifact is loaded and ready for inference."""
        return self.model is not None and self.feature_names is not None

    def predict_point(
        self,
        features: Dict[str, float],
        thresholds: Optional[Dict[str, tuple]] = None
    ) -> Dict[str, Any]:
        """
        Predict landslide risk for a single location/time instance.
        
        Parameters:
            features: Dictionary containing required environmental predictors:
                      - rainfall_24h (mm)
                      - rainfall_3day (mm)
                      - rainfall_7day (mm)
                      - elevation (meters)
                      - slope (degrees)
                      (and soil_moisture if part of model features)
            thresholds: Optional category bounds dict for display categorization.
            
        Returns:
            Dict containing:
                - prediction: binary int (0 or 1)
                - risk_probability: float (0.0 to 1.0)
                - risk_score: float (0.0 to 100.0)
                - display_category: str ("LOW", "MEDIUM", "HIGH")
                - features_used: list of feature names passed to model
        """
        if not self.is_ready():
            raise RuntimeError(
                f"Model artifact not loaded. Verify {self.model_path} and {self.features_path} exist."
            )

        # Format as single-row DataFrame with exact feature names
        X_df = pd.DataFrame([{feat: float(features[feat]) for feat in self.feature_names}])

        # Inference with scikit-learn model
        pred = int(self.model.predict(X_df)[0])
        prob = float(self.model.predict_proba(X_df)[0, 1])
        score = round(prob * 100.0, 2)

        # Determine display category
        cat = self.get_display_category(score, thresholds or DEFAULT_CATEGORY_THRESHOLDS)

        return {
            "prediction": pred,
            "risk_probability": round(prob, 4),
            "risk_score": score,
            "display_category": cat,
            "features_used": self.feature_names,
            "category_thresholds_note": (
                "Display category is a presentation threshold based on model probability, "
                "not an externally calibrated geotechnical engineering hazard standard."
            )
        }

    def predict_batch(
        self,
        df: pd.DataFrame,
        thresholds: Optional[Dict[str, tuple]] = None
    ) -> pd.DataFrame:
        """
        Vectorized batch inference on a DataFrame.
        """
        if not self.is_ready():
            raise RuntimeError("Model artifact not loaded.")

        missing_feats = [f for f in self.feature_names if f not in df.columns]
        if missing_feats:
            raise ValueError(f"Input dataframe missing required features: {missing_feats}")

        X = df[self.feature_names]
        preds = self.model.predict(X)
        probs = self.model.predict_proba(X)[:, 1]

        results = df.copy()
        results["prediction"] = preds
        results["risk_probability"] = np.round(probs, 4)
        results["risk_score"] = np.round(probs * 100.0, 2)
        results["display_category"] = [
            self.get_display_category(s, thresholds or DEFAULT_CATEGORY_THRESHOLDS)
            for s in results["risk_score"]
        ]
        return results

    @staticmethod
    def get_display_category(risk_score: float, thresholds: Dict[str, tuple]) -> str:
        """Assigns configurable display category based on risk score."""
        for cat_name, (low, high) in thresholds.items():
            if low <= risk_score <= high:
                return cat_name
        return "HIGH" if risk_score > 70.0 else "LOW"


# Convenience functional interface
_global_predictor: Optional[LandslidePredictor] = None

def predict_landslide_risk(
    features: Dict[str, float],
    model_path: Path = DEFAULT_MODEL_PATH,
    features_path: Path = DEFAULT_FEATURES_PATH
) -> Dict[str, Any]:
    """
    Standard top-level functional prediction API.
    """
    global _global_predictor
    if _global_predictor is None or _global_predictor.model_path != model_path:
        _global_predictor = LandslidePredictor(model_path, features_path)
    return _global_predictor.predict_point(features)

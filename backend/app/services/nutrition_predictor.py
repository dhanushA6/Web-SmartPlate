import os
import warnings
from typing import Dict, Any

import joblib
import numpy as np
import pandas as pd

from ..config import get_settings


settings = get_settings()

_model = None


TARGET_COLS = [
    "daily_calories_kcal",
    "daily_carbohydrates_g",
    "daily_protein_g",
    "daily_fat_g",
    "daily_fiber_g",
]


def _load_model():
    global _model
    if _model is None:
        model_path = settings.NUTRITION_MODEL_PATH
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"LightGBM pipeline not found at {model_path}")
        _model = joblib.load(model_path)
    return _model


def _predict_single(model, sample_dict: Dict[str, Any]) -> Dict[str, float]:
    sample_df = pd.DataFrame([sample_dict])

    expected_features = model.named_steps["prep"].feature_names_in_

    for col in expected_features:
        if col not in sample_df.columns:
            sample_df[col] = np.nan

    sample_df = sample_df[expected_features]

    # LightGBM can emit a known warning in some sklearn pipeline combinations
    # even when columns are aligned; silence only this specific noisy warning.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="X does not have valid feature names, but LGBMRegressor was fitted with feature names",
            category=UserWarning,
        )
        prediction = model.predict(sample_df)[0]

    return dict(zip(TARGET_COLS, prediction))


def predict_nutrition_from_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes a flat profile dict and returns:
    - daily macro targets
    - per-meal split according to fixed percentages
    """
    model = _load_model()

    # The model expects raw features as in the training notebook.
    sample_dict = dict(profile)

    preds = _predict_single(model, sample_dict)

    daily = {k: float(v) for k, v in preds.items()}

    distribution = {
        "breakfast": 0.25,
        "lunch": 0.35,
        "snacks": 0.15,
        "dinner": 0.25,
    }

    meal_splits: Dict[str, Dict[str, float]] = {}
    for meal, frac in distribution.items():
        meal_splits[meal] = {
            k: round(v * frac, 2) for k, v in daily.items()
        }

    return {
        "daily": daily,
        "distribution": distribution,
        "meal_splits": meal_splits,
    }


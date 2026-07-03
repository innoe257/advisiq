"""Loads the risk-prediction model and defines the feature contract it expects.

The model behind this loader is trained on purely synthetic data with a
synthetic, hand-defined risk label (see scripts/train_risk_model.py) — it
demonstrates the full prediction pipeline, not a validated real-world model.
"""

from functools import lru_cache

import xgboost as xgb

from app.config import get_settings

FEATURE_NAMES = ["gpa", "attendance_rate", "completion_ratio", "year_of_study", "age"]


def build_feature_vector(
    *,
    gpa: float,
    attendance_rate: float,
    year_of_study: int,
    age: int,
    credits_attempted: int,
    credits_completed: int,
) -> list[float]:
    completion_ratio = credits_completed / credits_attempted if credits_attempted else 0.0
    return [gpa, attendance_rate, completion_ratio, float(year_of_study), float(age)]


class RiskModel:
    """Thin wrapper so callers depend on a `predict_proba` interface rather
    than the xgboost API directly — the test suite substitutes a stub
    implementing the same interface instead of loading the real artifact."""

    def __init__(self, booster: xgb.Booster) -> None:
        self._booster = booster

    def predict_proba(self, feature_rows: list[list[float]]) -> list[float]:
        dmatrix = xgb.DMatrix(feature_rows, feature_names=FEATURE_NAMES)
        return [float(p) for p in self._booster.predict(dmatrix)]


@lru_cache
def load_model() -> RiskModel:
    settings = get_settings()
    booster = xgb.Booster()
    booster.load_model(str(settings.model_artifact_path))
    return RiskModel(booster)

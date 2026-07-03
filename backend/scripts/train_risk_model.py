"""Train the AdvisIQ risk model on synthetic data.

IMPORTANT: the project brief assumes an "existing validated XGBoost
prediction model." This repository has no real student outcomes to validate
against, so this script instead defines an explicit, documented synthetic
risk rule below and trains against that. This demonstrates the full
prediction pipeline (feature engineering -> training -> versioned artifact ->
serving) but the resulting model has no real-world predictive validity.

Usage (from backend/):
    uv run python scripts/train_risk_model.py
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import xgboost as xgb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.ml.model_loader import FEATURE_NAMES, build_feature_vector  # noqa: E402

TRAIN_SAMPLES = 5000
TEST_SAMPLES = 1000


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _synthetic_risk_probability(
    gpa: float, attendance_rate: float, completion_ratio: float
) -> float:
    """A hand-defined stand-in for a real outcome label (e.g. "did not
    progress to next year"). Weights are arbitrary, chosen only to make GPA,
    attendance, and credit completion each meaningfully move the risk score
    in the intuitive direction."""
    normalized_gpa = gpa / 4.0
    weighted_score = 0.40 * normalized_gpa + 0.35 * attendance_rate + 0.25 * completion_ratio
    steepness = 8.0
    midpoint = 0.55
    return _sigmoid(steepness * (midpoint - weighted_score))


def _generate_training_example(rng: random.Random) -> tuple[list[float], int]:
    year_of_study = rng.randint(1, 4)
    age = 17 + year_of_study + rng.randint(0, 3)
    engagement = rng.betavariate(2, 2)

    gpa = round(min(4.0, max(0.0, rng.gauss(1.5 + 2.5 * engagement, 0.4))), 2)
    attendance_rate = round(min(1.0, max(0.0, rng.gauss(0.5 + 0.45 * engagement, 0.12))), 2)

    credits_attempted = year_of_study * 30
    completion_ratio = min(1.0, max(0.0, rng.gauss(0.6 + 0.35 * engagement, 0.1)))
    credits_completed = round(credits_attempted * completion_ratio)

    risk_probability = _synthetic_risk_probability(gpa, attendance_rate, completion_ratio)
    label = 1 if rng.random() < risk_probability else 0

    features = build_feature_vector(
        gpa=gpa,
        attendance_rate=attendance_rate,
        year_of_study=year_of_study,
        age=age,
        credits_attempted=credits_attempted,
        credits_completed=credits_completed,
    )
    return features, label


def _build_dataset(count: int, rng: random.Random) -> tuple[list[list[float]], list[int]]:
    features: list[list[float]] = []
    labels: list[int] = []
    for _ in range(count):
        row, label = _generate_training_example(rng)
        features.append(row)
        labels.append(label)
    return features, labels


def main() -> None:
    rng = random.Random(7)

    train_features, train_labels = _build_dataset(TRAIN_SAMPLES, rng)
    test_features, test_labels = _build_dataset(TEST_SAMPLES, rng)

    dtrain = xgb.DMatrix(train_features, label=train_labels, feature_names=FEATURE_NAMES)
    dtest = xgb.DMatrix(test_features, label=test_labels, feature_names=FEATURE_NAMES)

    params = {
        "objective": "binary:logistic",
        "max_depth": 4,
        "eta": 0.1,
        "eval_metric": "logloss",
    }
    booster = xgb.train(
        params,
        dtrain,
        num_boost_round=50,
        evals=[(dtrain, "train"), (dtest, "test")],
        verbose_eval=False,
    )

    predictions = booster.predict(dtest)
    accuracy = sum(
        (1 if pred >= 0.5 else 0) == label
        for pred, label in zip(predictions, test_labels, strict=True)
    ) / len(test_labels)
    print(f"Holdout accuracy on {TEST_SAMPLES} synthetic examples: {accuracy:.3f}")

    settings = get_settings()
    settings.model_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(settings.model_artifact_path))
    print(f"Saved model ({settings.model_version}) to {settings.model_artifact_path}")


if __name__ == "__main__":
    main()

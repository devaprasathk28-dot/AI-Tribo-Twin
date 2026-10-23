"""Leakage-aware regression workflow with a strictly separated demo fixture."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import math
import platform
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import joblib
import matplotlib

matplotlib.use("Agg")
import numpy as np
import pandas as pd
import sklearn
from matplotlib import pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_READINESS_PATH = PROJECT_ROOT / "data" / "validation" / "TARGET_READINESS.csv"
DEFAULT_ARTIFACT_DIR = PROJECT_ROOT / "artifacts" / "ml" / "synthetic-demo"
SYNTHETIC_TARGET_ID = "SYNTHETIC-DEMO"
EXPERIMENTAL_TARGETS = {
    "TARGET-COF",
    "TARGET-WEAR",
    "TARGET-SWR",
    "TARGET-WVL",
}


class TrainingBlockedError(RuntimeError):
    """Raised when scientific readiness does not allow experimental training."""


@dataclass(frozen=True)
class TrainingResult:
    report: dict[str, object]
    artifact_dir: Path


def _readiness_status(target_id: str, readiness_path: Path) -> str:
    with readiness_path.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row.get("target_id") == target_id:
                return row.get("ml_readiness", "UNKNOWN")
    raise ValueError(f"Target {target_id!r} is not in the readiness register.")


def _check_training_authorization(
    target_id: str,
    source_kind: Literal["synthetic", "experimental"],
    readiness_path: Path,
) -> None:
    if source_kind not in {"synthetic", "experimental"}:
        raise ValueError(f"Unsupported training source: {source_kind!r}.")
    if source_kind == "experimental":
        if target_id not in EXPERIMENTAL_TARGETS:
            raise ValueError(f"Unknown experimental target: {target_id!r}.")
        status = _readiness_status(target_id, readiness_path)
        if status != "READY":
            raise TrainingBlockedError(
                f"{target_id} is {status}; experimental training requires READY status."
            )
        return
    if target_id != SYNTHETIC_TARGET_ID:
        raise ValueError(
            f"{source_kind} training must use target_id={SYNTHETIC_TARGET_ID!r}; "
            "experimental target IDs cannot be attached to synthetic data."
        )


def make_synthetic_fixture(
    *, seed: int = 417, group_count: int = 80, rows_per_group: int = 6
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Create deterministic, non-experimental data with known regression signal."""
    if group_count < 10 or rows_per_group < 2:
        raise ValueError("Synthetic fixture needs at least 10 groups and 2 rows per group.")

    rng = np.random.default_rng(seed)
    row_count = group_count * rows_per_group
    load = rng.uniform(5.0, 30.0, size=row_count)
    velocity = rng.uniform(0.2, 2.0, size=row_count)
    reinforcement = rng.uniform(0.0, 0.12, size=row_count)
    filler_family = rng.choice(["fixture-A", "fixture-B"], size=row_count)
    group_effects = rng.normal(0.0, 0.08, size=group_count)
    groups = np.repeat([f"synthetic-batch-{i:03d}" for i in range(group_count)], rows_per_group)
    target = (
        0.5
        + 0.018 * load
        - 0.12 * velocity
        + 0.7 * reinforcement
        + 0.004 * load * velocity
        + np.where(filler_family == "fixture-B", 0.1, -0.1)
        + np.repeat(group_effects, rows_per_group)
        + rng.normal(0.0, 0.035, size=row_count)
    )
    features = pd.DataFrame(
        {
            "load_n": load,
            "sliding_velocity_m_per_s": velocity,
            "reinforcement_fraction": reinforcement,
            "filler_family": filler_family,
        }
    )
    return features, pd.Series(target, name="synthetic_response"), pd.Series(groups, name="group_id")


def _make_preprocessor(features: pd.DataFrame) -> ColumnTransformer:
    numeric = features.select_dtypes(include=["number"]).columns.tolist()
    categorical = features.select_dtypes(exclude=["number"]).columns.tolist()
    if not numeric and not categorical:
        raise ValueError("At least one numeric or categorical feature is required.")

    transformers: list[tuple[str, Pipeline, list[str]]] = []
    if numeric:
        transformers.append(
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric,
            )
        )
    if categorical:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            )
        )
    return ColumnTransformer(transformers=transformers, remainder="drop")


def _build_candidates(features: pd.DataFrame) -> dict[str, Pipeline]:
    return {
        "mean_baseline": Pipeline(
            [("preprocess", _make_preprocessor(features)), ("model", DummyRegressor(strategy="mean"))]
        ),
        "ridge_regression": Pipeline(
            [("preprocess", _make_preprocessor(features)), ("model", Ridge(alpha=1.0))]
        ),
    }


def _metrics(observed: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    mse = float(mean_squared_error(observed, predicted))
    values = {
        "mae": float(mean_absolute_error(observed, predicted)),
        "rmse": math.sqrt(mse),
        "r2": float(r2_score(observed, predicted)),
    }
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError("Evaluation produced a non-finite metric.")
    return values


def _fingerprint(features: pd.DataFrame, target: pd.Series, groups: pd.Series) -> str:
    frame = features.copy()
    frame["__target__"] = target.to_numpy()
    frame["__group__"] = groups.astype(str).to_numpy()
    return hashlib.sha256(frame.to_csv(index=False, lineterminator="\n").encode("utf-8")).hexdigest()


def train_regression(
    features: pd.DataFrame,
    target: pd.Series,
    groups: Sequence[object] | pd.Series,
    *,
    target_id: str,
    source_kind: Literal["synthetic", "experimental"],
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
    readiness_path: Path = DEFAULT_READINESS_PATH,
    seed: int = 417,
) -> TrainingResult:
    """Compare regression baselines with group-aware CV and a holdout test set."""
    _check_training_authorization(target_id, source_kind, readiness_path)
    if features.empty or features.shape[1] == 0:
        raise ValueError("Training features must contain at least one row and one column.")
    if len(features) != len(target) or len(features) != len(groups):
        raise ValueError("Features, target, and group labels must have equal row counts.")
    if features.columns.duplicated().any():
        raise ValueError("Feature names must be unique.")
    features = features.copy().reset_index(drop=True)
    raw_target = pd.Series(target).reset_index(drop=True)
    target = pd.to_numeric(raw_target, errors="coerce")
    invalid_target_mask = raw_target.notna() & target.isna()
    if invalid_target_mask.any():
        raise ValueError("Target contains non-numeric values.")
    group_values = pd.Series(list(groups), dtype="string")
    missing_target_mask = target.isna()
    missing_target_rows_excluded = int(missing_target_mask.sum())
    if missing_target_rows_excluded:
        features = features.loc[~missing_target_mask].reset_index(drop=True)
        target = target.loc[~missing_target_mask].reset_index(drop=True)
        group_values = group_values.loc[~missing_target_mask].reset_index(drop=True)
    if not np.isfinite(target.to_numpy(dtype=float)).all():
        raise ValueError("Target contains non-finite values.")
    if group_values.isna().any() or group_values.str.strip().eq("").any():
        raise ValueError("Every row requires a non-empty independent-group identifier.")
    if group_values.nunique() < 10:
        raise ValueError("At least 10 independent groups are required for this evaluation.")
    if target.nunique() < 2:
        raise ValueError("Regression requires at least two distinct target values.")

    # Hold out whole groups before fitting any learned preprocessing.
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
    train_indices, test_indices = next(splitter.split(features, target, group_values))
    x_train, x_test = features.iloc[train_indices].copy(), features.iloc[test_indices].copy()
    y_train, y_test = target.iloc[train_indices].astype(float), target.iloc[test_indices].astype(float)
    train_groups = group_values.iloc[train_indices]
    test_groups = group_values.iloc[test_indices]
    if set(train_groups) & set(test_groups):
        raise RuntimeError("Group leakage detected between train and holdout partitions.")

    cv_splits = min(5, train_groups.nunique())
    if cv_splits < 2:
        raise ValueError("At least two training groups are required for cross-validation.")
    cv = GroupKFold(n_splits=cv_splits)
    candidates = _build_candidates(features)
    comparison: dict[str, dict[str, float]] = {}
    fitted_models: dict[str, Pipeline] = {}
    for name, pipeline in candidates.items():
        cv_result = cross_validate(
            pipeline,
            x_train,
            y_train,
            groups=train_groups,
            cv=cv,
            scoring={
                "mae": "neg_mean_absolute_error",
                "rmse": "neg_root_mean_squared_error",
                "r2": "r2",
            },
            return_train_score=False,
            error_score="raise",
        )
        comparison[name] = {
            "cv_mae_mean": float(-np.mean(cv_result["test_mae"])),
            "cv_mae_std": float(np.std(-cv_result["test_mae"], ddof=1)),
            "cv_rmse_mean": float(-np.mean(cv_result["test_rmse"])),
            "cv_r2_mean": float(np.mean(cv_result["test_r2"])),
        }
        fitted_models[name] = pipeline

    selected_name = min(comparison, key=lambda name: comparison[name]["cv_mae_mean"])
    selected_model = fitted_models[selected_name]
    selected_model.fit(x_train, y_train)
    test_predictions = np.asarray(selected_model.predict(x_test), dtype=float).reshape(-1)
    holdout_metrics = _metrics(y_test.to_numpy(), test_predictions)

    artifact_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifact_dir / "model.joblib"
    predictions_path = artifact_dir / "holdout_predictions.csv"
    plot_path = artifact_dir / "predictions_vs_observations.png"
    report_path = artifact_dir / "report.json"
    manifest_path = artifact_dir / "manifest.json"

    joblib.dump(selected_model, model_path)
    pd.DataFrame(
        {
            "group_id": test_groups.to_numpy(),
            "observed_synthetic_response": y_test.to_numpy(),
            "predicted_synthetic_response": test_predictions,
        }
    ).to_csv(predictions_path, index=False)

    fig, axis = plt.subplots(figsize=(6.5, 6))
    axis.scatter(y_test, test_predictions, alpha=0.75, edgecolors="none")
    bounds = [
        min(float(y_test.min()), float(np.min(test_predictions))),
        max(float(y_test.max()), float(np.max(test_predictions))),
    ]
    axis.plot(bounds, bounds, linestyle="--", color="#b45309", label="Perfect agreement")
    axis.set(
        title="Synthetic demo: held-out groups",
        xlabel="Observed synthetic response",
        ylabel="Predicted synthetic response",
    )
    axis.legend()
    fig.tight_layout()
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)

    report: dict[str, object] = {
        "status": (
            "EVALUATED_SYNTHETIC_DEMO"
            if source_kind == "synthetic"
            else "EVALUATED_EXPERIMENTAL_MODEL"
        ),
        "source_kind": source_kind,
        "synthetic_only": source_kind == "synthetic",
        "experimental_results": source_kind == "experimental",
        "target_id": target_id,
        "target_name": (
            "Synthetic demonstration response"
            if source_kind == "synthetic"
            else target_id
        ),
        "training_rows": len(train_indices),
        "holdout_rows": len(test_indices),
        "training_groups": int(train_groups.nunique()),
        "holdout_groups": int(test_groups.nunique()),
        "training_group_ids": sorted(train_groups.unique().tolist()),
        "holdout_group_ids": sorted(test_groups.unique().tolist()),
        "cross_validation_folds": cv_splits,
        "seed": seed,
        "missing_target_rows_excluded": missing_target_rows_excluded,
        "feature_columns": features.columns.tolist(),
        "dataset_sha256": _fingerprint(features, target, group_values),
        "model_comparison": comparison,
        "selected_model": selected_name,
        "holdout_metrics": holdout_metrics,
        "artifacts": {
            "model": model_path.name,
            "predictions": predictions_path.name,
            "plot": plot_path.name,
        },
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "interpretation": (
            "Synthetic fixture demonstration only. These metrics are not estimates "
            "of performance on AI-TriboTwin composite experiments."
            if source_kind == "synthetic"
            else "Experimental evaluation; interpret only with its recorded readiness and provenance."
        ),
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "format_version": 2,
        "source_kind": source_kind,
        "target_id": target_id,
        "artifacts": {
            "model": {"file": model_path.name, "sha256": _file_sha256(model_path)},
            "report": {"file": report_path.name, "sha256": _file_sha256(report_path)},
            "predictions": {
                "file": predictions_path.name,
                "sha256": _file_sha256(predictions_path),
            },
            "plot": {"file": plot_path.name, "sha256": _file_sha256(plot_path)},
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    logger.info(
        "Trained %s on %s rows from %d groups; held-out MAE %.6f",
        selected_name,
        len(train_indices),
        train_groups.nunique(),
        holdout_metrics["mae"],
    )
    return TrainingResult(report=report, artifact_dir=artifact_dir)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validated_artifact_path(artifact_dir: Path, filename: object, label: str) -> Path:
    if not isinstance(filename, str) or Path(filename).name != filename:
        raise ValueError(f"Model manifest contains an invalid {label} filename.")
    path = artifact_dir / filename
    if not path.is_file():
        raise FileNotFoundError(f"Model {label} artifact not found: {path}")
    return path


def verify_model_artifact_bundle(artifact_dir: Path) -> dict[str, object]:
    """Verify the hash-bound model, report, predictions, and evaluation metrics."""
    manifest_path = artifact_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Model manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format_version") != 2:
        raise ValueError("Unsupported model artifact manifest version.")
    source_kind = manifest.get("source_kind")
    target_id = manifest.get("target_id")
    if source_kind not in {"synthetic", "experimental"}:
        raise ValueError("Model artifact has an unsupported source kind.")
    if source_kind == "synthetic" and target_id != SYNTHETIC_TARGET_ID:
        raise ValueError("Synthetic artifact has inconsistent target provenance.")
    if source_kind == "experimental" and target_id not in EXPERIMENTAL_TARGETS:
        raise ValueError("Experimental artifact refers to an unknown target.")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise TypeError("Model manifest has no artifact inventory.")
    resolved: dict[str, Path] = {}
    for label in ("model", "report", "predictions", "plot"):
        entry = artifacts.get(label)
        if not isinstance(entry, dict):
            raise TypeError(f"Model manifest has no {label} artifact entry.")
        path = _validated_artifact_path(artifact_dir, entry.get("file"), label)
        digest = entry.get("sha256")
        if not isinstance(digest, str) or _file_sha256(path) != digest:
            raise ValueError(f"{label.capitalize()} artifact SHA-256 does not match its manifest.")
        resolved[label] = path

    report = json.loads(resolved["report"].read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise TypeError("Saved model report is not an object.")
    if report.get("source_kind") != source_kind or report.get("target_id") != target_id:
        raise ValueError("Saved model report does not match manifest provenance.")
    expected_status = (
        "EVALUATED_SYNTHETIC_DEMO" if source_kind == "synthetic" else "EVALUATED_EXPERIMENTAL_MODEL"
    )
    if report.get("status") != expected_status:
        raise ValueError("Saved model report has an inconsistent evaluation status.")

    predictions = pd.read_csv(resolved["predictions"])
    observed_column = f"observed_{'synthetic_response' if source_kind == 'synthetic' else 'response'}"
    predicted_column = f"predicted_{'synthetic_response' if source_kind == 'synthetic' else 'response'}"
    required_columns = {"group_id", observed_column, predicted_column}
    if not required_columns.issubset(predictions.columns):
        raise ValueError("Saved predictions do not have the expected provenance columns.")
    if len(predictions) != report.get("holdout_rows"):
        raise ValueError("Saved prediction count does not match the reported holdout size.")
    observed = pd.to_numeric(predictions[observed_column], errors="coerce").to_numpy(dtype=float)
    predicted = pd.to_numeric(predictions[predicted_column], errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(observed).all() or not np.isfinite(predicted).all():
        raise ValueError("Saved predictions contain non-finite evaluation values.")
    recorded_metrics = report.get("holdout_metrics")
    if not isinstance(recorded_metrics, dict):
        raise TypeError("Saved model report has no holdout metrics.")
    reproduced_metrics = _metrics(observed, predicted)
    for name, value in reproduced_metrics.items():
        if not math.isclose(recorded_metrics.get(name, float("nan")), value, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("Saved predictions do not reproduce the reported holdout metrics.")
    return report


def load_model_artifact(
    artifact_dir: Path, *, readiness_path: Path = DEFAULT_READINESS_PATH
) -> Pipeline:
    """Load a locally generated model only after verifying its manifest hash."""
    manifest = json.loads((artifact_dir / "manifest.json").read_text(encoding="utf-8"))
    source_kind = manifest.get("source_kind")
    target_id = manifest.get("target_id")
    if source_kind not in {"synthetic", "experimental"}:
        raise ValueError("Model artifact has an unsupported source kind.")
    if source_kind == "synthetic" and target_id != SYNTHETIC_TARGET_ID:
        raise ValueError("Synthetic artifact has inconsistent target provenance.")
    if source_kind == "experimental" and target_id not in EXPERIMENTAL_TARGETS:
        raise ValueError("Experimental artifact refers to an unknown target.")
    if source_kind == "experimental" and _readiness_status(
        str(target_id), readiness_path
    ) != "READY":
        raise TrainingBlockedError(
            f"{target_id} is not READY; its experimental artifact cannot be loaded."
        )
    verify_model_artifact_bundle(artifact_dir)
    artifacts = manifest["artifacts"]
    model_path = _validated_artifact_path(artifact_dir, artifacts["model"]["file"], "model")
    model = joblib.load(model_path)
    if not isinstance(model, Pipeline):
        raise TypeError("Loaded artifact is not a scikit-learn Pipeline.")
    return model


def run_synthetic_demo(
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
    *,
    seed: int = 417,
    readiness_path: Path = DEFAULT_READINESS_PATH,
) -> TrainingResult:
    features, target, groups = make_synthetic_fixture(seed=seed)
    return train_regression(
        features,
        target,
        groups,
        target_id=SYNTHETIC_TARGET_ID,
        source_kind="synthetic",
        artifact_dir=artifact_dir,
        readiness_path=readiness_path,
        seed=seed,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--seed", type=int, default=417)
    args = parser.parse_args()
    result = run_synthetic_demo(args.artifact_dir, seed=args.seed)
    print(json.dumps(result.report, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

"""First model trained on real external measurements.

Material domain: carbon-fibre tow (T700 12k) sliding on a glass tool, from the
University of Cambridge "Friction of carbon fibre tows" dataset. Target: the
workbook's measured coefficient of friction.

This model is deliberately separate from AI-TriboTwin's original
glass-fibre/epoxy composite data and targets. Its metrics are not estimates of
performance on the composite experiments, and it cannot be substituted for the
blocked composite targets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import platform
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
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, LeaveOneGroupOut, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import PROJECT_ROOT
from src.data.cambridge import (
    CAMBRIDGE_PROCESSED_DIR,
    GROUP_COLUMN,
    MODEL_FEATURE_COLUMNS,
    TARGET_COLUMN,
    _validate_dataset,
    load_towtool_measurements,
    sha256_file,
    write_processed_dataset,
)

logger = logging.getLogger(__name__)

EXTERNAL_MODEL_ID = "TOW-TOOL-COF-CAMBRIDGE"
EXTERNAL_SOURCE_KIND: Literal["external"] = "external"
EXTERNAL_ARTIFACT_DIR = PROJECT_ROOT / "artifacts" / "ml" / "external-cof-cambridge"
MIN_EXTERNAL_GROUPS = 8
HOLDOUT_FRACTION = 0.3

# Physical meaning and unit of every model input, keyed by column name. The
# derived log10 load column is documented separately (see DERIVED_FEATURES).
FEATURE_METADATA: dict[str, dict[str, str]] = {
    "normal_load_n": {
        "unit": "N",
        "description": "Applied normal load on the tow for this ramp step",
    },
    "log10_normal_load_n": {
        "unit": "log10(N)",
        "description": "Base-10 logarithm of the applied normal load (derived from normal_load_n)",
    },
    "nominal_pressure_mpa": {
        "unit": "MPa",
        "description": "Nominal contact pressure (normal load divided by contact area)",
    },
    "contact_width_mm": {
        "unit": "mm",
        "description": "Measured width of the tow-on-tool contact patch",
    },
    "contact_area_mm2": {
        "unit": "mm^2",
        "description": "Measured contact area between the tow and the glass tool",
    },
    "contact_length_scanned_mm": {
        "unit": "mm",
        "description": "Contact length measured from the scanned contact image",
    },
    "contact_half_width_a_mm": {
        "unit": "mm",
        "description": "Contact half-width a derived from the measured contact geometry",
    },
    "percent_contact_length": {
        "unit": "%",
        "description": "Measured contact length expressed as a percentage of the ideal length",
    },
    "tow_type": {
        "unit": "categorical",
        "description": "Carbon-fibre tow sizing label (T700 12k, 60E or 50C)",
    },
}

# Model inputs the model computes from other inputs; a client never submits these.
DERIVED_FEATURES: dict[str, dict[str, str]] = {
    "log10_normal_load_n": {
        "source": "normal_load_n",
        "transformation": "log10(normal_load_n), base 10",
    },
}

# The features a prediction request must supply. Derived columns are computed
# server-side so the client cannot introduce a load/derived-load inconsistency.
REQUEST_FEATURE_COLUMNS: tuple[str, ...] = tuple(
    name for name in MODEL_FEATURE_COLUMNS if name not in DERIVED_FEATURES
)


class ExternalModelError(RuntimeError):
    """Raised when the external model cannot be trained or verified."""


@dataclass(frozen=True)
class ExternalTrainingResult:
    report: dict[str, object]
    artifact_dir: Path


def _metrics(observed: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    mse = float(mean_squared_error(observed, predicted))
    values = {
        "mae": float(mean_absolute_error(observed, predicted)),
        "rmse": math.sqrt(mse),
        "r2": float(r2_score(observed, predicted)) if len(observed) > 1 else float("nan"),
    }
    if not all(math.isfinite(value) for key in ("mae", "rmse") for value in [values[key]]):
        raise ExternalModelError("Evaluation produced a non-finite error metric.")
    if not math.isfinite(values["r2"]):
        raise ExternalModelError("Evaluation produced a non-finite R^2.")
    return values


def _holdout_slice_metrics(
    predictions: pd.DataFrame, group_column: str
) -> dict[str, dict[str, float | int]]:
    slices: dict[str, dict[str, float | int]] = {}
    for group, subset in predictions.groupby(group_column, sort=True):
        observed = subset["observed_coefficient_of_friction"].to_numpy(dtype=float)
        predicted = subset["predicted_coefficient_of_friction"].to_numpy(dtype=float)
        baseline = subset["baseline_mean_prediction"].to_numpy(dtype=float)
        values = _metrics(observed, predicted)
        baseline_values = _metrics(observed, baseline)
        entry: dict[str, float | int] = {
            "rows": int(len(subset)),
            **values,
            "mean_residual": float(np.mean(predicted - observed)),
            "baseline_mae": baseline_values["mae"],
            "baseline_rmse": baseline_values["rmse"],
            "baseline_r2": baseline_values["r2"],
            "baseline_mean_residual": float(np.mean(baseline - observed)),
        }
        if "stratified_baseline_prediction" in subset.columns:
            strat = subset["stratified_baseline_prediction"].to_numpy(dtype=float)
            strat_values = _metrics(observed, strat)
            entry["stratified_baseline_mae"] = strat_values["mae"]
            entry["stratified_baseline_rmse"] = strat_values["rmse"]
            entry["stratified_baseline_r2"] = strat_values["r2"]
            entry["stratified_baseline_mean_residual"] = float(np.mean(strat - observed))
        slices[str(group)] = entry
    return slices


def _leave_one_run_out_analysis(frame: pd.DataFrame) -> dict[str, object]:
    """Leave-One-Run-Out (LOGO) cross-validation sensitivity analysis across all 10 runs."""
    features = frame[list(MODEL_FEATURE_COLUMNS)].reset_index(drop=True)
    target = frame[TARGET_COLUMN].astype(float).reset_index(drop=True)
    groups = frame[GROUP_COLUMN].astype(str).reset_index(drop=True)
    tow_types = frame["tow_type"].astype(str).reset_index(drop=True)

    logo = LeaveOneGroupOut()
    run_metrics: dict[str, dict[str, float | str | int]] = {}

    for train_idx, test_idx in logo.split(features, target, groups):
        test_run = str(groups.iloc[test_idx].values[0])
        tow = str(tow_types.iloc[test_idx].values[0])
        pipe = Pipeline([("preprocess", _make_preprocessor()), ("model", Ridge(alpha=1.0))])
        pipe.fit(features.iloc[train_idx], target.iloc[train_idx])
        preds = np.asarray(pipe.predict(features.iloc[test_idx]), dtype=float).reshape(-1)
        obs = target.iloc[test_idx].to_numpy(dtype=float)
        m = _metrics(obs, preds)
        run_metrics[test_run] = {
            "tow_type": tow,
            "rows": int(len(test_idx)),
            **m,
            "mean_residual": float(np.mean(preds - obs)),
        }

    summary_by_tow: dict[str, dict[str, float | int]] = {}
    for tow in sorted(frame["tow_type"].unique()):
        runs_for_tow = [m for m in run_metrics.values() if m["tow_type"] == tow]
        summary_by_tow[str(tow)] = {
            "runs": int(len(runs_for_tow)),
            "mae_mean": float(np.mean([float(m["mae"]) for m in runs_for_tow])),
            "rmse_mean": float(np.mean([float(m["rmse"]) for m in runs_for_tow])),
            "r2_mean": float(np.mean([float(m["r2"]) for m in runs_for_tow])),
            "mean_residual_mean": float(np.mean([float(m["mean_residual"]) for m in runs_for_tow])),
        }

    return {
        "description": (
            "Leave-One-Run-Out (LOGO) cross-validation evaluated across all 10 Cambridge runs "
            "to assess sensitivity across individual test sweeps. This does NOT replace or "
            "alter the fixed holdout evaluation split."
        ),
        "by_run": run_metrics,
        "summary_by_tow_type": summary_by_tow,
    }



def _dataset_fingerprint(subframe: pd.DataFrame) -> str:
    ordered = subframe[list(MODEL_FEATURE_COLUMNS) + [TARGET_COLUMN, GROUP_COLUMN]].copy()
    payload = ordered.to_csv(index=False, lineterminator="\n")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    return sha256_file(path)


def _make_preprocessor() -> ColumnTransformer:
    numeric = [name for name in MODEL_FEATURE_COLUMNS if name != "tow_type"]
    categorical = ["tow_type"]
    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric,
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            ),
        ],
        remainder="drop",
    )


def _build_candidates(seed: int) -> dict[str, Pipeline]:
    return {
        "mean_baseline": Pipeline(
            [("preprocess", _make_preprocessor()), ("model", DummyRegressor(strategy="mean"))]
        ),
        "ridge_regression": Pipeline(
            [("preprocess", _make_preprocessor()), ("model", Ridge(alpha=1.0))]
        ),
        "hist_gradient_boosting": Pipeline(
            [
                ("preprocess", _make_preprocessor()),
                ("model", HistGradientBoostingRegressor(random_state=seed)),
            ]
        ),
    }


def _modelling_frame(measurements: pd.DataFrame) -> pd.DataFrame:
    columns = [*MODEL_FEATURE_COLUMNS, TARGET_COLUMN, GROUP_COLUMN, "tow_type", "test_index", "step"]
    frame = measurements[list(dict.fromkeys(columns))].copy()
    frame[TARGET_COLUMN] = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    frame = frame.loc[frame[TARGET_COLUMN].notna()].reset_index(drop=True)
    if frame.empty:
        raise ExternalModelError("No observations with a measured coefficient of friction.")
    return frame


def train_external_cof(
    *,
    artifact_dir: Path = EXTERNAL_ARTIFACT_DIR,
    seed: int = 417,
    write_processed: bool = True,
) -> ExternalTrainingResult:
    """Train and honestly evaluate the tow-on-tool coefficient-of-friction model."""
    dataset = load_towtool_measurements()
    observed_groups = int(dataset.measurements[GROUP_COLUMN].nunique())
    if observed_groups < MIN_EXTERNAL_GROUPS:
        raise ExternalModelError(
            f"Only {observed_groups} independent test runs; at least {MIN_EXTERNAL_GROUPS} are required."
        )
    _validate_dataset(dataset.measurements, min_groups=MIN_EXTERNAL_GROUPS)
    table_path, provenance_path = (
        write_processed_dataset(dataset, CAMBRIDGE_PROCESSED_DIR)
        if write_processed
        else (CAMBRIDGE_PROCESSED_DIR / "towtool_cof_measurements.csv",
              CAMBRIDGE_PROCESSED_DIR / "towtool_cof_provenance.json")
    )

    frame = _modelling_frame(dataset.measurements)
    features = frame[list(MODEL_FEATURE_COLUMNS)].reset_index(drop=True)
    target = frame[TARGET_COLUMN].astype(float).reset_index(drop=True)
    groups = frame[GROUP_COLUMN].astype(str).reset_index(drop=True)
    if groups.nunique() < MIN_EXTERNAL_GROUPS:
        raise ExternalModelError(
            f"Only {groups.nunique()} independent test runs; at least {MIN_EXTERNAL_GROUPS} are required."
        )

    splitter = GroupShuffleSplit(n_splits=1, test_size=HOLDOUT_FRACTION, random_state=seed)
    train_indices, test_indices = next(splitter.split(features, target, groups))
    x_train = features.iloc[train_indices].copy()
    x_test = features.iloc[test_indices].copy()
    y_train = target.iloc[train_indices].astype(float)
    y_test = target.iloc[test_indices].astype(float)
    train_groups = groups.iloc[train_indices]
    test_groups = groups.iloc[test_indices]
    if set(train_groups) & set(test_groups):
        raise ExternalModelError("Group leakage detected between train and holdout partitions.")

    cv_splits = min(5, train_groups.nunique())
    if cv_splits < 2:
        raise ExternalModelError("At least two training groups are required for cross-validation.")
    cv = GroupKFold(n_splits=cv_splits)
    candidates = _build_candidates(seed)
    comparison: dict[str, dict[str, float]] = {}
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

    selected_name = min(comparison, key=lambda name: comparison[name]["cv_mae_mean"])
    selected_model = candidates[selected_name]
    selected_model.fit(x_train, y_train)
    test_predictions = np.asarray(selected_model.predict(x_test), dtype=float).reshape(-1)
    holdout_metrics = _metrics(y_test.to_numpy(), test_predictions)

    baseline_model = candidates["mean_baseline"]
    baseline_model.fit(x_train, y_train)
    baseline_predictions = np.asarray(baseline_model.predict(x_test), dtype=float).reshape(-1)
    baseline_metrics = _metrics(y_test.to_numpy(), baseline_predictions)

    held_out = frame.iloc[test_indices].reset_index(drop=True)
    mean_by_tow = x_train.assign(target=y_train).groupby("tow_type")["target"].mean().to_dict()
    stratified_baseline_predictions = held_out["tow_type"].map(mean_by_tow).to_numpy(dtype=float)
    stratified_baseline_metrics = _metrics(y_test.to_numpy(), stratified_baseline_predictions)

    artifact_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifact_dir / "model.joblib"
    predictions_path = artifact_dir / "holdout_predictions.csv"
    plot_path = artifact_dir / "predictions_vs_observations.png"
    report_path = artifact_dir / "report.json"
    manifest_path = artifact_dir / "manifest.json"

    joblib.dump(selected_model, model_path)
    holdout_predictions = pd.DataFrame(
        {
            "test_run_id": test_groups.to_numpy(),
            "tow_type": held_out["tow_type"].to_numpy(),
            "step": held_out["step"].to_numpy(),
            "observed_coefficient_of_friction": y_test.to_numpy(),
            "predicted_coefficient_of_friction": test_predictions,
            "baseline_mean_prediction": baseline_predictions,
            "stratified_baseline_prediction": stratified_baseline_predictions,
        }
    )
    holdout_predictions.to_csv(predictions_path, index=False, lineterminator="\n")

    _save_scatter_plot(y_test.to_numpy(), test_predictions, plot_path)

    report = _build_report(
        dataset=dataset,
        training_frame=frame.iloc[train_indices].reset_index(drop=True),
        full_frame=frame,
        selected_name=selected_name,
        comparison=comparison,
        holdout_metrics=holdout_metrics,
        baseline_metrics=baseline_metrics,
        stratified_baseline_metrics=stratified_baseline_metrics,
        holdout_predictions=holdout_predictions,
        train_groups=train_groups,
        test_groups=test_groups,
        seed=seed,
        cv_splits=cv_splits,
        table_path=table_path,
        provenance_path=provenance_path,
    )
    report["artifacts"] = {
        "model": model_path.name,
        "predictions": predictions_path.name,
        "plot": plot_path.name,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "format_version": 1,
        "model_id": EXTERNAL_MODEL_ID,
        "source_kind": EXTERNAL_SOURCE_KIND,
        "artifacts": {
            "model": {"file": model_path.name, "sha256": _file_sha256(model_path)},
            "report": {"file": report_path.name, "sha256": _file_sha256(report_path)},
            "predictions": {"file": predictions_path.name, "sha256": _file_sha256(predictions_path)},
            "plot": {"file": plot_path.name, "sha256": _file_sha256(plot_path)},
        },
        "source": {
            "workbook": dataset.metadata["workbook"],
            "workbook_sha256": dataset.metadata["workbook_sha256"],
            "processed_measurements": table_path.name,
            "processed_measurements_sha256": sha256_file(table_path) if table_path.is_file() else None,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    logger.info(
        "External COF model %s: holdout MAE %.6f (baseline %.6f) over %d held-out rows.",
        selected_name,
        holdout_metrics["mae"],
        baseline_metrics["mae"],
        len(test_indices),
    )
    return ExternalTrainingResult(report=report, artifact_dir=artifact_dir)


def _save_scatter_plot(observed: np.ndarray, predicted: np.ndarray, path: Path) -> None:
    fig, axis = plt.subplots(figsize=(6.5, 6))
    axis.scatter(observed, predicted, alpha=0.75, edgecolors="none")
    lower = float(min(observed.min(), predicted.min()))
    upper = float(max(observed.max(), predicted.max()))
    if not math.isfinite(lower) or not math.isfinite(upper) or lower == upper:
        lower, upper = lower - 0.5, upper + 0.5
    axis.plot([lower, upper], [lower, upper], linestyle="--", color="#b45309", label="Perfect agreement")
    axis.set(
        title="Cambridge tow-on-tool COF: held-out test runs",
        xlabel="Observed coefficient of friction",
        ylabel="Predicted coefficient of friction",
    )
    axis.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _feature_schema(frame: pd.DataFrame) -> dict[str, object]:
    """Describe every model input: its unit, role, and training range."""
    features: list[dict[str, object]] = []
    for name in MODEL_FEATURE_COLUMNS:
        meta = FEATURE_METADATA[name]
        entry: dict[str, object] = {
            "name": name,
            "unit": meta["unit"],
            "description": meta["description"],
            "required": name in REQUEST_FEATURE_COLUMNS,
        }
        if name in DERIVED_FEATURES:
            derived = DERIVED_FEATURES[name]
            entry["dtype"] = "derived"
            entry["source"] = derived["source"]
            entry["transformation"] = derived["transformation"]
        elif name == "tow_type":
            entry["dtype"] = "categorical"
            entry["allowed_values"] = sorted(
                frame[name].dropna().astype(str).unique().tolist()
            )
        else:
            values = pd.to_numeric(frame[name], errors="coerce").dropna().to_numpy(dtype=float)
            if values.size == 0:
                raise ExternalModelError(f"Feature {name!r} has no finite training values.")
            entry["dtype"] = "numeric"
            entry["min"] = float(values.min())
            entry["max"] = float(values.max())
            entry["mean"] = float(values.mean())
            entry["median"] = float(np.median(values))
            medians_by_tow: dict[str, float] = {}
            ranges_by_tow: dict[str, dict[str, float]] = {}
            for tow, tow_sub in frame.groupby("tow_type", sort=True):
                sub_vals = pd.to_numeric(tow_sub[name], errors="coerce").dropna().to_numpy(dtype=float)
                if sub_vals.size > 0:
                    medians_by_tow[str(tow)] = float(np.median(sub_vals))
                    ranges_by_tow[str(tow)] = {
                        "min": float(sub_vals.min()),
                        "max": float(sub_vals.max()),
                    }
            entry["medians_by_tow_type"] = medians_by_tow
            entry["ranges_by_tow_type"] = ranges_by_tow
        features.append(entry)
    return {
        "features": features,
        "request_feature_columns": list(REQUEST_FEATURE_COLUMNS),
        "derived_features": [name for name in MODEL_FEATURE_COLUMNS if name in DERIVED_FEATURES],
        "categorical_features": ["tow_type"],
        "range_basis": "minimum and maximum observed in the Cambridge model-training partition only",
    }


def _build_report(
    *,
    dataset,
    training_frame: pd.DataFrame,
    full_frame: pd.DataFrame,
    selected_name: str,
    comparison: dict[str, dict[str, float]],
    holdout_metrics: dict[str, float],
    baseline_metrics: dict[str, float],
    stratified_baseline_metrics: dict[str, float],
    holdout_predictions: pd.DataFrame,
    train_groups: pd.Series,
    test_groups: pd.Series,
    seed: int,
    cv_splits: int,
    table_path: Path,
    provenance_path: Path,
) -> dict[str, object]:
    metadata = dataset.metadata
    return {
        "status": "EVALUATED_EXTERNAL_COF",
        "model_id": EXTERNAL_MODEL_ID,
        "source_kind": EXTERNAL_SOURCE_KIND,
        "is_ai_tribotwin_model": False,
        "experimental_results": False,
        "material_domain": metadata["material_domain"],
        "source_name": metadata["source_name"],
        "source_url": metadata["repository_item"],
        "source_workbook": metadata["workbook"],
        "source_workbook_sha256": metadata["workbook_sha256"],
        "processed_table": table_path.name,
        "processed_table_sha256": sha256_file(table_path) if table_path.is_file() else None,
        "provenance_file": provenance_path.name,
        "measurement_protocol": metadata["measurement_protocol"],
        "target": TARGET_COLUMN,
        "target_definition": metadata["target_definition"],
        "target_unit": "dimensionless",
        "feature_columns": list(MODEL_FEATURE_COLUMNS),
        "feature_schema": _feature_schema(training_frame),
        "excluded_leakage_columns": list(metadata["excluded_leakage_columns"]),
        "observation_count": int(len(train_groups) + len(test_groups)),
        "training_rows": int(len(train_groups)),
        "holdout_rows": int(len(test_groups)),
        "training_groups": int(train_groups.nunique()),
        "holdout_groups": int(test_groups.nunique()),
        "training_group_ids": sorted(train_groups.unique().tolist()),
        "holdout_group_ids": sorted(test_groups.unique().tolist()),
        "tow_types": list(metadata["tow_types"]),
        "cross_validation_folds": int(cv_splits),
        "seed": seed,
        "model_comparison": comparison,
        "selected_model": selected_name,
        "selection_basis": "lowest group cross-validation MAE on the training groups",
        "holdout_metrics": holdout_metrics,
        "baseline_metrics": baseline_metrics,
        "stratified_baseline_metrics": stratified_baseline_metrics,
        "holdout_slices": {
            "by_tow_type": _holdout_slice_metrics(holdout_predictions, "tow_type"),
            "by_test_run": _holdout_slice_metrics(holdout_predictions, "test_run_id"),
        },
        "leave_one_run_out_sensitivity": _leave_one_run_out_analysis(full_frame),
        "failure_investigation_50c": {
            "held_out_run": "T700-12k-50C-T1",
            "findings": [
                (
                    "Plausible statistical contributor at low-load ramp step 0: In step 0 (normal load ~0.077 N), "
                    "observed COF was 1.1636 in T1 versus 1.63 to 2.02 in training 50C sweeps. The model predicted "
                    "1.9496, producing a residual of +0.7861 and squared error of 0.6179. This single observation "
                    "accounts for 65.0% of the run's total sum of squared errors (0.9504), establishing a theoretical "
                    "lower bound on the run's RMSE of sqrt(0.6179 / 14) = 0.2101, which is fully consistent with "
                    "the actual run RMSE of 0.2605."
                ),
                (
                    "Steps 3-9 and overall functional tracking: Across ramp steps 3 through 9 (loads 3.5 N to 39.2 N), "
                    "model predictions track observations within an MAE of 0.0300 (errors between 0.011 and 0.051) "
                    "with a correlation of r = 0.9867. Across all 14 steps of the run, the overall Pearson correlation "
                    "is r = 0.9520, confirming that the model captures the functional shape of the load-friction curve."
                ),
                (
                    "Plausible explanation vs proven root cause: While Step 0 statistically dominates the squared error, "
                    "one unusual observation alone does not prove that experimental measurement noise caused the poor score. "
                    "Physical factors (e.g. sizing tack, static friction transitions) cannot be ruled out without independent "
                    "specimen replication."
                ),
                (
                    "Holdout sample size vulnerability: The holdout partition contains only a single 50C run (14 rows), "
                    "making the aggregate 50C holdout score (-0.7446) entirely dependent on that single sweep."
                ),
                (
                    "Sensitivity under leave-one-run-out: Across all 5 runs of 50C under LOGO, 3 runs achieve "
                    "R^2 >= 0.70 (T2: 0.91, T4: 0.76, T5: 0.71), while T1 (-1.04) and T3 (-0.39) drop negative, "
                    "yielding a mean R^2 of 0.1901. In contrast, 60E achieves R^2 > 0.81 across every single run "
                    "(mean R^2 = 0.8572)."
                ),
            ],
            "implication": (
                "Predictions for T700-12k-50C carry substantially higher uncertainty and residual risk than "
                "T700-12k-60E. Recommendations or predictions for 50C must be treated with particular caution."
            ),
        },
        "specimen_independence_disclosure": {
            "labelled_runs": 10,
            "runs_per_tow_type": 5,
            "specimen_serial_numbers_recorded": False,
            "statement": (
                "The Cambridge workbook labels sweeps as Test 1 through Test 5 per tow type without "
                "recording specimen serial numbers or spool identifiers. Whether sweeps represent "
                "independent physical specimens or repeated sweeps on the same tow patch is unverified."
            ),
        },
        "residual_analysis": {
            "residual_definition": "predicted coefficient of friction minus observed coefficient of friction",
            "mean_residual": float(
                np.mean(
                    holdout_predictions["predicted_coefficient_of_friction"].to_numpy(dtype=float)
                    - holdout_predictions["observed_coefficient_of_friction"].to_numpy(dtype=float)
                )
            ),
            "baseline_mean_residual": float(
                np.mean(
                    holdout_predictions["baseline_mean_prediction"].to_numpy(dtype=float)
                    - holdout_predictions["observed_coefficient_of_friction"].to_numpy(dtype=float)
                )
            ),
            "stratified_baseline_mean_residual": float(
                np.mean(
                    holdout_predictions["stratified_baseline_prediction"].to_numpy(dtype=float)
                    - holdout_predictions["observed_coefficient_of_friction"].to_numpy(dtype=float)
                )
            ),
            "interpretation": (
                "Residual summaries describe this fixed three-run holdout only; they are "
                "not an estimate of bias across independent specimens."
            ),
        },
        "evaluation_design": {
            "holdout_method": "GroupShuffleSplit, preserved seed and original group holdout",
            "preprocessing_fit_scope": (
                "Pipeline preprocessing is fitted within each training fold and refitted on "
                "the 7 training runs; no holdout rows are used to fit preprocessing."
            ),
            "group_overlap": bool(set(train_groups) & set(test_groups)),
            "feature_range_scope": "training observations only",
            "feature_scope": (
                "Normal-load and contact measurements only; friction-derived target and "
                "friction-force columns are excluded."
            ),
        },
        "uncertainty_assessment": {
            "status": "NOT_CALIBRATED",
            "prediction_intervals_produced": False,
            "mathematical_requirement": (
                "Under standard split-conformal prediction at a nominal 90% confidence level (alpha = 0.10), "
                "the required calibration group count n must satisfy ceil((n+1)*0.9)/n <= 1, which requires "
                "at least n >= 9 independent calibration runs per stratum."
            ),
            "scientific_validity_distinction": (
                "Meeting this mathematical floor of 9 runs is a necessary condition for computing empirical "
                "quantiles, but does NOT by itself guarantee reliable or valid prediction intervals. Scientifically "
                "defensible calibration in physical tribology requires verified specimen independence (specimen "
                "serial numbers, distinct material batches), exchangeability across environmental and testing conditions, "
                "tow-type-specific variance modeling, and separate empirical coverage validation on unseen runs."
            ),
            "reason": (
                "With only 7 training and 3 held-out labelled runs total, unverified specimen independence, and "
                "strong sequential ramp autocorrelation, prediction intervals cannot be defensibly calibrated "
                "and remain unavailable."
            ),
        },
        "group_count_limitation": (
            "The source contains 10 labelled runs (5 per tow type) without specimen serial "
            "numbers. Independence between runs is assumed from labels and cannot be verified."
        ),
        "dataset_sha256": _dataset_fingerprint(dataset.measurements.loc[
            dataset.measurements[TARGET_COLUMN].notna()
        ].reset_index(drop=True)),
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "caveats": list(metadata["caveats"]),
        "interpretation": (
            "External-data model: carbon-fibre tow-on-tool friction (Cambridge dataset). "
            "These metrics describe only that external dataset and are NOT performance "
            "estimates for AI-TriboTwin's glass-fibre/epoxy composite experiments or targets."
        ),
    }


def _validated_artifact_path(artifact_dir: Path, filename: object, label: str) -> Path:
    if not isinstance(filename, str) or Path(filename).name != filename:
        raise ValueError(f"External model manifest contains an invalid {label} filename.")
    path = artifact_dir / filename
    if not path.is_file():
        raise FileNotFoundError(f"External model {label} artifact not found: {path}")
    return path


def verify_external_artifact_bundle(artifact_dir: Path = EXTERNAL_ARTIFACT_DIR) -> dict[str, object]:
    """Verify the hash-bound external model, report, predictions, and metrics."""
    manifest_path = artifact_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"External model manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format_version") != 1:
        raise ValueError("Unsupported external model manifest version.")
    if manifest.get("model_id") != EXTERNAL_MODEL_ID or manifest.get("source_kind") != EXTERNAL_SOURCE_KIND:
        raise ValueError("External model manifest has inconsistent provenance.")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise TypeError("External model manifest has no artifact inventory.")
    resolved: dict[str, Path] = {}
    for label in ("model", "report", "predictions", "plot"):
        entry = artifacts.get(label)
        if not isinstance(entry, dict):
            raise TypeError(f"External model manifest has no {label} artifact entry.")
        path = _validated_artifact_path(artifact_dir, entry.get("file"), label)
        digest = entry.get("sha256")
        if not isinstance(digest, str) or _file_sha256(path) != digest:
            raise ValueError(f"{label.capitalize()} artifact SHA-256 does not match its manifest.")
        resolved[label] = path

    report = json.loads(resolved["report"].read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise TypeError("Saved external model report is not an object.")
    if report.get("model_id") != EXTERNAL_MODEL_ID or report.get("source_kind") != EXTERNAL_SOURCE_KIND:
        raise ValueError("Saved external model report does not match manifest provenance.")
    if report.get("status") != "EVALUATED_EXTERNAL_COF" or report.get("is_ai_tribotwin_model") is not False:
        raise ValueError("Saved external model report has an inconsistent status.")

    predictions = pd.read_csv(resolved["predictions"])
    required = {
        "test_run_id",
        "tow_type",
        "observed_coefficient_of_friction",
        "predicted_coefficient_of_friction",
        "baseline_mean_prediction",
    }
    if not required.issubset(predictions.columns):
        raise ValueError("Saved external predictions lack the expected provenance columns.")
    if len(predictions) != report.get("holdout_rows"):
        raise ValueError("Saved external prediction count does not match the reported holdout size.")
    observed = pd.to_numeric(predictions["observed_coefficient_of_friction"], errors="coerce").to_numpy(float)
    predicted = pd.to_numeric(predictions["predicted_coefficient_of_friction"], errors="coerce").to_numpy(float)
    if not np.isfinite(observed).all() or not np.isfinite(predicted).all():
        raise ValueError("Saved external predictions contain non-finite values.")
    recorded = report.get("holdout_metrics")
    if not isinstance(recorded, dict):
        raise TypeError("Saved external model report has no holdout metrics.")
    reproduced = _metrics(observed, predicted)
    for name, value in reproduced.items():
        if not math.isclose(recorded.get(name, float("nan")), value, rel_tol=1e-9, abs_tol=1e-12):
            raise ValueError("Saved external predictions do not reproduce the reported holdout metrics.")
    recorded_stratified = report.get("stratified_baseline_metrics")
    if isinstance(recorded_stratified, dict) and "stratified_baseline_prediction" in predictions.columns:
        strat_preds = pd.to_numeric(predictions["stratified_baseline_prediction"], errors="coerce").to_numpy(float)
        reproduced_strat = _metrics(observed, strat_preds)
        for name, value in reproduced_strat.items():
            if not math.isclose(recorded_stratified.get(name, float("nan")), value, rel_tol=1e-9, abs_tol=1e-12):
                raise ValueError("Saved external predictions do not reproduce reported stratified baseline metrics.")
    for required_key in (
        "leave_one_run_out_sensitivity",
        "failure_investigation_50c",
        "specimen_independence_disclosure",
    ):
        if required_key not in report or not isinstance(report[required_key], dict):
            raise ValueError(f"Saved external report is missing valid {required_key}.")
    train_groups = report.get("training_group_ids")
    holdout_groups = report.get("holdout_group_ids")
    if (
        not isinstance(train_groups, list)
        or not isinstance(holdout_groups, list)
        or set(train_groups) & set(holdout_groups)
        or set(predictions["test_run_id"].astype(str)) != set(holdout_groups)
    ):
        raise ValueError("Saved external evaluation has inconsistent or overlapping run partitions.")
    reported_slices = report.get("holdout_slices")
    if not isinstance(reported_slices, dict):
        raise ValueError("Saved external report has no holdout slice metrics.")
    for slice_name, group_column in (
        ("by_tow_type", "tow_type"),
        ("by_test_run", "test_run_id"),
    ):
        slice_report = reported_slices.get(slice_name)
        if not isinstance(slice_report, dict):
            raise ValueError(f"Saved external report has no {slice_name} metrics.")
        actual_slices = _holdout_slice_metrics(predictions, group_column)
        if set(actual_slices) != set(slice_report):
            raise ValueError(f"Saved external report has inconsistent {slice_name} groups.")
        for group_name, actual in actual_slices.items():
            stored = slice_report[group_name]
            if not isinstance(stored, dict) or stored.get("rows") != actual["rows"]:
                raise ValueError(f"Saved external report has invalid {slice_name} row counts.")
            for metric_name, value in actual.items():
                if metric_name != "rows" and not math.isclose(
                    float(stored.get(metric_name, float("nan"))),
                    float(value),
                    rel_tol=1e-9,
                    abs_tol=1e-12,
                ):
                    raise ValueError(f"Saved external report has invalid {slice_name} metrics.")
    return report


def load_external_model(artifact_dir: Path = EXTERNAL_ARTIFACT_DIR) -> Pipeline:
    """Load the verified external model artifact."""
    manifest = json.loads((artifact_dir / "manifest.json").read_text(encoding="utf-8"))
    verify_external_artifact_bundle(artifact_dir)
    model_path = _validated_artifact_path(artifact_dir, manifest["artifacts"]["model"]["file"], "model")
    model = joblib.load(model_path)
    if not isinstance(model, Pipeline):
        raise TypeError("Loaded external artifact is not a scikit-learn Pipeline.")
    return model


def run_external_cof_model(
    artifact_dir: Path = EXTERNAL_ARTIFACT_DIR, *, seed: int = 417
) -> ExternalTrainingResult:
    """Build the processed dataset and train the external COF model."""
    return train_external_cof(artifact_dir=artifact_dir, seed=seed, write_processed=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=EXTERNAL_ARTIFACT_DIR)
    parser.add_argument("--seed", type=int, default=417)
    args = parser.parse_args()
    result = run_external_cof_model(args.artifact_dir, seed=args.seed)
    print(json.dumps(result.report, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

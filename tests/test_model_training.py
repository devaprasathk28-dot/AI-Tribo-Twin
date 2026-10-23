from __future__ import annotations

import json
from typing import Literal

import numpy as np
import pandas as pd
import pytest

from src.models.training import (
    SYNTHETIC_TARGET_ID,
    TrainingBlockedError,
    load_model_artifact,
    make_synthetic_fixture,
    train_regression,
    verify_model_artifact_bundle,
)


def train_demo(
    tmp_path,
    *,
    source_kind: Literal["synthetic", "experimental"] = "synthetic",
    target_id: str = SYNTHETIC_TARGET_ID,
):
    features, target, groups = make_synthetic_fixture(group_count=30, rows_per_group=4)
    return train_regression(
        features,
        target,
        groups,
        target_id=target_id,
        source_kind=source_kind,
        artifact_dir=tmp_path,
    )


def test_synthetic_demo_trains_compares_and_saves_provenanced_artifacts(tmp_path) -> None:
    result = train_demo(tmp_path)
    report = result.report

    assert report["status"] == "EVALUATED_SYNTHETIC_DEMO"
    assert report["synthetic_only"] is True
    assert report["experimental_results"] is False
    assert report["source_kind"] == "synthetic"
    assert report["target_id"] == "SYNTHETIC-DEMO"
    assert report["holdout_groups"] > 0
    assert report["cross_validation_folds"] == 5
    assert set(report["model_comparison"]) == {"mean_baseline", "ridge_regression"}
    assert report["holdout_metrics"]["mae"] >= 0
    assert report["holdout_metrics"]["rmse"] >= 0
    assert np.isfinite(report["holdout_metrics"]["r2"])
    assert report["model_comparison"]["ridge_regression"]["cv_mae_mean"] < report[
        "model_comparison"
    ]["mean_baseline"]["cv_mae_mean"]
    assert (tmp_path / "report.json").is_file()
    assert (tmp_path / "manifest.json").is_file()
    assert (tmp_path / "model.joblib").is_file()
    assert (tmp_path / "holdout_predictions.csv").is_file()
    assert (tmp_path / "predictions_vs_observations.png").is_file()


def test_experimental_training_fails_closed_for_blocked_target(tmp_path) -> None:
    features, target, groups = make_synthetic_fixture(group_count=12, rows_per_group=2)

    with pytest.raises(TrainingBlockedError, match="TARGET-COF is BLOCKED"):
        train_regression(
            features,
            target,
            groups,
            target_id="TARGET-COF",
            source_kind="experimental",
            artifact_dir=tmp_path,
        )

    assert list(tmp_path.iterdir()) == []


def test_synthetic_data_cannot_be_labelled_as_experimental_target(tmp_path) -> None:
    with pytest.raises(ValueError, match="must use target_id='SYNTHETIC-DEMO'"):
        train_demo(tmp_path, target_id="TARGET-COF")


def test_unknown_experimental_target_is_rejected(tmp_path) -> None:
    features, target, groups = make_synthetic_fixture(group_count=12, rows_per_group=2)

    with pytest.raises(ValueError, match="Unknown experimental target"):
        train_regression(
            features,
            target,
            groups,
            target_id="TARGET-NOT-IN-REGISTER",
            source_kind="experimental",
            artifact_dir=tmp_path,
        )


def test_feature_missing_values_are_imputed_and_missing_targets_are_excluded(tmp_path) -> None:
    features, target, groups = make_synthetic_fixture(group_count=30, rows_per_group=4)
    features.loc[0, "load_n"] = np.nan
    target.loc[1] = np.nan
    result = train_regression(
        features,
        target,
        groups,
        target_id=SYNTHETIC_TARGET_ID,
        source_kind="synthetic",
        artifact_dir=tmp_path,
    )

    assert result.report["missing_target_rows_excluded"] == 1
    assert result.report["training_rows"] + result.report["holdout_rows"] == len(target) - 1


def test_missing_group_ids_are_rejected(tmp_path) -> None:
    features, target, groups = make_synthetic_fixture(group_count=12, rows_per_group=2)
    groups.iloc[0] = ""

    with pytest.raises(ValueError, match="non-empty independent-group"):
        train_regression(
            features,
            target,
            groups,
            target_id=SYNTHETIC_TARGET_ID,
            source_kind="synthetic",
            artifact_dir=tmp_path,
        )


def test_model_artifact_load_checks_manifest_hash(tmp_path) -> None:
    train_demo(tmp_path)

    loaded = load_model_artifact(tmp_path)
    features, _, _ = make_synthetic_fixture(group_count=12, rows_per_group=2)
    assert loaded.predict(features.iloc[:2]).shape == (2,)

    with (tmp_path / "model.joblib").open("ab") as stream:
        stream.write(b"tampered")
    with pytest.raises(ValueError, match="SHA-256"):
        load_model_artifact(tmp_path)


def test_artifact_bundle_rejects_tampered_report_or_predictions(tmp_path) -> None:
    train_demo(tmp_path)
    report_path = tmp_path / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["holdout_metrics"]["mae"] = 999
    report_path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError, match="Report artifact SHA-256"):
        verify_model_artifact_bundle(tmp_path)

    train_demo(tmp_path)
    predictions_path = tmp_path / "holdout_predictions.csv"
    predictions = pd.read_csv(predictions_path)
    predictions.loc[0, "predicted_synthetic_response"] += 1
    predictions.to_csv(predictions_path, index=False)

    with pytest.raises(ValueError, match="Predictions artifact SHA-256"):
        verify_model_artifact_bundle(tmp_path)


def test_blocked_experimental_model_artifact_cannot_be_loaded(tmp_path) -> None:
    train_demo(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_kind"] = "experimental"
    manifest["target_id"] = "TARGET-COF"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(TrainingBlockedError, match="TARGET-COF is not READY"):
        load_model_artifact(tmp_path)


def test_report_records_deterministic_fixture_fingerprint(tmp_path) -> None:
    first = train_demo(tmp_path / "first").report
    second = train_demo(tmp_path / "second").report

    assert first["dataset_sha256"] == second["dataset_sha256"]
    assert json.loads((tmp_path / "first" / "report.json").read_text())["source_kind"] == "synthetic"

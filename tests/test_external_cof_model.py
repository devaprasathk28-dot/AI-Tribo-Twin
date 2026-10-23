from __future__ import annotations

import json
import shutil

import numpy as np
import pandas as pd
import pytest

from src.data.cambridge import LEAKAGE_COLUMNS, MODEL_FEATURE_COLUMNS, TARGET_COLUMN, load_towtool_measurements
from src.models.external_cof import (
    EXTERNAL_MODEL_ID,
    ExternalModelError,
    load_external_model,
    train_external_cof,
    verify_external_artifact_bundle,
)


@pytest.fixture(scope="module")
def training(tmp_path_factory):
    artifact_dir = tmp_path_factory.mktemp("external-cof-artifacts")
    result = train_external_cof(artifact_dir=artifact_dir, seed=417, write_processed=True)
    return result, artifact_dir


def test_report_declares_external_provenance(training) -> None:
    report, _ = training
    body = report.report
    assert body["status"] == "EVALUATED_EXTERNAL_COF"
    assert body["source_kind"] == "external"
    assert body["model_id"] == EXTERNAL_MODEL_ID
    assert body["is_ai_tribotwin_model"] is False
    assert body["experimental_results"] is False
    assert "carbon" in str(body["material_domain"]).lower()
    assert body["caveats"]
    assert "NOT performance" in body["interpretation"]


def test_no_leakage_columns_are_used_as_features(training) -> None:
    report, _ = training
    feature_columns = report.report["feature_columns"]
    assert TARGET_COLUMN not in feature_columns
    for column in LEAKAGE_COLUMNS:
        assert column not in feature_columns


def test_metrics_are_finite_and_group_held_out(training) -> None:
    _, artifact_dir = training
    report = verify_external_artifact_bundle(artifact_dir)
    assert report["observation_count"] == 140
    assert report["training_rows"] + report["holdout_rows"] == 140
    assert report["holdout_groups"] >= 2
    assert not set(report["training_group_ids"]) & set(report["holdout_group_ids"])
    assert report["holdout_group_ids"] == [
        "T700-12k-50C-T1",
        "T700-12k-60E-T2",
        "T700-12k-60E-T4",
    ]
    assert report["evaluation_design"]["group_overlap"] is False
    for key in ("holdout_metrics", "baseline_metrics"):
        for name in ("mae", "rmse", "r2"):
            assert np.isfinite(report[key][name])


def test_report_includes_holdout_slices_residuals_and_calibration_limit(training) -> None:
    result, _ = training
    report = result.report

    assert set(report["holdout_slices"]["by_tow_type"]) == {
        "T700-12k-50C",
        "T700-12k-60E",
    }
    assert set(report["holdout_slices"]["by_test_run"]) == set(report["holdout_group_ids"])
    assert report["holdout_slices"]["by_tow_type"]["T700-12k-50C"]["rows"] == 14
    assert report["holdout_slices"]["by_tow_type"]["T700-12k-60E"]["rows"] == 28
    assert np.isfinite(report["residual_analysis"]["mean_residual"])
    assert np.isfinite(report["residual_analysis"]["baseline_mean_residual"])
    assert report["uncertainty_assessment"]["status"] == "NOT_CALIBRATED"
    assert report["uncertainty_assessment"]["prediction_intervals_produced"] is False
    assert "specimen" in report["group_count_limitation"]


def test_feature_range_schema_uses_training_partition_only(training) -> None:
    result, _ = training
    measurements = load_towtool_measurements().measurements
    training_groups = set(result.report["training_group_ids"])
    training_rows = measurements[measurements["test_run_id"].isin(training_groups)]
    load_range = next(
        item for item in result.report["feature_schema"]["features"]
        if item["name"] == "normal_load_n"
    )

    assert load_range["min"] == pytest.approx(training_rows["normal_load_n"].min())
    assert load_range["max"] == pytest.approx(training_rows["normal_load_n"].max())
    assert result.report["feature_schema"]["range_basis"].endswith("partition only")


def test_selected_model_beats_mean_baseline_on_holdout(training) -> None:
    report, _ = training
    body = report.report
    assert body["selected_model"] in body["model_comparison"]
    assert body["holdout_metrics"]["mae"] < body["baseline_metrics"]["mae"]
    assert body["holdout_metrics"]["r2"] > body["baseline_metrics"]["r2"]


def test_artifacts_are_written(training) -> None:
    _, artifact_dir = training
    for name in (
        "model.joblib",
        "holdout_predictions.csv",
        "predictions_vs_observations.png",
        "report.json",
        "manifest.json",
    ):
        assert (artifact_dir / name).is_file()
    predictions = pd.read_csv(artifact_dir / "holdout_predictions.csv")
    assert {
        "test_run_id",
        "observed_coefficient_of_friction",
        "predicted_coefficient_of_friction",
    }.issubset(predictions.columns)


def test_load_model_predicts_finite_values(training) -> None:
    _, artifact_dir = training
    model = load_external_model(artifact_dir)
    features = load_towtool_measurements().measurements[list(MODEL_FEATURE_COLUMNS)].head(3)
    predictions = np.asarray(model.predict(features), dtype=float)
    assert predictions.shape == (3,)
    assert np.isfinite(predictions).all()


def test_tampered_predictions_break_the_manifest_hash(training, tmp_path) -> None:
    _, artifact_dir = training
    copied = tmp_path / "copy"
    shutil.copytree(artifact_dir, copied)
    predictions_path = copied / "holdout_predictions.csv"
    predictions = pd.read_csv(predictions_path)
    predictions.loc[0, "predicted_coefficient_of_friction"] += 1.0
    predictions.to_csv(predictions_path, index=False)

    with pytest.raises(ValueError, match="SHA-256"):
        verify_external_artifact_bundle(copied)


def test_tampered_manifest_provenance_is_rejected(training, tmp_path) -> None:
    _, artifact_dir = training
    copied = tmp_path / "copy2"
    shutil.copytree(artifact_dir, copied)
    manifest = json.loads((copied / "manifest.json").read_text(encoding="utf-8"))
    manifest["model_id"] = "NOT-THE-MODEL"
    (copied / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="inconsistent provenance"):
        verify_external_artifact_bundle(copied)


def test_training_blocks_when_groups_are_insufficient(monkeypatch, tmp_path) -> None:
    import src.models.external_cof as module

    dataset = load_towtool_measurements()
    truncated = dataset.measurements[
        dataset.measurements["test_run_id"].isin(sorted(dataset.measurements["test_run_id"].unique())[:3])
    ]
    reduced = type(dataset)(measurements=truncated, metadata=dataset.metadata)
    monkeypatch.setattr(module, "load_towtool_measurements", lambda: reduced)

    with pytest.raises(ExternalModelError, match="at least 8 are required"):
        module.train_external_cof(artifact_dir=tmp_path / "blocked", write_processed=False)


def test_report_includes_stratified_baseline_and_logo_sensitivity(training) -> None:
    result, artifact_dir = training
    report = result.report

    # Stratified baseline metrics
    assert "stratified_baseline_metrics" in report
    strat = report["stratified_baseline_metrics"]
    assert np.isfinite(strat["mae"])
    assert np.isfinite(strat["rmse"])
    assert np.isfinite(strat["r2"])
    assert report["holdout_metrics"]["mae"] < strat["mae"]

    # LOGO Sensitivity
    assert "leave_one_run_out_sensitivity" in report
    logo = report["leave_one_run_out_sensitivity"]
    assert len(logo["by_run"]) == 10
    assert "T700-12k-60E" in logo["summary_by_tow_type"]
    assert "T700-12k-50C" in logo["summary_by_tow_type"]
    assert logo["summary_by_tow_type"]["T700-12k-60E"]["r2_mean"] > 0.80
    assert logo["summary_by_tow_type"]["T700-12k-60E"]["runs"] == 5
    assert logo["summary_by_tow_type"]["T700-12k-50C"]["runs"] == 5

    # Predictions CSV includes stratified baseline column
    predictions = pd.read_csv(artifact_dir / "holdout_predictions.csv")
    assert "stratified_baseline_prediction" in predictions.columns


def test_report_includes_50c_failure_investigation_and_specimen_independence(training) -> None:
    result, _ = training
    report = result.report

    # 50C Failure Investigation
    assert "failure_investigation_50c" in report
    inv = report["failure_investigation_50c"]
    assert inv["held_out_run"] == "T700-12k-50C-T1"
    assert len(inv["findings"]) >= 3
    assert any("step 0" in f.lower() for f in inv["findings"])
    assert any("correlation" in f.lower() for f in inv["findings"])

    # Specimen Independence Disclosure
    assert "specimen_independence_disclosure" in report
    disc = report["specimen_independence_disclosure"]
    assert disc["labelled_runs"] == 10
    assert disc["specimen_serial_numbers_recorded"] is False
    assert "serial numbers" in disc["statement"].lower()


def test_uncertainty_assessment_distinguishes_mathematical_floor_from_scientific_validity(
    training,
) -> None:
    result, _ = training
    report = result.report

    uncertainty = report["uncertainty_assessment"]
    assert uncertainty["status"] == "NOT_CALIBRATED"
    assert uncertainty["prediction_intervals_produced"] is False
    assert "mathematical_requirement" in uncertainty
    assert "scientific_validity_distinction" in uncertainty
    assert "ceil" in uncertainty["mathematical_requirement"] or "9" in uncertainty["mathematical_requirement"]
    assert "independence" in uncertainty["scientific_validity_distinction"].lower()


def test_recomputed_metrics_from_predictions_csv_match_report_exactly(training) -> None:
    result, artifact_dir = training
    report = result.report
    predictions = pd.read_csv(artifact_dir / "holdout_predictions.csv")

    y_true = predictions["observed_coefficient_of_friction"].to_numpy(dtype=float)
    y_pred = predictions["predicted_coefficient_of_friction"].to_numpy(dtype=float)
    b_mean = predictions["baseline_mean_prediction"].to_numpy(dtype=float)
    b_strat = predictions["stratified_baseline_prediction"].to_numpy(dtype=float)

    # 1. Overall metrics match
    assert len(y_true) == report["holdout_rows"] == 42
    overall_mae = float(np.mean(np.abs(y_pred - y_true)))
    overall_rmse = float(np.sqrt(np.mean((y_pred - y_true) ** 2)))
    ss_res = float(np.sum((y_pred - y_true) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    overall_r2 = float(1.0 - ss_res / ss_tot)
    assert overall_mae == pytest.approx(report["holdout_metrics"]["mae"], rel=1e-6)
    assert overall_rmse == pytest.approx(report["holdout_metrics"]["rmse"], rel=1e-6)
    assert overall_r2 == pytest.approx(report["holdout_metrics"]["r2"], rel=1e-6)

    # 2. Slices by tow type match
    for tow, slice_rep in report["holdout_slices"]["by_tow_type"].items():
        mask = (predictions["tow_type"] == tow).to_numpy()
        sub_y = y_true[mask]
        sub_pred = y_pred[mask]
        mae = float(np.mean(np.abs(sub_pred - sub_y)))
        rmse = float(np.sqrt(np.mean((sub_pred - sub_y) ** 2)))
        r2 = float(1.0 - np.sum((sub_pred - sub_y) ** 2) / np.sum((sub_y - np.mean(sub_y)) ** 2))
        assert mae == pytest.approx(slice_rep["mae"], rel=1e-6)
        assert rmse == pytest.approx(slice_rep["rmse"], rel=1e-6)
        assert r2 == pytest.approx(slice_rep["r2"], rel=1e-6)

    # 3. Slices by test run match
    for run, run_rep in report["holdout_slices"]["by_test_run"].items():
        mask = (predictions["test_run_id"] == run).to_numpy()
        sub_y = y_true[mask]
        sub_pred = y_pred[mask]
        mae = float(np.mean(np.abs(sub_pred - sub_y)))
        rmse = float(np.sqrt(np.mean((sub_pred - sub_y) ** 2)))
        r2 = float(1.0 - np.sum((sub_pred - sub_y) ** 2) / np.sum((sub_y - np.mean(sub_y)) ** 2))
        assert mae == pytest.approx(run_rep["mae"], rel=1e-6)
        assert rmse == pytest.approx(run_rep["rmse"], rel=1e-6)
        assert r2 == pytest.approx(run_rep["r2"], rel=1e-6)


def test_rmse_lower_bound_detects_impossible_metrics(training) -> None:
    result, artifact_dir = training
    report = result.report
    predictions = pd.read_csv(artifact_dir / "holdout_predictions.csv")

    # Mathematical property: For any dataset with N residuals,
    # RMSE = sqrt(sum(e_i^2) / N) >= sqrt(max(e_i^2) / N) = max(|e_i|) / sqrt(N).
    for run, run_rep in report["holdout_slices"]["by_test_run"].items():
        mask = (predictions["test_run_id"] == run).to_numpy()
        residuals = (
            predictions.loc[mask, "predicted_coefficient_of_friction"].to_numpy(dtype=float)
            - predictions.loc[mask, "observed_coefficient_of_friction"].to_numpy(dtype=float)
        )
        n = len(residuals)
        max_sq_error = float(np.max(residuals**2))
        theoretical_min_rmse = float(np.sqrt(max_sq_error / n))

        # Reported RMSE must be >= theoretical minimum
        reported_rmse = float(run_rep["rmse"])
        assert reported_rmse >= theoretical_min_rmse - 1e-9

        # Specifically for 50C-T1, verify that an impossible RMSE like 0.2064 would fail
        if run == "T700-12k-50C-T1":
            assert theoretical_min_rmse > 0.2100
            assert reported_rmse == pytest.approx(0.260546, rel=1e-4)
            impossible_rmse = 0.2064
            assert impossible_rmse < theoretical_min_rmse


def test_manifest_model_predictions_exact_provenance_and_scoring_consistency(training) -> None:
    result, artifact_dir = training
    report = result.report
    predictions = pd.read_csv(artifact_dir / "holdout_predictions.csv")
    model = load_external_model(artifact_dir)

    # Re-score the holdout rows from the raw Cambridge dataset with the loaded model
    dataset = load_towtool_measurements()
    held_out = dataset.measurements[
        dataset.measurements["test_run_id"].isin(report["holdout_group_ids"])
    ]
    features = held_out[list(MODEL_FEATURE_COLUMNS)]
    recomputed_preds = np.asarray(model.predict(features), dtype=float).reshape(-1)
    saved_preds = predictions["predicted_coefficient_of_friction"].to_numpy(dtype=float)

    # Must match within machine floating point precision
    assert np.max(np.abs(recomputed_preds - saved_preds)) < 1e-12

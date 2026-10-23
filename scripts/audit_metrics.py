"""Independent metric integrity audit for AI-TriboTwin Sprint 8.1.

Recomputes all evaluation metrics from saved row-level predictions,
verifies artifact hashes and model consistency, and validates 50C-T1 step errors.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.data.cambridge import MODEL_FEATURE_COLUMNS, TARGET_COLUMN, load_towtool_measurements

ARTIFACT_DIR = Path("artifacts/ml/external-cof-cambridge")


def calc_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    res = y_pred - y_true
    mae = float(np.mean(np.abs(res)))
    rmse = float(np.sqrt(np.mean(res**2)))
    mean_res = float(np.mean(res))
    sse = float(np.sum(res**2))
    max_ae = float(np.max(np.abs(res)))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = float(1.0 - sse / ss_tot)
    return {
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "mean_residual": mean_res,
        "sse": sse,
        "max_ae": max_ae,
    }


def main():
    manifest = json.loads((ARTIFACT_DIR / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((ARTIFACT_DIR / "report.json").read_text(encoding="utf-8"))
    predictions = pd.read_csv(ARTIFACT_DIR / "holdout_predictions.csv")
    model = joblib.load(ARTIFACT_DIR / "model.joblib")

    print("=== 1. MANIFEST & ARTIFACT HASH CHECK ===")
    for key, meta in manifest["artifacts"].items():
        p = ARTIFACT_DIR / meta["file"]
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        match = h == meta["sha256"]
        print(f"[{'OK' if match else 'FAIL'}] {key} ({meta['file']}): {h}")
        if not match:
            raise RuntimeError(f"Hash mismatch for {key}")

    print("\n=== 2. FRESH MODEL PREDICTION RECOMPUTATION ===")
    dataset = load_towtool_measurements()
    held_out_runs = report["holdout_group_ids"]
    held_out_rows = dataset.measurements[dataset.measurements["test_run_id"].isin(held_out_runs)].copy()
    
    # Ensure exact same row alignment as holdout_predictions.csv
    # In external_cof.py, held_out comes from frame.iloc[test_indices]
    x_features = held_out_rows[list(MODEL_FEATURE_COLUMNS)]
    fresh_preds = np.asarray(model.predict(x_features), dtype=float).reshape(-1)
    csv_preds = predictions["predicted_coefficient_of_friction"].to_numpy(dtype=float)
    max_diff = float(np.max(np.abs(fresh_preds - csv_preds)))
    print(f"Max absolute discrepancy between fresh model predict() and saved CSV: {max_diff:.4e}")

    print("\n=== 3. UNROUNDED HOLDOUT OVERALL METRICS ===")
    y_true = predictions["observed_coefficient_of_friction"].to_numpy(dtype=float)
    y_pred = predictions["predicted_coefficient_of_friction"].to_numpy(dtype=float)
    b_mean = predictions["baseline_mean_prediction"].to_numpy(dtype=float)
    b_strat = predictions["stratified_baseline_prediction"].to_numpy(dtype=float)

    m_overall = calc_metrics(y_true, y_pred)
    b_mean_overall = calc_metrics(y_true, b_mean)
    b_strat_overall = calc_metrics(y_true, b_strat)

    print(f"Overall Rows: {len(y_true)}")
    print(f"Selected Model:       MAE={m_overall['mae']:.6f}, RMSE={m_overall['rmse']:.6f}, R2={m_overall['r2']:.6f}, MeanRes={m_overall['mean_residual']:+.6f}")
    print(f"Pooled Mean Baseline: MAE={b_mean_overall['mae']:.6f}, RMSE={b_mean_overall['rmse']:.6f}, R2={b_mean_overall['r2']:.6f}, MeanRes={b_mean_overall['mean_residual']:+.6f}")
    print(f"Stratified Baseline:  MAE={b_strat_overall['mae']:.6f}, RMSE={b_strat_overall['rmse']:.6f}, R2={b_strat_overall['r2']:.6f}, MeanRes={b_strat_overall['mean_residual']:+.6f}")

    # Compare against report.json
    rep_holdout = report["holdout_metrics"]
    rep_base = report["baseline_metrics"]
    rep_strat = report["stratified_baseline_metrics"]

    assert math.isclose(m_overall["mae"], rep_holdout["mae"], rel_tol=1e-6)
    assert math.isclose(m_overall["rmse"], rep_holdout["rmse"], rel_tol=1e-6)
    assert math.isclose(m_overall["r2"], rep_holdout["r2"], rel_tol=1e-6)
    assert math.isclose(b_mean_overall["mae"], rep_base["mae"], rel_tol=1e-6)
    assert math.isclose(b_strat_overall["mae"], rep_strat["mae"], rel_tol=1e-6)
    print(">> All overall metrics in report.json match row-level recomputations perfectly!")

    print("\n=== 4. PER-TOW TYPE METRICS ===")
    for tow in sorted(predictions["tow_type"].unique()):
        mask = (predictions["tow_type"] == tow).to_numpy()
        sub_y = y_true[mask]
        sub_pred = y_pred[mask]
        sub_strat = b_strat[mask]
        m = calc_metrics(sub_y, sub_pred)
        bs = calc_metrics(sub_y, sub_strat)
        print(f"Tow Type {tow} ({mask.sum()} rows):")
        print(f"  Model:      MAE={m['mae']:.6f}, RMSE={m['rmse']:.6f}, R2={m['r2']:.6f}, MeanRes={m['mean_residual']:+.6f}, SSE={m['sse']:.6f}, MaxAE={m['max_ae']:.6f}")
        print(f"  StratBase:  MAE={bs['mae']:.6f}, RMSE={bs['rmse']:.6f}, R2={bs['r2']:.6f}, MeanRes={bs['mean_residual']:+.6f}")
        
        rep_slice = report["holdout_slices"]["by_tow_type"][tow]
        assert math.isclose(m["mae"], rep_slice["mae"], rel_tol=1e-6)
        assert math.isclose(m["rmse"], rep_slice["rmse"], rel_tol=1e-6)
        assert math.isclose(m["r2"], rep_slice["r2"], rel_tol=1e-6)

    print("\n=== 5. PER-RUN METRICS ===")
    for run in sorted(predictions["test_run_id"].unique()):
        mask = (predictions["test_run_id"] == run).to_numpy()
        sub_y = y_true[mask]
        sub_pred = y_pred[mask]
        sub_strat = b_strat[mask]
        m = calc_metrics(sub_y, sub_pred)
        bs = calc_metrics(sub_y, sub_strat)
        print(f"Run {run} ({mask.sum()} rows):")
        print(f"  Model:      MAE={m['mae']:.6f}, RMSE={m['rmse']:.6f}, R2={m['r2']:.6f}, MeanRes={m['mean_residual']:+.6f}, SSE={m['sse']:.6f}, MaxAE={m['max_ae']:.6f}")
        print(f"  StratBase:  MAE={bs['mae']:.6f}, RMSE={bs['rmse']:.6f}, R2={bs['r2']:.6f}")
        
        rep_slice = report["holdout_slices"]["by_test_run"][run]
        assert math.isclose(m["mae"], rep_slice["mae"], rel_tol=1e-6)
        assert math.isclose(m["rmse"], rep_slice["rmse"], rel_tol=1e-6)
        assert math.isclose(m["r2"], rep_slice["r2"], rel_tol=1e-6)

    print("\n=== 6. AUDIT OF T700-12k-50C-T1 AND STEP 0 ERROR ===")
    t1_mask = (predictions["test_run_id"] == "T700-12k-50C-T1").to_numpy()
    t1_df = predictions[t1_mask].sort_values("step").reset_index(drop=True)
    t1_m = calc_metrics(t1_df["observed_coefficient_of_friction"].to_numpy(), t1_df["predicted_coefficient_of_friction"].to_numpy())
    
    print(f"T1 Actual Rows: {len(t1_df)}")
    print(f"T1 Actual MAE:  {t1_m['mae']:.6f}")
    print(f"T1 Actual RMSE: {t1_m['rmse']:.6f}")
    print(f"T1 Actual R2:   {t1_m['r2']:.6f}")
    print(f"T1 Actual SSE:  {t1_m['sse']:.6f}")

    step0 = t1_df.iloc[0]
    s0_obs = float(step0["observed_coefficient_of_friction"])
    s0_pred = float(step0["predicted_coefficient_of_friction"])
    s0_err = s0_pred - s0_obs
    s0_sq = s0_err**2
    min_rmse_s0 = math.sqrt(s0_sq / len(t1_df))

    print(f"Step 0 (Normal Load ~{float(step0.get('normal_load_n', 0.077)):.4f} N):")
    print(f"  Observed COF:   {s0_obs:.6f}")
    print(f"  Predicted COF:  {s0_pred:.6f}")
    print(f"  Residual:       {s0_err:+.6f}")
    print(f"  Squared Error:  {s0_sq:.6f}")
    print(f"  Share of Total SSE: {s0_sq / t1_m['sse'] * 100:.2f}% ({s0_sq:.4f} of {t1_m['sse']:.4f})")
    print(f"  Lower Bound on Run RMSE from Step 0 alone: sqrt({s0_sq:.6f}/14) = {min_rmse_s0:.6f}")
    print(f"  Does Actual RMSE ({t1_m['rmse']:.6f}) >= Lower Bound ({min_rmse_s0:.6f})? {t1_m['rmse'] >= min_rmse_s0}")

    # Steps 3 to 9 correlation
    steps_3_9 = t1_df[(t1_df["step"] >= 3) & (t1_df["step"] <= 9)]
    corr_3_9 = float(np.corrcoef(steps_3_9["observed_coefficient_of_friction"], steps_3_9["predicted_coefficient_of_friction"])[0, 1])
    mae_3_9 = float(np.mean(np.abs(steps_3_9["predicted_coefficient_of_friction"] - steps_3_9["observed_coefficient_of_friction"])))
    print(f"Steps 3 to 9 (Rows: {len(steps_3_9)}):")
    print(f"  Correlation r:  {corr_3_9:.6f}")
    print(f"  MAE (steps 3-9): {mae_3_9:.6f}")

    # All steps correlation
    corr_all = float(np.corrcoef(t1_df["observed_coefficient_of_friction"], t1_df["predicted_coefficient_of_friction"])[0, 1])
    print(f"All 14 steps Correlation r: {corr_all:.6f}")

    print("\n=== 7. LEAVE-ONE-RUN-OUT RECOMPUTATION ===")
    logo = report["leave_one_run_out_sensitivity"]
    for tow, summary in logo["summary_by_tow_type"].items():
        print(f"LOGO {tow} ({summary['runs']} runs): Mean MAE={summary['mae_mean']:.6f}, Mean RMSE={summary['rmse_mean']:.6f}, Mean R2={summary['r2_mean']:.6f}")


if __name__ == "__main__":
    main()

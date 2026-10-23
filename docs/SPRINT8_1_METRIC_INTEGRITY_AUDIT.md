# Sprint 8.1 — Evaluation Metric Integrity Audit

## Objective & Background
During the review of Sprint 8, a critical numerical contradiction was identified in the markdown report:
- The report stated that held-out run `T700-12k-50C-T1` had an RMSE of `0.2064` across its 14 rows.
- Concurrently, the report documented that Step 0 had an observed COF of `1.1636` and predicted COF of `1.9496` (absolute error $\approx 0.7860$, squared error $\approx 0.61789$).
- Mathematically, a single squared error of $0.61789$ enforces a strict theoretical lower bound:
  $$\mathrm{RMSE} \ge \sqrt{\frac{0.61789}{14}} \approx 0.210083$$
- An RMSE of `0.2064` is mathematically impossible for that prediction set.

Sprint 8.1 performs a rigorous, ground-up audit of the evaluation artifacts, resolves the contradiction, independently recomputes all metrics directly from row-level predictions, audits the 50C-T1 Step 0 error and correlation claims, verifies model/artifact provenance, and adds automated regression tests to prevent mathematical metric inconsistencies.

---

## 1. Investigation & Root Cause of the Contradiction

### Artifact vs. Report Discrepancy
We inspected the saved model bundle in `artifacts/ml/external-cof-cambridge/` (`report.json`, `holdout_predictions.csv`, and `manifest.json`):
1. **Actual Artifact Content**:
   - In `holdout_predictions.csv`, the 14 rows for `T700-12k-50C-T1` yield:
     $$\mathrm{SSE} = \sum_{i=1}^{14} (\widehat{y}_i - y_i)^2 = 0.95037699\dots$$
     $$\mathrm{RMSE} = \sqrt{\frac{0.95037699}{14}} = \mathbf{0.26054578\dots} \approx \mathbf{0.2605}$$
     $$\mathrm{MAE} = \frac{1}{14} \sum_{i=1}^{14} |\widehat{y}_i - y_i| = \mathbf{0.15712930\dots} \approx \mathbf{0.1571}$$
   - In `report.json`, under `holdout_slices.by_test_run["T700-12k-50C-T1"]` and `holdout_slices.by_tow_type["T700-12k-50C"]`, the metrics recorded by the training script were:
     `{"rows": 14, "mae": 0.157129, "rmse": 0.260546, "r2": -0.744623}`.
   - In the frontend dashboard (`src/app/models/page.tsx`), the values rendered from `report.json` were MAE `0.1571`, RMSE `0.2605`.

2. **The Root Cause**:
   - The underlying model, `holdout_predictions.csv`, and `report.json` **never contained an RMSE of 0.2064**.
   - `0.2064` was a **typographical transcription error** in the manual markdown table written in `docs/SPRINT8_RECOMMENDATION_VALIDATION.md` (and repeated in the accompanying chat summary).
   - In that table, the metrics for `T700-12k-60E` (MAE 0.1225, RMSE 0.2070) were inadvertently mistranscribed into the 50C row as `MAE: 0.1215` and `RMSE: 0.2064`.
   - Under the genuine, unrounded artifact metric **$\mathrm{RMSE} = 0.260546$**, the mathematical lower bound $\mathrm{RMSE} \ge 0.210083$ is cleanly and strictly satisfied ($0.260546 \ge 0.210083$).

---

## 2. Independent Ground-Up Recomputation of All Metrics

Using [`scripts/audit_metrics.py`](file:///c:/Users/devap/Documents/AI-TriboTwin/scripts/audit_metrics.py), all metrics were independently calculated from the unrounded row-level data in `holdout_predictions.csv`:

### Overall Holdout Evaluation (42 rows across 3 held-out runs)

| Estimator / Baseline | MAE | RMSE | $R^2$ | Mean Residual | SSE | Max Absolute Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Selected Ridge Model** | **0.134026** | **0.226287** | **+0.782574** | **+0.083996** | 2.150639 | 0.870035 |
| **Pooled Mean Baseline** | 0.273719 | 0.486239 | -0.003905 | +0.030325 | 9.930034 | 0.942730 |
| **Tow-Stratified Baseline** | 0.273859 | 0.486247 | -0.003937 | +0.030514 | 9.930353 | 0.942391 |

*Note: All unrounded values match `report.json` within floating-point precision ($< 10^{-6}$). The Ridge model outperforms both baselines by 51.0% lower MAE and 53.5% lower RMSE.*

### Sliced Generalization by Tow Type on the Holdout

| Tow Type | Runs in Holdout | Rows | Ridge MAE | Ridge RMSE | Ridge $R^2$ | Mean Residual | Stratified Baseline MAE | Stratified Baseline RMSE | Stratified Baseline $R^2$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T700-12k-60E** | 2 (`T2`, `T4`) | 28 | **0.122475** | **0.207042** | **+0.871567** | +0.047430 | 0.340357 | 0.578358 | -0.002192 |
| **T700-12k-50C** | 1 (`T1`) | 14 | **0.157129** | **0.260546** | **-0.744623** | **+0.157129** | **0.140862** | **0.200780** | **-0.036036** |

### Per-Run Holdout Results

| Run ID | Tow Type | Rows | Ridge MAE | Ridge RMSE | Ridge $R^2$ | Mean Residual | Stratified Baseline MAE | SSE | Max AE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T700-12k-60E-T2** | 60E | 14 | 0.072589 | 0.107104 | +0.947924 | +0.046789 | 0.312072 | 0.160598 | 0.313895 |
| **T700-12k-60E-T4** | 60E | 14 | 0.172361 | 0.272510 | +0.833217 | +0.048070 | 0.368642 | 1.039664 | 0.870035 |
| **T700-12k-50C-T1** | 50C | 14 | 0.157129 | 0.260546 | -0.744623 | +0.157129 | 0.140862 | 0.950377 | 0.786060 |

---

## 3. Detailed Audit of the 50C-T1 Investigation

### Step-by-Step Row Breakdown for `T700-12k-50C-T1`

| Step | Normal Load (N) | Observed COF | Predicted COF | Residual ($\widehat{y} - y$) | Squared Error | Share of Run SSE |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | **0.0770** | **1.163582** | **1.949642** | **+0.786060** | **0.617890** | **65.02%** |
| 1 | 0.4069 | 0.640258 | 1.061125 | +0.420867 | 0.177129 | 18.64% |
| 2 | 1.7040 | 0.576865 | 0.855197 | +0.278332 | 0.077469 | 8.15% |
| 3 | 3.5134 | 0.600584 | 0.652027 | +0.051443 | 0.002646 | 0.28% |
| 4 | 7.8488 | 0.593543 | 0.605162 | +0.011619 | 0.000135 | 0.01% |
| 5 | 13.7845 | 0.533676 | 0.569426 | +0.035750 | 0.001278 | 0.13% |
| 6 | 19.6432 | 0.533205 | 0.567016 | +0.033811 | 0.001143 | 0.12% |
| 7 | 25.5996 | 0.460764 | 0.488520 | +0.027756 | 0.000770 | 0.08% |
| 8 | 31.4287 | 0.424820 | 0.438876 | +0.014056 | 0.000198 | 0.02% |
| 9 | 39.2483 | 0.406801 | 0.442461 | +0.035660 | 0.001272 | 0.13% |
| 10 | 47.0784 | 0.393724 | 0.465107 | +0.071383 | 0.005096 | 0.54% |
| 11 | 48.0691 | 0.382114 | 0.490091 | +0.107977 | 0.011659 | 1.23% |
| 12 | 48.5645 | 0.375867 | 0.517804 | +0.141937 | 0.020146 | 2.12% |
| 13 | 49.1554 | 0.372534 | 0.555693 | +0.183159 | 0.033547 | 3.53% |
| **Total** | — | — | — | — | **0.950377** | **100.0%** |

### Correlation Audit & Scope Reconciliation
1. **Steps 3 through 9 Filter** (`step >= 3` and `step <= 9`, 7 rows):
   - Mean Absolute Error: **0.030014** (all errors between 0.0116 and 0.0514).
   - Pearson Correlation: $r = \mathbf{0.986736}$ ($r \approx 0.987$).
2. **All 14 Steps Filter** (`step 0` through `step 13`, 14 rows):
   - Pearson Correlation: $r = \mathbf{0.952031}$ ($r \approx 0.952$).
   - *Clarification*: The previous report referred to $r = 0.952$ when discussing steps 3–9; that $0.952$ was in fact the correlation across **all 14 steps** of the sweep, while steps 3–9 specifically achieve an even stronger correlation of $r = 0.987$.

### Plausible Explanation vs. Proven Root Cause
- **Statistical finding**: Step 0 contributes 65.02% of the run's sum of squared errors ($0.6179 / 0.9504$). If Step 0 is omitted, the run's RMSE drops from $0.2605$ to $0.1599$.
- **Scientific distinction**: An observation with high error near zero normal load (~0.077 N) is a **plausible statistical contributor**, not a proven physical root cause. One cannot assert that "measurement noise" alone caused the failure. Physical tribological mechanisms (such as sizing tackiness, static-to-kinetic friction transition, or boundary lubrication regimes at near-zero normal force) could be genuine physical effects in 50C tow. Without multiple independent physical specimens, these mechanisms cannot be differentiated.

---

## 4. Leave-One-Run-Out (LOGO) Sensitivity Audit Across All 10 Runs

Every run was evaluated under a complete leave-one-group-out protocol with pipeline preprocessing re-fitted strictly on the remaining 9 runs:

| Run ID | Tow Type | Rows | MAE | RMSE | $R^2$ | Mean Residual |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `T700-12k-60E-T1` | 60E | 14 | 0.125604 | 0.307471 | +0.810092 | -0.065236 |
| `T700-12k-60E-T2` | 60E | 14 | 0.076147 | 0.114881 | +0.940086 | +0.043368 |
| `T700-12k-60E-T3` | 60E | 14 | 0.142732 | 0.255352 | +0.848970 | -0.067756 |
| `T700-12k-60E-T4` | 60E | 14 | 0.166543 | 0.286742 | +0.815341 | +0.028431 |
| `T700-12k-60E-T5` | 60E | 14 | 0.143189 | 0.202140 | +0.871491 | +0.075973 |
| `T700-12k-50C-T1` | 50C | 14 | 0.172718 | 0.281978 | -1.043451 | +0.172718 |
| `T700-12k-50C-T2` | 50C | 14 | 0.101605 | 0.117013 | +0.909888 | -0.084111 |
| `T700-12k-50C-T3` | 50C | 14 | 0.160502 | 0.243084 | -0.385231 | +0.012209 |
| `T700-12k-50C-T4` | 50C | 14 | 0.121404 | 0.155575 | +0.760331 | +0.088910 |
| `T700-12k-50C-T5` | 50C | 14 | 0.199280 | 0.217853 | +0.708828 | -0.198604 |

### LOGO Tow-Type Summary
- **T700-12k-60E (5 runs)**: Mean MAE = **0.130843**, Mean RMSE = **0.233317**, Mean $R^2$ = **+0.857196**, Mean Residual = **+0.002956**. All 5 sweeps achieve $R^2 \ge 0.810$.
- **T700-12k-50C (5 runs)**: Mean MAE = **0.151102**, Mean RMSE = **0.203100**, Mean $R^2$ = **+0.190073**, Mean Residual = **-0.001776**. Volatile run-to-run behavior: 3 sweeps achieve high $R^2$ ($0.910, 0.760, 0.709$), while sweeps T1 ($-1.043$) and T3 ($-0.385$) drop negative due to vertical baseline shifts.

---

## 5. Artifact & Provenance Consistency Verification

1. **Hash Verification**:
   - `model.joblib`: SHA-256 matches `manifest.json`.
   - `report.json`: SHA-256 matches `manifest.json`.
   - `holdout_predictions.csv`: SHA-256 matches `manifest.json`.
   - `predictions_vs_observations.png`: SHA-256 matches `manifest.json`.
2. **Fresh Model Prediction Alignment**:
   - Loading `model.joblib` and scoring the holdout features directly from the raw Cambridge dataset yields predictions identical to `holdout_predictions.csv` with a maximum discrepancy of $2.22 \times 10^{-16}$ (machine epsilon limit).
3. **Partition Integrity**:
   - The holdout split (seed 417, `GroupShuffleSplit`, 7 training runs / 3 holdout runs) remains strictly preserved. No tuning or model re-selection was performed against the holdout partition.
   - Glass-fibre/epoxy composite targets remain completely untrained and strictly marked **`BLOCKED`**.

---

## 6. Automated Regression Tests Added

Three new automated tests were added to [`tests/test_external_cof_model.py`](file:///c:/Users/devap/Documents/AI-TriboTwin/tests/test_external_cof_model.py):
1. `test_recomputed_metrics_from_predictions_csv_match_report_exactly`:
   - Recomputes MAE, RMSE, and $R^2$ from the unrounded predictions CSV for overall, per-tow, and per-run slices, asserting agreement with `report.json` within $10^{-6}$.
2. `test_rmse_lower_bound_detects_impossible_metrics`:
   - Enforces the mathematical inequality $\mathrm{RMSE} \ge \sqrt{\max(e_i^2) / N}$ across all slices, verifying that $0.2064$ is mathematically rejected and $0.260546$ is verified.
3. `test_manifest_model_predictions_exact_provenance_and_scoring_consistency`:
   - Verifies that fresh scoring of raw inputs with the loaded model matches the predictions CSV within $10^{-12}$.

---

## 7. Automated Test Suite Results

- **Python Suite**: **110 passed**, 0 failed, 1 warning in 13.06s.
- **Frontend Vitest**: **9 passed**, 0 failed in 3.40s.
- **Frontend Typecheck**: `tsc --noEmit` passed with 0 errors.
- **Frontend Linting**: `eslint .` passed with 0 warnings/errors.
- **Frontend Production Build**: `next build` succeeded with all 6 static routes prerendered.

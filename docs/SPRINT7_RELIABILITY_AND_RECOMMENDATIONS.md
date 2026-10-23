# Sprint 7 — Scientific Reliability and Constrained Experiment Recommendations

Sprint 6 established a working prediction interface for the University of Cambridge "Friction of carbon fibre tows" dataset. Sprint 7 audits prediction reliability under domain violations, rigorously evaluates generalization across tow types and independent test runs, demonstrates why calibrated group-aware prediction intervals cannot be defensibly claimed with the existing data, and introduces a strictly bounded candidate experiment recommendation workflow.

---

## 1. Audit of the Extreme Prediction (Normal Load 50,010.1 N -> COF 217.0966)

### Investigation & Root Cause
In Sprint 6, submitting `normal_load_n = 50010.1` returned a predicted coefficient of friction of `217.0966` with an `OUT_OF_DOMAIN` warning badge. Investigation of the pipeline, feature transformations, preprocessing, and model weights revealed the exact mathematical and physical cause:

1. **Model Architecture & Preprocessing**:
   - The selected model is a **Ridge regression** estimator fitted on standardized numerical features and one-hot encoded tow types (`StandardScaler` followed by `Ridge(alpha=1.0)`).
   - The model feature set incorporates both linear normal load (`normal_load_n`) and derived logarithmic load (`log10_normal_load_n`).
   - In the training partition (7 runs, 98 rows), `normal_load_n` has a mean of ~16.92 N, standard deviation of ~15.35 N, and maximum of 49.155 N.
   - The fitted Ridge coefficient for standardized `normal_load_n` is **+0.069908**, for `log10_normal_load_n` is **-0.640778**, and the intercept is **0.566037**.

2. **Unbounded Linear Extrapolation**:
   - An input of 50,010.1 N sits >3,144 standard deviations above the training mean.
   - Standard scaling transforms 50,010.1 N to $z \approx +3144.14$.
   - The linear load term alone contributes:
     $$3144.14 \times 0.069908 \approx +219.80$$
   - In contrast, $\log_{10}(50010.1) \approx 4.699$, which scales to $z \approx 5.10$, contributing $5.10 \times (-0.6408) \approx -3.27$.
   - Combining the linear term (+219.80), log term (-3.27), intercept (0.566), and tow-type offset (-0.031) yields:
     $$\widehat{\text{COF}} = 219.80 - 3.27 + 0.566 - 0.031 = 217.065 \approx 217.1$$
   - Because standard linear models have no bounding mechanism, linear extrapolation beyond the training range scales without limit.

3. **Physical Inconsistency in the Request**:
   - Applying a normal load of 50,010.1 N over the submitted contact area of 150 mm² corresponds to a physical nominal pressure of:
     $$P = \frac{50010.1\text{ N}}{150\text{ mm}^2} \approx 333.4\text{ MPa}$$
   - However, the submitted request supplied `nominal_pressure_mpa = 0.1 MPa`, an internal physical contradiction of over 3,300x.

### Fail-Safe Remedy
A domain warning alone is insufficient because downstream automated consumers or decision-makers could parse the numeric `predicted_coefficient_of_friction` field. 

- **Two Distinct Behaviours**:
  - **In-domain requests**: Return HTTP 200 with the single-point prediction, full model provenance, holdout metrics, and explicit disclaimers.
  - **Out-of-domain requests**: Are rejected before model scoring with HTTP 422 (`ExternalPredictionInputError`), stating explicitly that no prediction is generated and numerical outputs for out-of-domain inputs are not validated for decision-making.
- **No silent clipping**: The model artifact is preserved unchanged without ad-hoc post-prediction clipping or synthetic dampening.
- **Regression test**: `test_reported_extreme_load_extrapolation_is_blocked_before_model_scoring` ensures that `_predict()` is not called, HTTP 422 is returned, and 217 is never presented as actionable.

---

## 2. Model Reliability & Generalization Evaluation

The evaluation preserves the original holdout partition (7 training runs / 3 held-out runs; seed 417; GroupShuffleSplit) to maintain scientific comparability.

### Overall Holdout Performance

| Estimator | Holdout MAE | Holdout RMSE | Holdout $R^2$ | Mean Residual |
| :--- | :--- | :--- | :--- | :--- |
| **Ridge Regression (Selected)** | **0.1340** | **0.2263** | **+0.7826** | **+0.0840** |
| **Mean Baseline** | 0.2737 | 0.4862 | -0.0039 | +0.0303 |

### Sliced Generalization: By Tow Type

| Tow Type | Rows | Selected MAE | Selected RMSE | Selected $R^2$ | Mean Residual | Baseline MAE | Baseline $R^2$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T700-12k-60E** | 28 (2 runs) | **0.1225** | **0.2070** | **+0.8716** | +0.0474 | 0.3401 | -0.0021 |
| **T700-12k-50C** | 14 (1 run) | **0.1571** | **0.2605** | **-0.7446** | **+0.1571** | **0.1410** | -0.0367 |

### Sliced Generalization: By Held-Out Test Run

| Run ID | Tow Type | Rows | Selected MAE | Selected RMSE | Selected $R^2$ | Mean Residual | Baseline MAE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T700-12k-60E-T2** | 60E | 14 | 0.0726 | 0.1071 | +0.9479 | +0.0468 | 0.3118 |
| **T700-12k-60E-T4** | 60E | 14 | 0.1724 | 0.2725 | +0.8332 | +0.0481 | 0.3684 |
| **T700-12k-50C-T1** | 50C | 14 | 0.1571 | 0.2605 | -0.7446 | +0.1571 | 0.1410 |

### Critical Reliability Insights
1. **Severe Tow-Type Asymmetry**: While the Ridge model demonstrates solid predictive performance on `T700-12k-60E` ($R^2 = 0.87$), it performs **worse than the simple mean baseline on `T700-12k-50C`** ($R^2 = -0.74$, MAE 0.157 vs baseline 0.141).
2. **Systematic Over-Prediction Bias**: Across all 3 held-out test runs, the mean residual ($\widehat{y} - y$) is positive (+0.0840 overall, +0.1571 on 50C). The model systematically over-estimates friction under held-out test conditions.
3. **Data Leakage Verification**:
   - Preprocessing (`StandardScaler`, `SimpleImputer`) is fitted strictly on the training partition within each cross-validation fold and on the 7 training runs.
   - Run overlap is verified to be empty: $\text{train\_groups} \cap \text{test\_groups} = \emptyset$.
   - Feature scope excludes friction-derived targets and friction forces.
   - Feature schema bounds are derived from `x_train` only.
4. **Severe Group-Count Limitation**: The dataset contains only 10 labelled runs (5 per tow type) without specimen serial numbers. The held-out evaluation for 50C relies on a **single run** (`T700-12k-50C-T1`), which is statistically insufficient to prove generalization across physical specimens.

---

## 3. Uncertainty Estimation Feasibility

We investigated whether the available run structure supports a defensible prediction interval (e.g., group-conformal prediction):

1. **Non-Exchangeable Observations**:
   - Within each run, the 14 measurement steps represent sequential increasing-load ramp steps on the same tow patch.
   - Observations within a run are autocorrelated; treating rows as independent calibration units violates conformal exchangeability.
2. **Mathematical Group-Conformal Requirement**:
   - For a standard 90% group-conformal prediction interval ($\alpha = 0.10$), the required number of independent calibration groups $n$ must satisfy:
     $$\left\lceil \frac{(n + 1)(1 - \alpha)}{n} \right\rceil \le 1 \implies 0.9(n + 1) \le n \implies n \ge 9$$
   - At least **9 independent calibration runs per tow type** are the mathematical minimum to calibrate a 90% group prediction interval.
   - The entire Cambridge dataset contains only 10 runs total (5 per tow type: 4 train / 1 test for 50C, 3 train / 2 test for 60E).
3. **Conclusion**:
   - Ten runs are **mathematically and experimentally insufficient** for calibrated group-aware prediction intervals.
   - Fabricating heuristic error bands or assuming independent Gaussian residuals would mislead engineers into treating model spread as calibrated scientific confidence.
   - Calibrated intervals remain **unproduced (`status: NOT_CALIBRATED`)** until at least 9 additional independent, specimen-identified calibration runs per tow type are collected.

---

## 4. Constrained Experiment Recommendation Prototype

To enable scientific experiment planning while strictly guarding against unvalidated claims, Sprint 7 implements a constrained recommendation prototype (`POST /api/v1/models/external/recommendations`):

### Prototype Design & Guardrails
- **Strictly In-Domain**: Recommends candidate test conditions solely within the documented training bounds of normal load ($[0.0775, 49.155]$ N) and allowable categorical tow types (`T700-12k-50C`, `T700-12k-60E`).
- **Physical Consistency**: Enforces physical geometry consistency; nominal pressure is computed directly from normal load and training-median contact area ($P = F_N / A$).
- **Actual Saved Model**: Evaluates candidates using the verified, hash-bound Ridge model (`model.joblib`).
- **Target Criteria**: Supports ranking candidate test conditions by `lowest_predicted_cof`, `highest_predicted_cof`, or uniform `load_sweep_grid`.
- **Honest Framing**:
  - Every candidate is explicitly labeled: `"Candidate condition for physical laboratory testing (not an established optimum)"`.
  - COF is identified as a **model estimate, not a measurement** (`is_model_estimate_not_measurement: true`).
  - **No Causal Claim**: Explicitly disclaims causality (`"No causal relationship is inferred. Model associations reflect observational correlations in the 10 Cambridge ramp runs only."`).
  - **No Composite Claim**: Explicitly states `composite_targets_trained: false`.
  - **Reliability Notice**: Prominently warns users about negative $R^2$ on 50C and uncalibrated uncertainty.

---

## 5. Separation and Provenance

- **Cambridge external model**: Isolated in `artifacts/ml/external-cof-cambridge/` with cryptographic SHA-256 manifest verification across `model.joblib`, `report.json`, `holdout_predictions.csv`, and `predictions_vs_observations.png`.
- **Synthetic demonstration**: Isolated in `artifacts/models/demo/` with synthetic-only provenance.
- **Composite targets**: The 4 AI-TriboTwin glass-fibre/epoxy composite targets (`TARGET-COF`, `TARGET-SPECIFIC-WEAR-RATE`, `TARGET-WEAR-VOLUME`, `TARGET-TEMPERATURE`) remain strictly **BLOCKED** (`SCIENTIFIC_READINESS_BLOCKED`). The external model cannot be substituted for composite targets.

---

## 6. Verification Results

All automated test suites and build pipelines were executed against the codebase:

- **Python Tests**: **97 passed** in 12.45s (`.venv\Scripts\pytest.exe`), including 23 prediction and recommendation endpoint tests.
- **Frontend Tests**: **9 passed** in 3.91s (`npm test` via Vitest).
- **Frontend Typecheck**: **0 errors** (`tsc --noEmit`).
- **Frontend Linter**: **0 warnings, 0 errors** (`eslint .`).
- **Frontend Build**: **Production bundle compiled successfully** (`next build`).

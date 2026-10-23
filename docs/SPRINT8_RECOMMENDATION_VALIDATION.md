# Sprint 8 — Recommendation Validation and Generalization Audit

Sprint 7 established the external tow-on-tool prediction endpoint, domain boundary verification, and an initial constrained recommendation workflow. Sprint 8 validates the mathematical and physical behavior of candidate recommendations, audits joint feature consistency, conducts deep sensitivity analysis of model generalization across tow types and individual sweeps, and addresses the distinction between mathematical calibration requirements and scientific validity.

---

## 1. Audit of Candidate Generation & Joint Domain Consistency

### Joint Feature Consistency & Physical Geometry
In physical tribology on the Cambridge tow-on-tool apparatus, observations do not vary independently across coordinate axes:
1. **Contact Geometry & Tool Length**:
   - The Cambridge test rig slides carbon-fibre tow across a flat glass tool with a fixed contact patch length of **23.75 mm**.
   - Analysis of all 140 experimental rows confirms:
     $$\frac{\text{contact\_area\_mm}^2}{\text{contact\_width\_mm}} = 23.75 \pm 0.00\text{ mm}$$
   - Any proposed candidate where contact area deviates from $\text{contact\_width\_mm} \times 23.75\text{ mm}$ by more than 5% relative tolerance represents a physically impossible condition on this test rig.
   - `_combination_issues()` now enforces this geometric constraint alongside the nominal pressure check ($P = F_N / A$). Requests or candidate batches violating this geometry are rejected with HTTP 422 or flagged as non-testable.

2. **Tow-Type Dimensional Asymmetry**:
   - The two tow sizings exhibit fundamentally distinct physical geometry:
     - **T700-12k-50C**: Median contact width is **5.74 mm**, median contact area is **136.2 mm²**.
     - **T700-12k-60E**: Median contact width is **7.39 mm**, median contact area is **175.5 mm²**.
   - Candidate generation previously used pooled marginal medians (~160 mm²), generating unphysical combinations for both tows.
   - `recommend_external_experiments()` now resolves medians from `medians_by_tow_type` in `_feature_schema`, guaranteeing physically coherent geometries for 50C and 60E candidates alike.

3. **Duplicate & Invariant Candidate Detection**:
   - `validate_external_candidates()` now checks the batch for duplicate `candidate_id` entries and duplicate physical condition vectors across candidates.
   - `recommend_external_experiments()` validates that `max_load_n - min_load_n \ge 10^{-4}\text{ N}`, preventing degenerate zero-variance sweeps.

4. **Deterministic Ranking & Tie-Breaking**:
   - Sorting by `lowest_predicted_cof`, `highest_predicted_cof`, and `load_sweep_grid` now includes deterministic secondary tie-breaking by `normal_load_n`.
   - Recommendations are explicitly labeled as:
     `"Candidate condition for physical laboratory testing (not an established optimum)"`.

---

## 2. Model Evaluation & Generalization Audit

The original holdout split (seed 417, 7 training runs / 3 held-out runs; `GroupShuffleSplit`) is strictly preserved for comparability.

### Comparison Against Baselines on the Held-Out Set (42 rows)

| Estimator / Baseline | Description | MAE | RMSE | $R^2$ | Mean Residual |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Ridge Regression (Selected)** | Standardized features + $L_2$ penalty | **0.1340** | **0.2263** | **+0.7826** | **+0.0840** |
| **Pooled Mean Baseline** | Predicts overall training mean COF | 0.2737 | 0.4862 | -0.0039 | +0.0303 |
| **Tow-Stratified Baseline** | Predicts tow-specific training mean COF | 0.2738 | 0.4862 | -0.0039 | +0.0305 |

The selected Ridge model outperforms both the pooled mean baseline and the tow-stratified baseline by **51% lower MAE** and **53% lower RMSE**.

### Sliced Generalization by Tow Type on the Holdout

| Tow Type | Runs in Holdout | Rows | Ridge MAE | Ridge RMSE | Ridge $R^2$ | Mean Residual | Stratified Baseline MAE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T700-12k-60E** | 2 (`T2`, `T4`) | 28 | **0.1225** | **0.2070** | **+0.8716** | +0.0474 | 0.3404 |
| **T700-12k-50C** | 1 (`T1`) | 14 | **0.1571** | **0.2605** | **-0.7446** | **+0.1571** | **0.1409** |

### Per-Run Holdout Results

| Run ID | Tow Type | Rows | Ridge MAE | Ridge RMSE | Ridge $R^2$ | Mean Residual | Stratified Baseline MAE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T700-12k-60E-T2** | 60E | 14 | 0.0726 | 0.1071 | +0.9479 | +0.0468 | 0.3121 |
| **T700-12k-60E-T4** | 60E | 14 | 0.1724 | 0.2725 | +0.8332 | +0.0481 | 0.3686 |
| **T700-12k-50C-T1** | 50C | 14 | 0.1571 | 0.2605 | -0.7446 | +0.1571 | 0.1409 |

---

## 3. Investigation of the 50C Failure

Why did `T700-12k-50C` yield negative $R^2$ (-0.7446) on the holdout?

1. **Plausible Statistical Contributor at Low-Load Ramp Step 0**:
   - In Cambridge sweep `T700-12k-50C-T1`, Step 0 applied a normal load of only **0.077 N**.
   - At this near-zero load, the observed COF was **1.1636**.
   - In contrast, the training 50C runs (T2, T4, T5) recorded Step 0 COF values between **1.63 and 2.02**.
   - The Ridge model, learning from the training runs, predicted **1.9496** on T1 Step 0.
   - This single observation created a residual of $+0.7861$, contributing a squared error of $(1.9496 - 1.1636)^2 = 0.6179$.
   - This single point accounts for **65.0% of the entire run's sum of squared errors** (0.6179 out of 0.9504).
   - A single squared error of 0.6179 establishes a mathematical lower bound on the run's RMSE of:
     $$\mathrm{RMSE} \ge \sqrt{\frac{0.6179}{14}} \approx 0.2101$$
   - The actual run RMSE of **0.2605** (SSE = 0.9504 across all 14 steps) is fully mathematically consistent with this lower bound ($0.2605 \ge 0.2101$). The previously reported figure of 0.2064 was a typographical transcription error in the Sprint 8 markdown table.

2. **Steps 3–9 High Alignment and Overall Functional Correlation**:
   - For ramp steps 3 through 9 (normal loads 3.5 N to 39.2 N), the Ridge model tracks observed COF with an MAE of **0.0300** (errors between 0.011 and 0.051), exhibiting a correlation of $r = \mathbf{0.9867}$.
   - Across **all 14 steps** of the run (steps 0 through 13), the Pearson correlation between predictions and observations is $r = \mathbf{0.9520}$.
   - The negative $R^2$ is driven by a vertical baseline offset and Step 0 ratio noise, not a failure to capture the functional load-friction dependence.

3. **Plausible Explanation vs. Established Root Cause**:
   - While Step 0 statistically dominates the squared error, one unusual observation alone does not prove that measurement noise caused the poor score.
   - Physical factors (such as static friction transitions, sizing tack, or boundary layer behavior at near-zero normal force) cannot be ruled out without independent specimen replication.

4. **Sample Size Vulnerability of a 1-Run Holdout**:
   - Because the holdout partition contains only **one run** of 50C (14 rows), the overall 50C score is completely hostage to the ratio noise and baseline offset of that single test sweep.

---

## 4. Leave-One-Run-Out (LOGO) Sensitivity Analysis

To assess generalization sensitivity without altering the fixed holdout evaluation, we performed Leave-One-Run-Out cross-validation across all 10 Cambridge sweeps.

### Summary by Tow Type Across All 10 Runs

| Tow Type | Total Runs | Mean MAE | Mean RMSE | Mean $R^2$ | Mean Residual | Generalization Profile |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T700-12k-60E** | 5 | **0.1308** | **0.2333** | **+0.8572** | +0.0030 | **Consistent** ($R^2 > 0.81$ on every run) |
| **T700-12k-50C** | 5 | **0.1511** | **0.2031** | **+0.1901** | -0.0018 | **Volatile** (3 runs high $R^2$, 2 runs negative) |

### Complete Run-by-Run Breakdown Under LOGO

| Run ID | Tow Type | Rows | MAE | RMSE | $R^2$ | Mean Residual |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `T700-12k-60E-T1` | 60E | 14 | 0.1256 | 0.3075 | +0.8101 | -0.0652 |
| `T700-12k-60E-T2` | 60E | 14 | 0.0761 | 0.1149 | +0.9401 | +0.0434 |
| `T700-12k-60E-T3` | 60E | 14 | 0.1427 | 0.2554 | +0.8490 | -0.0678 |
| `T700-12k-60E-T4` | 60E | 14 | 0.1665 | 0.2867 | +0.8153 | +0.0284 |
| `T700-12k-60E-T5` | 60E | 14 | 0.1432 | 0.2021 | +0.8715 | +0.0760 |
| `T700-12k-50C-T1` | 50C | 14 | 0.1727 | 0.2820 | -1.0435 | +0.1727 |
| `T700-12k-50C-T2` | 50C | 14 | 0.1016 | 0.1170 | +0.9099 | -0.0841 |
| `T700-12k-50C-T3` | 50C | 14 | 0.1605 | 0.2431 | -0.3852 | +0.0122 |
| `T700-12k-50C-T4` | 50C | 14 | 0.1214 | 0.1556 | +0.7603 | +0.0889 |
| `T700-12k-50C-T5` | 50C | 14 | 0.1993 | 0.2179 | +0.7088 | -0.1986 |

**Key Takeaways**:
- **60E demonstrates robust, repeatable generalization**: Every single 60E run achieves $R^2 \ge 0.81$ when held out entirely from training.
- **50C displays severe run-to-run baseline shifts**: While 3 of the 5 runs achieve $R^2 \ge 0.70$, runs T1 and T3 exhibit vertical offset shifts that cause negative scores under zero-intercept/mean-comparison metrics.
- Candidate recommendations and predictions for 50C must carry prominent reliability caveats.


---

## 5. Review of Uncertainty Claims: Mathematical Floor vs. Scientific Validity

Sprint 7 noted that at least 9 calibration runs are mathematically required for a 90% group-conformal interval. Sprint 8 sharpens this distinction:

1. **The Mathematical Floor**:
   - For standard split-conformal prediction at nominal 90% confidence ($\alpha = 0.10$), coverage requires:
     $$\left\lceil \frac{(n + 1)(1 - \alpha)}{n} \right\rceil \le 1 \implies n \ge 9$$
   - Having fewer than 9 calibration units means the 90th percentile of nonconformity scores cannot be mathematically formed without extrapolation.

2. **The Scientific Validity Distinction**:
   - Achieving $n \ge 9$ runs is **merely a necessary mathematical condition**, not a guarantee of scientific validity.
   - In physical tribology, valid prediction intervals require:
     - **Verified Specimen Independence**: Confirmation that test sweeps used distinct physical tow cuts rather than repeated sweeps on the same patch.
     - **Exchangeability**: Verification that test environment (temperature, relative humidity) and tool condition are identically distributed.
     - **Tow-Stratified Dispersion**: Accounting for the large variance difference between 50C and 60E.
     - **Empirical Coverage Validation**: Verifying that 90% intervals cover at least 90% of observations on an unseen test cohort.
   - Therefore, AI-TriboTwin **refuses to fabricate heuristic error bars** or claim that acquiring 9 runs alone would validate prediction intervals.

---

## 6. Verification & Automated Test Summary

All automated test suites pass cleanly across both backend and frontend:

- **Python Test Suite**: **107 passed** (0 failed, 1 warning in 12.70s).
- **Frontend Vitest Suite**: **9 passed** (2 test files).
- **Frontend Typecheck**: `tsc --noEmit` passed with 0 errors.
- **Frontend Linting**: `eslint .` passed with 0 warnings/errors.
- **Frontend Production Build**: `next build` succeeded with all 6 static routes prerendered.

---

## 7. Remaining Scientific Limitations

1. **Specimen Independence Remains Unverified**: The Cambridge workbook numbers sweeps as Test 1 through Test 5 without recording specimen or spool serial numbers. Whether sweeps represent independent specimens or repeated testing remains unknown.
2. **Glass-Fibre/Epoxy Composite Data Remains Blocked**: All 4 original composite targets remain in status `BLOCKED`. The Cambridge model predicts carbon-fibre tow-on-tool friction only, preserving strict scientific isolation.

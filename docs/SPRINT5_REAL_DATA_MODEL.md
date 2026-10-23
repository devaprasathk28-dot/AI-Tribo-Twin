# Sprint 5 — First model trained on real experimental data

Status: **executed**. A regression model for the tow-on-tool coefficient of
friction has been trained and evaluated on the University of Cambridge
carbon-fibre-tow friction dataset, with group-aware validation and a
hash-validated artifact bundle. The AI-TriboTwin composite targets remain
blocked and are unaffected.

## 1. Datasets inspected

### University of Cambridge — Friction of carbon fibre tows (item CAM-1671)

Repository item: <https://www.repository.cam.ac.uk/items/3039d85c-0261-46b9-b249-fec061329100>

Three workbooks are preserved under `data/external/cambridge-cam-1671/raw/`:

| Workbook | SHA-256 | Content found |
| --- | --- | --- |
| `TowTool_ContactLengthAndFrictionForce.xlsx` | `b9c9af71be796d25d8d6deac6e303943dc6ad45a69909eb3c7f7a06126bc4763` | Tow-on-tool load-ramp measurements for two tow sizings, including a measured `Coefficient of Friction` column |
| `TowTool_ContactLength.xlsx` | (unchanged, not used) | Tow-on-tool contact-length only (no friction force) |
| `TowTow_FrictionTests.xlsx` | (unchanged, not used) | Tow-tow parallel and perpendicular friction tests |

`TowTool_ContactLengthAndFrictionForce.xlsx` `Sheet1` holds two tow-type
blocks (`T700-12k-60E`, `T700-12k-50C`), each with five `Test 1..5` blocks.
Every test block is a 14-step monotonically increasing normal-load ramp
(0.0775 N to ~49 N). The workbook's `COF`, `FrictionForce`, `ContactLength`
and `T1..T5-FrictionForce` sheets are chart-only (`Chartsheet`), so the
per-step tables in `Sheet1` are the machine-readable source.

The tow-tow workbook was inspected but not used: its parallel and
perpendicular configurations are different contact protocols, and mixing them
solely to raise the observation count is not scientifically defensible. It is
recorded here as available future data.

### Zenodo record 14609650 — re-inspection

The preserved archives
`data/external/zenodo-14609650/raw/Temperature-Measurements.7z` and
`Inter-Tow-Angle-Measurements.7z` were re-examined.

- Both carry a valid 7z signature (`377abcaf271c`).
- Their 7z headers are compressed, so archive member names and any embedded
  identifiers cannot be recovered by a raw scan (verified: zero recoverable
  file-like names and zero UUID-like tokens).
- No 7z extractor is available in this environment (no `7z`/`7za` on `PATH`,
  no `py7zr`, and the offline package install failed), so the internal
  workbooks could not be re-opened here.

Carried forward from Sprint 4 (which did open `Analyse_Temperature.xlsm` and
the 15 per-test archives): the analysis workbook's summary response rows
(`Reibwert`) are not linked to individual per-test archive UUIDs in any
machine-readable observation table, and only four test dates exist. This
remains the blocker. **Exact remaining requirement:** an authoritative,
machine-readable mapping from every workbook summary row to its per-test
archive run identifier, plus the response-calculation definition and
confirmation of the independent test/replicate structure.

## 2. Modelling route selected

The Cambridge tow-on-tool workbook was selected because it is a single,
clearly scoped protocol with an explicit measured response and leakage-free
predictors.

- **Material domain:** carbon-fibre tow (T700 12k, 60E and 50C sizing)
  sliding on a glass tool. This is **not** AI-TriboTwin's glass-fibre/epoxy
  composite system.
- **Target:** `coefficient_of_friction` (dimensionless) — the workbook's
  `Coefficient of Friction` column, defined as the friction force per contact
  divided by the total normal load.
- **Independent unit (group):** one `Test N` load ramp. There are **10** test
  runs (2 tow types x 5 tests), giving 140 observations.
- **Features (all normal-side / applied-condition, no friction-force input):**
  `normal_load_n`, `log10_normal_load_n`, `nominal_pressure_mpa`,
  `contact_width_mm`, `contact_area_mm2`, `contact_length_scanned_mm`,
  `contact_half_width_a_mm`, `percent_contact_length`, `tow_type`.
- **Leakage control:** the friction-force columns
  (`friction_force_n`, `friction_force_zeroed_n`,
  `friction_force_per_contact_n`, `friction_force_over_area_mpa`) and the
  target itself are explicitly excluded from the feature set, so the
  coefficient of friction is never reconstructed from its own inputs.

## 3. Validation design

1. Whole test runs are held out first (`GroupShuffleSplit`, 30%), so no ramp
   contributes to both training and evaluation.
2. Candidate models (`mean_baseline`, `ridge_regression`,
   `hist_gradient_boosting`) are compared with 5-fold group cross-validation
   (`GroupKFold`) on the training runs only.
3. The candidate with the lowest group-CV MAE is refit on the training runs
   and evaluated once on the held-out runs.
4. A group-leakage assertion guards the split.

Both the target and the prediction are on the same held-out groups; the mean
baseline is evaluated on the identical held-out rows for an honest comparison.

## 4. Results

Seed `417`. 98 training rows (7 runs), 42 held-out rows (3 runs:
`T700-12k-50C-T1`, `T700-12k-60E-T2`, `T700-12k-60E-T4`).

Training-fold group CV (5 folds):

| Candidate | CV MAE mean ± SD | CV RMSE mean | CV R² mean |
| --- | --- | --- | --- |
| mean_baseline | 0.2694 ± 0.0742 | 0.4812 | -0.0137 |
| **ridge_regression** | **0.1568 ± 0.0403** | **0.2390** | **0.6944** |
| hist_gradient_boosting | 0.1818 ± 0.0553 | 0.3582 | 0.3866 |

Selected model: **ridge_regression** (lowest group-CV MAE).

Held-out evaluation:

| Metric | Selected model | Mean baseline |
| --- | --- | --- |
| MAE | **0.1340** | 0.2737 |
| RMSE | **0.2263** | 0.4862 |
| R² | **0.7826** | -0.0039 |

The model roughly halves the mean-baseline MAE on unseen test runs. This is a
genuine external-data result and is **not** an estimate of accuracy on
AI-TriboTwin's composite experiments.
## 5. Artifacts, provenance and hashes

- Processed dataset: `data/external/cambridge-cam-1671/processed/towtool_cof_measurements.csv`
  (SHA-256 `61ee1ec23b913272cf593939ae729208db1a7c367a926c08d900d1177bb6b91f`).
- Provenance sidecar: `data/external/cambridge-cam-1671/processed/towtool_cof_provenance.json`.
- Model bundle: `artifacts/ml/external-cof-cambridge/` containing
  `model.joblib`, `holdout_predictions.csv`, `predictions_vs_observations.png`,
  `report.json`, and `manifest.json`. `manifest.json` records the SHA-256 of
  each artifact, and `verify_external_artifact_bundle` recomputes the SHAs and
  re-derives the holdout metrics from the saved predictions before the report
  is served.
- The original raw composite CSV
  `data/raw/tribological_experiments_raw.csv` was verified before and after
  this work: SHA-256
  `bc4b438bfcb472bdb92d653953b23acd3ff20dbaf3e0220704aa0a16bddedd1d`
  (unchanged).

## 6. Application integration

- API `GET /api/v1/models/status` now returns an `external_model` block
  (`status`, `plot_available`, `report`) alongside the existing synthetic demo
  and composite target gates. `experimental_model_trained` remains `false`, so
  external performance is never presented as composite accuracy.
- API `GET /api/v1/models/external/predictions.png` serves the external
  observed-vs-predicted plot (404 with a clear message when absent).
- Frontend `frontend/src/app/models/page.tsx` renders a dedicated
  "External real-data model · tow-on-tool friction" section showing the
  material domain, source, hashes, selected model, held-out metrics, the
  candidate comparison, the selected-vs-baseline table, caveats, and the plot.

## 7. Files changed

Added: `src/data/cambridge.py`, `src/models/external_cof.py`,
`scripts/build_cambridge_dataset.py`, `tests/test_cambridge_dataset.py`,
`tests/test_external_cof_model.py`, `docs/SPRINT5_REAL_DATA_MODEL.md`, and the
generated `data/external/cambridge-cam-1671/processed/*` and
`artifacts/ml/external-cof-cambridge/*`.

Changed: `backend/app/core/config.py` (`EXTERNAL_MODEL_DIR`),
`backend/app/services/model_status.py`, `backend/app/api/routes.py`,
`frontend/src/lib/api.ts`, `frontend/src/app/models/page.tsx`,
`backend/tests/test_api.py`.

## 8. Tests executed

- `python -m pytest tests -q` — 45 passed.
- `python -m pytest backend -q` — 27 passed.
- `npm run typecheck` (frontend) — clean.
- `npm run lint` (frontend) — clean.
- `npm test` (frontend, vitest) — 2 passed.
- `npm run build` (frontend) — compiled successfully, types valid, 8/8 pages.

## 9. Unresolved items

- Zenodo mapping: unresolved. The archives cannot be extracted in this
  environment, and the Sprint-4 blocker (no workbook-to-run mapping) stands.
  Exact requirement stated in §1.
- Tow-run independence: the workbook labels five sweeps per tow type but
  exposes no specimen serial number; independence is taken from the labels.
- Small group count: ten runs is the minimum for group-aware validation and
  the three held-out runs are not balanced across tow types.
- Near-zero-load rows are retained and reported rather than dropped.
- Tow-tow data inspected but not modelled, to avoid mixing protocols.

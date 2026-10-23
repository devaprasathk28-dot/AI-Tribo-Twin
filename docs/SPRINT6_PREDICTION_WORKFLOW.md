# Sprint 6 — External tow-on-tool prediction workflow

Sprint 5 trained and evaluated a model on the University of Cambridge
"Friction of carbon fibre tows" dataset and surfaced its report on the **ML
status** page. Sprint 6 turns that verified model into a working prediction
workflow in the application: a typed serving endpoint plus a client form,
both scoped strictly to the external carbon-fibre-tow system.

## What Sprint 6 adds

| Layer | File | Purpose |
| --- | --- | --- |
| Model report | `src/models/external_cof.py` | Adds a `feature_schema` block (unit, role, and training range per input) to `report.json`. |
| API schemas | `backend/app/schemas/predictions.py` | Strict request/response contracts for a single prediction. |
| API service | `backend/app/services/external_prediction.py` | Verifies the bundle, validates ranges, derives features, predicts, assembles the payload. |
| API route | `backend/app/api/routes.py` | `POST /api/v1/models/external/predict`. |
| Frontend client | `frontend/src/lib/api.ts` | Feature-schema and prediction types plus `api.predictCof()`. |
| Frontend UI | `frontend/src/components/cof-prediction-form.tsx`, `cof-prediction-result.tsx` | Prediction form and result panel, wired into `frontend/src/app/models/page.tsx`. |
| Tests | `backend/tests/test_predictions.py`, `frontend/src/components/cof-prediction-form.test.tsx` | Endpoint and component coverage. |

## Feature schema

`report.json` now carries `feature_schema`, derived from the training
observations rather than hardcoded:

- Each numeric input records its physical `unit`, a `description`, and the
  observed `min`, `max`, `mean`, and `median`.
- `tow_type` records its `allowed_values` (`T700-12k-50C`, `T700-12k-60E`).
- `log10_normal_load_n` is marked `dtype: "derived"` with its source column
  and geometric transformation; it is **not** a request field.
- `request_feature_columns` lists exactly what a client must supply.

Because the schema is written into the hash-bound report, the range and
categorical checks the API performs always match the shipped model.

## Request and response

`POST /api/v1/models/external/predict` accepts one observation:

```json
{
  "normal_load_n": 10.0,
  "nominal_pressure_mpa": 0.1,
  "contact_width_mm": 6.5,
  "contact_area_mm2": 150.0,
  "contact_length_scanned_mm": 1400.0,
  "contact_half_width_a_mm": 0.00003,
  "percent_contact_length": 18.0,
  "tow_type": "T700-12k-60E"
}
```

It returns the point prediction plus its honest framing: the model id and
source kind, the target name and unit, the `domain_status`
(`IN_DOMAIN` / `OUT_OF_DOMAIN`), any out-of-domain flags, the held-out and
baseline metrics, the full provenance block, the external-domain limitation,
and `composite_targets_trained: false`.

## Validation and fail-safe behaviour

- **Strict input.** The request model uses `ConfigDict(extra="forbid",
  strict=True)`: unknown fields are rejected, and numeric strings ("18") are
  not coerced to numbers.
- **Finite and positive.** Every numeric field is checked to be finite and
  greater than zero; `NaN`, `Infinity`, `-Infinity`, zero, and negatives are
  rejected with `422`.
- **Supported categorical.** A `tow_type` outside the trained values is
  rejected with `422`, since the model has no basis for it.
- **Out-of-domain is flagged, not hidden.** A numeric value outside the
  recorded training range is still scored, and every offending feature is
  returned in `out_of_domain_features` with its value, range, and direction.
- **Fail safe.** The workflow loads only the provenance-verified external
  bundle. If the manifest is absent or any artifact fails its SHA-256 check,
  the endpoint returns `503` rather than a prediction.
- **No fabricated uncertainty.** The response states that the value is a
  single-point output with no prediction interval and no feature-importance
  attribution, and never implies that a composite target is trained.

## Frontend

The **ML status** page renders the prediction form inside the external-model
section when the report contains a feature schema. Each input is labelled with
its unit and the recorded training range, defaults to the training median, and
the derived `log10` load is shown as computed automatically. The result panel
shows the predicted coefficient of friction, an in/out-of-domain badge,
per-feature out-of-domain warnings, the held-out metrics against the mean
baseline, the provenance (source, workbook, hashes), the external-domain
limitation, and an explicit "composite targets trained: no" line.

## Verification

- `pytest backend/tests` — 42 passed, including 15 new prediction tests
  (valid prediction, missing/malformed/NaN/inf/zero inputs, out-of-domain,
  unknown categorical, missing and tampered artifacts, domain labelling, and
  composite targets still blocked).
- `pytest tests` — 45 passed.
- `npm test` — 7 passed, including 5 new prediction-form tests.
- `npm run typecheck`, `npm run lint`, `npm run build` — clean.
- Live end-to-end: the API and **ML status** page were run together; an
  in-domain request returned `0.4123` (`IN_DOMAIN`) and an out-of-range normal
  load returned `217.0966` with `OUT OF DOMAIN` and the flag
  `normal_load_n=50010.1 is outside the training range [0.077499, 49.155] N`.

## Non-goals and limits

The endpoint predicts the coefficient of friction for the external
carbon-fibre-tow-on-glass system only. It is not a composite-material model,
it does not serve the blocked composite targets, and it produces no uncertainty
estimate or explanation. The synthetic demo model is never loaded by this path.

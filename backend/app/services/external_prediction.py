"""Serve a single external tow-on-tool COF prediction from the verified bundle.

The workflow loads ONLY the provenance-verified external artifact bundle, checks
the submitted observation against the recorded training ranges, derives the
log10-load feature server-side, and returns the predicted coefficient of
friction with the external model's provenance, metrics, and domain limits.

It never loads the synthetic demo model and it never reports a composite
target as trained.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.schemas.predictions import (
    CofCandidateValidationRequest,
    CofCandidateValidationResponse,
    CofCandidateValidationResult,
    CofPredictionRequest,
    CofPredictionResponse,
    CofRecommendationRequest,
    CofRecommendationResponse,
    CofRecommendedCandidate,
    OutOfDomainFeature,
    PredictionMetrics,
    PredictionProvenance,
)
from app.services.model_status import EXTERNAL_ARTIFACT_DIR
from src.data.cambridge import MODEL_FEATURE_COLUMNS
from src.models.external_cof import load_external_model, verify_external_artifact_bundle

PREDICTION_NOTE = (
    "Single-point model estimate for the external tow-on-tool system, not a "
    "measurement. It has no prediction interval or feature-importance "
    "attribution. Evaluation used only 10 labelled runs, with no specimen serial "
    "numbers; it is not validated for engineering decisions."
)


class ExternalPredictionError(RuntimeError):
    """Base class for external prediction failures."""


class ExternalModelUnavailable(ExternalPredictionError):
    """The verified external bundle is missing or failed verification (HTTP 503)."""


class ExternalPredictionInputError(ExternalPredictionError):
    """The observation cannot be scored by this model (HTTP 422)."""


@dataclass(frozen=True)
class PredictionContext:
    report: dict[str, Any]
    model: Any
    schema: dict[str, Any]


def _require(report: dict[str, Any], key: str, expected: type) -> Any:
    value = report.get(key)
    if not isinstance(value, expected):
        raise ExternalModelUnavailable(f"External model report is missing a valid {key}.")
    return value


def _feature_schema(report: dict[str, Any]) -> dict[str, Any]:
    schema = report.get("feature_schema")
    if not isinstance(schema, dict) or not isinstance(schema.get("features"), list):
        raise ExternalModelUnavailable("External model bundle has no usable feature schema.")
    for feature in schema["features"]:
        if feature.get("name") not in MODEL_FEATURE_COLUMNS:
            raise ExternalModelUnavailable("External model feature schema names an unknown feature.")
    return schema


def load_prediction_context(artifact_dir: Path | None = None) -> PredictionContext:
    """Verify the external bundle, then load the model and its feature schema."""
    directory = artifact_dir or EXTERNAL_ARTIFACT_DIR
    try:
        report = verify_external_artifact_bundle(directory)
        schema = _feature_schema(report)
        model = load_external_model(directory)
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        raise ExternalModelUnavailable(
            "The external model bundle failed provenance verification."
        ) from error
    return PredictionContext(report=report, model=model, schema=schema)


def _feature_row(request: CofPredictionRequest) -> dict[str, Any]:
    """Map the request to the model's inputs, deriving the log10 load server-side."""
    return {
        "normal_load_n": request.normal_load_n,
        "log10_normal_load_n": math.log10(request.normal_load_n),
        "nominal_pressure_mpa": request.nominal_pressure_mpa,
        "contact_width_mm": request.contact_width_mm,
        "contact_area_mm2": request.contact_area_mm2,
        "contact_length_scanned_mm": request.contact_length_scanned_mm,
        "contact_half_width_a_mm": request.contact_half_width_a_mm,
        "percent_contact_length": request.percent_contact_length,
        "tow_type": request.tow_type,
    }


def _validate_categorical(row: dict[str, Any], schema: dict[str, Any]) -> None:
    for feature in schema["features"]:
        if feature.get("dtype") != "categorical":
            continue
        allowed = feature.get("allowed_values")
        if not isinstance(allowed, list) or not allowed:
            raise ExternalModelUnavailable("External model schema is missing categorical values.")
        value = row.get(feature["name"])
        if value not in allowed:
            raise ExternalPredictionInputError(
                f"{feature['name']}={value!r} is not supported; expected one of {sorted(allowed)}."
            )


def _out_of_domain(row: dict[str, Any], schema: dict[str, Any]) -> list[OutOfDomainFeature]:
    flags: list[OutOfDomainFeature] = []
    for feature in schema["features"]:
        if feature.get("dtype") != "numeric":
            continue
        name = feature["name"]
        value = float(row[name])
        low = float(feature["min"])
        high = float(feature["max"])
        if value < low or value > high:
            unit = str(feature.get("unit", ""))
            flags.append(
                OutOfDomainFeature(
                    feature=name,
                    unit=unit,
                    value=value,
                    training_min=low,
                    training_max=high,
                    direction="below_min" if value < low else "above_max",
                    message=(
                        f"{name}={value:g} is outside the training range "
                        f"[{low:g}, {high:g}] {unit}."
                    ),
                )
            )
    return flags


PRESSURE_RELATIVE_TOLERANCE = 0.05
TOOL_LENGTH_MM = 23.75


def _combination_issues(row: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    expected_pressure = float(row["normal_load_n"]) / float(row["contact_area_mm2"])
    reported_pressure = float(row["nominal_pressure_mpa"])
    if not math.isclose(
        reported_pressure,
        expected_pressure,
        rel_tol=PRESSURE_RELATIVE_TOLERANCE,
    ):
        issues.append(
            "nominal_pressure_mpa must agree with normal_load_n / contact_area_mm2 "
            f"within {PRESSURE_RELATIVE_TOLERANCE:.0%}; expected approximately "
            f"{expected_pressure:g} MPa."
        )

    expected_area = float(row["contact_width_mm"]) * TOOL_LENGTH_MM
    reported_area = float(row["contact_area_mm2"])
    if not math.isclose(
        reported_area,
        expected_area,
        rel_tol=PRESSURE_RELATIVE_TOLERANCE,
    ):
        issues.append(
            f"contact_area_mm2 must agree with contact_width_mm * {TOOL_LENGTH_MM:g} mm "
            f"(tool contact length) within {PRESSURE_RELATIVE_TOLERANCE:.0%}; expected approximately "
            f"{expected_area:g} mm²."
        )
    return issues


def _predict(context: PredictionContext, frame: pd.DataFrame) -> float:
    raw = context.model.predict(frame)
    value = float(np.asarray(raw, dtype=float).reshape(-1)[0])
    if not math.isfinite(value):
        raise ExternalModelUnavailable("The external model produced a non-finite prediction.")
    return value


def validate_external_candidates(
    request: CofCandidateValidationRequest, *, artifact_dir: Path | None = None
) -> CofCandidateValidationResponse:
    """Check candidate conditions against the saved model domain without scoring them."""
    context = load_prediction_context(artifact_dir)
    results: list[CofCandidateValidationResult] = []
    seen_candidate_ids: set[str] = set()
    seen_conditions: dict[tuple[Any, ...], str] = {}

    for candidate in request.candidates:
        row = _feature_row(candidate.conditions)
        issues = _combination_issues(row)

        if candidate.candidate_id in seen_candidate_ids:
            issues.append(
                f"Duplicate candidate_id {candidate.candidate_id!r} detected in submission batch."
            )
        else:
            seen_candidate_ids.add(candidate.candidate_id)

        condition_signature = (
            str(candidate.conditions.tow_type),
            round(float(candidate.conditions.normal_load_n), 4),
            round(float(candidate.conditions.nominal_pressure_mpa), 4),
            round(float(candidate.conditions.contact_width_mm), 4),
            round(float(candidate.conditions.contact_area_mm2), 4),
            round(float(candidate.conditions.contact_length_scanned_mm), 2),
            round(float(candidate.conditions.contact_half_width_a_mm), 6),
            round(float(candidate.conditions.percent_contact_length), 2),
        )
        if condition_signature in seen_conditions:
            issues.append(
                f"Candidate condition is a duplicate of candidate {seen_conditions[condition_signature]!r}."
            )
        else:
            seen_conditions[condition_signature] = candidate.candidate_id

        try:
            _validate_categorical(row, context.schema)
        except ExternalPredictionInputError as error:
            issues.append(str(error))
        flags = _out_of_domain(row, context.schema)
        results.append(
            CofCandidateValidationResult(
                candidate_id=candidate.candidate_id,
                accepted_for_physical_testing=not issues and not flags,
                out_of_domain_features=flags,
                issues=issues,
            )
        )
    return CofCandidateValidationResponse(
        model_id=str(context.report["model_id"]),
        source_kind="external",
        interpretation=(
            "Accepted entries are only within the recorded marginal training ranges "
            "and pass the nominal-pressure and contact-geometry consistency checks. They are candidates for "
            "physical testing, not ranked recommendations, model estimates, or proven "
            "optima. Rejection or acceptance does not establish scientific validity."
        ),
        results=results,
    )


def _build_response(
    report: dict[str, Any], prediction: float, flags: list[OutOfDomainFeature]
) -> CofPredictionResponse:
    holdout = report.get("holdout_metrics")
    baseline = report.get("baseline_metrics")
    stratified_baseline = report.get("stratified_baseline_metrics")
    if not isinstance(holdout, dict) or not isinstance(baseline, dict):
        raise ExternalModelUnavailable("External model report is missing evaluation metrics.")
    provenance = PredictionProvenance(
        model_id=_require(report, "model_id", str),
        source_kind="external",
        source_name=_require(report, "source_name", str),
        source_url=_require(report, "source_url", str),
        source_workbook=_require(report, "source_workbook", str),
        source_workbook_sha256=str(report.get("source_workbook_sha256") or ""),
        processed_table=_require(report, "processed_table", str),
        processed_table_sha256=str(report.get("processed_table_sha256") or ""),
        dataset_sha256=_require(report, "dataset_sha256", str),
        measurement_protocol=_require(report, "measurement_protocol", str),
        material_domain=_require(report, "material_domain", str),
        observation_count=_require(report, "observation_count", int),
        training_rows=_require(report, "training_rows", int),
        holdout_rows=_require(report, "holdout_rows", int),
        training_groups=_require(report, "training_groups", int),
        holdout_groups=_require(report, "holdout_groups", int),
        selected_model=_require(report, "selected_model", str),
        seed=_require(report, "seed", int),
        range_basis=str(report.get("feature_schema", {}).get("range_basis", "")),
    )
    metrics = PredictionMetrics(
        mae=float(holdout["mae"]),
        rmse=float(holdout["rmse"]),
        r2=float(holdout["r2"]),
        holdout_rows=_require(report, "holdout_rows", int),
        selection_basis=str(report.get("selection_basis", "")),
        baseline_mae=float(baseline["mae"]),
        baseline_rmse=float(baseline["rmse"]),
        baseline_r2=float(baseline["r2"]),
        stratified_baseline_mae=(
            float(stratified_baseline["mae"])
            if isinstance(stratified_baseline, dict) and "mae" in stratified_baseline
            else None
        ),
        stratified_baseline_rmse=(
            float(stratified_baseline["rmse"])
            if isinstance(stratified_baseline, dict) and "rmse" in stratified_baseline
            else None
        ),
        stratified_baseline_r2=(
            float(stratified_baseline["r2"])
            if isinstance(stratified_baseline, dict) and "r2" in stratified_baseline
            else None
        ),
    )
    return CofPredictionResponse(
        model_id=provenance.model_id,
        source_kind="external",
        predicted_coefficient_of_friction=prediction,
        domain_status="OUT_OF_DOMAIN" if flags else "IN_DOMAIN",
        out_of_domain_features=flags,
        interpretation=_require(report, "interpretation", str),
        metrics=metrics,
        provenance=provenance,
        note=PREDICTION_NOTE,
    )



def predict_external_cof(
    request: CofPredictionRequest, *, artifact_dir: Path | None = None
) -> CofPredictionResponse:
    """Score one observation with the verified external tow-on-tool model."""
    context = load_prediction_context(artifact_dir)
    row = _feature_row(request)
    _validate_categorical(row, context.schema)
    flags = _out_of_domain(row, context.schema)
    if flags:
        reasons = "; ".join(flag.message for flag in flags)
        raise ExternalPredictionInputError(
            "No prediction was generated because the request is outside the "
            f"training range: {reasons} Numerical outputs for this request are "
            "not validated for decision-making."
        )
    combination_issues = _combination_issues(row)
    if combination_issues:
        raise ExternalPredictionInputError(" ".join(combination_issues))
    frame = pd.DataFrame([row], columns=list(MODEL_FEATURE_COLUMNS))
    prediction = _predict(context, frame)
    return _build_response(context.report, prediction, flags)


def recommend_external_experiments(
    request: CofRecommendationRequest, *, artifact_dir: Path | None = None
) -> CofRecommendationResponse:
    """Generate and rank candidate physical-test conditions strictly within the training domain."""
    context = load_prediction_context(artifact_dir)

    # Validate categorical tow_type against schema
    categorical_feature = next(
        (f for f in context.schema["features"] if f.get("name") == "tow_type"),
        None,
    )
    allowed_tows = (
        categorical_feature.get("allowed_values", []) if categorical_feature else []
    )
    if request.tow_type not in allowed_tows:
        raise ExternalPredictionInputError(
            f"tow_type={request.tow_type!r} is not supported; expected one of {sorted(allowed_tows)}."
        )

    # Find normal_load_n training bounds
    load_feature = next(
        (f for f in context.schema["features"] if f.get("name") == "normal_load_n"),
        None,
    )
    if not load_feature or "min" not in load_feature or "max" not in load_feature:
        raise ExternalModelUnavailable("External model schema lacks normal_load_n bounds.")
    train_min_load = float(load_feature["min"])
    train_max_load = float(load_feature["max"])

    if request.min_load_n is not None:
        if request.min_load_n < train_min_load or request.min_load_n > train_max_load:
            raise ExternalPredictionInputError(
                f"min_load_n={request.min_load_n:g} is outside the training range "
                f"[{train_min_load:g}, {train_max_load:g}] N."
            )
    if request.max_load_n is not None:
        if request.max_load_n < train_min_load or request.max_load_n > train_max_load:
            raise ExternalPredictionInputError(
                f"max_load_n={request.max_load_n:g} is outside the training range "
                f"[{train_min_load:g}, {train_max_load:g}] N."
            )
    if request.min_load_n is not None and request.max_load_n is not None:
        if request.min_load_n >= request.max_load_n:
            raise ExternalPredictionInputError("min_load_n must be strictly less than max_load_n.")
        if request.max_load_n - request.min_load_n < 1e-4:
            raise ExternalPredictionInputError("max_load_n must exceed min_load_n by at least 1e-4 N.")

    start_load = request.min_load_n if request.min_load_n is not None else train_min_load
    end_load = request.max_load_n if request.max_load_n is not None else train_max_load

    if end_load - start_load < 1e-4:
        raise ExternalPredictionInputError("Upper load bound must exceed lower bound by at least 1e-4 N.")

    # Extract medians by tow_type if available to maintain joint physical consistency
    feature_dict = {f["name"]: f for f in context.schema["features"]}

    def _get_tow_median(name: str) -> float:
        info = feature_dict[name]
        medians_by_tow = info.get("medians_by_tow_type")
        if isinstance(medians_by_tow, dict) and request.tow_type in medians_by_tow:
            return float(medians_by_tow[request.tow_type])
        return float(info["median"])

    contact_area = _get_tow_median("contact_area_mm2")
    contact_width = _get_tow_median("contact_width_mm")
    contact_length = _get_tow_median("contact_length_scanned_mm")
    contact_half_width = _get_tow_median("contact_half_width_a_mm")
    pct_contact_length = _get_tow_median("percent_contact_length")

    candidate_loads = np.linspace(start_load, end_load, request.num_candidates)
    scored_candidates: list[tuple[CofPredictionRequest, float]] = []

    for load in candidate_loads:
        load_val = float(load)
        pressure = load_val / contact_area
        cond = CofPredictionRequest(
            normal_load_n=load_val,
            nominal_pressure_mpa=pressure,
            contact_width_mm=contact_width,
            contact_area_mm2=contact_area,
            contact_length_scanned_mm=contact_length,
            contact_half_width_a_mm=contact_half_width,
            percent_contact_length=pct_contact_length,
            tow_type=request.tow_type,
        )
        row = _feature_row(cond)
        frame = pd.DataFrame([row], columns=list(MODEL_FEATURE_COLUMNS))
        prediction = _predict(context, frame)
        scored_candidates.append((cond, prediction))

    if request.target_criterion == "lowest_predicted_cof":
        scored_candidates.sort(key=lambda item: (round(item[1], 8), item[0].normal_load_n))
    elif request.target_criterion == "highest_predicted_cof":
        scored_candidates.sort(key=lambda item: (-round(item[1], 8), item[0].normal_load_n))
    elif request.target_criterion == "load_sweep_grid":
        scored_candidates.sort(key=lambda item: item[0].normal_load_n)

    recommendations = [
        CofRecommendedCandidate(
            rank=i + 1,
            candidate_id=f"candidate-{i + 1}",
            conditions=cond,
            predicted_coefficient_of_friction=round(pred, 4),
            is_model_estimate_not_measurement=True,
            recommendation_label="Candidate condition for physical laboratory testing (not an established optimum)",
        )
        for i, (cond, pred) in enumerate(scored_candidates)
    ]

    reliability_notice = (
        "Caution: The model has negative R² (-0.74) on held-out T700-12k-50C and uncalibrated "
        "prediction intervals. Ranking order may reflect residual model bias rather than "
        "true optimal friction behavior. Model rankings for 50C must be treated with particular caution."
        if request.tow_type == "T700-12k-50C"
        else (
            "Caution: The model has negative R² (-0.74) on held-out T700-12k-50C and uncalibrated "
            "prediction intervals. Rankings are empirical approximations from 10 Cambridge ramp runs, "
            "not proven optima, and must be physically verified."
        )
    )

    return CofRecommendationResponse(
        model_id=str(context.report["model_id"]),
        source_kind="external",
        target_criterion=request.target_criterion,
        interpretation=(
            "These conditions are candidate points for laboratory testing within the Cambridge "
            "tow-on-tool training domain. They represent model estimates rather than physical "
            "measurements. They are NOT proven optima and do NOT imply a causal effect or apply "
            "to composite materials."
        ),
        causal_disclaimer=(
            "No causal relationship is inferred. Model associations reflect observational "
            "correlations in the 10 Cambridge ramp runs only."
        ),
        reliability_notice=reliability_notice,
        composite_targets_trained=False,
        recommendations=recommendations,
    )



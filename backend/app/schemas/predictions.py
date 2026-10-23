"""Request and response contracts for the external tow-on-tool COF prediction.

These models describe a single observation of the Cambridge tow-on-tool system
only. They never imply that a composite (glass-fibre/epoxy) target has been
trained, and they carry the external model's provenance and evaluation metrics
so a caller can see exactly which model answered.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

COF_TARGET_NAME = "coefficient_of_friction"
COF_DOMAIN_LIMITATION = (
    "This model was trained only on the University of Cambridge tow-on-tool "
    "friction experiments (carbon-fibre T700 12k tow sliding on a glass tool). "
    "It is an external-dataset model and is NOT a predictor for AI-TriboTwin's "
    "glass-fibre/epoxy composite experiments or for any composite friction, "
    "wear, or specific-wear-rate target."
)


def _require_finite_positive(value: float, *, field: str) -> float:
    if not math.isfinite(value):
        raise ValueError(f"{field} must be a finite number")
    if value <= 0:
        raise ValueError(f"{field} must be greater than zero")
    return value


class CofPredictionRequest(BaseModel):
    """One tow-on-tool observation to score with the external model."""

    # strict=True rejects string-encoded numbers ("18") and other coercions so a
    # malformed request fails validation instead of silently changing units.
    model_config = ConfigDict(extra="forbid", strict=True)

    normal_load_n: float = Field(description="Applied normal load, newtons")
    nominal_pressure_mpa: float = Field(description="Nominal contact pressure, megapascals")
    contact_width_mm: float = Field(description="Contact patch width, millimetres")
    contact_area_mm2: float = Field(description="Contact area, square millimetres")
    contact_length_scanned_mm: float = Field(
        description="Contact length from the scanned image, millimetres"
    )
    contact_half_width_a_mm: float = Field(description="Contact half-width a, millimetres")
    percent_contact_length: float = Field(description="Contact length as a percentage, percent")
    tow_type: str = Field(min_length=1, max_length=64, description="Carbon-fibre tow sizing label")

    @field_validator(
        "normal_load_n",
        "nominal_pressure_mpa",
        "contact_width_mm",
        "contact_area_mm2",
        "contact_length_scanned_mm",
        "contact_half_width_a_mm",
        "percent_contact_length",
    )
    @classmethod
    def numeric_fields_must_be_finite_and_positive(cls, value: float, info) -> float:
        return _require_finite_positive(value, field=info.field_name)

    @field_validator("tow_type")
    @classmethod
    def tow_type_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("tow_type must not be blank")
        return stripped


class CofExperimentCandidate(BaseModel):
    """One proposed physical-test condition to validate, never to optimize."""

    model_config = ConfigDict(extra="forbid", strict=True)

    candidate_id: str = Field(min_length=1, max_length=64)
    conditions: CofPredictionRequest


class CofCandidateValidationRequest(BaseModel):
    """A bounded list of proposed Cambridge-system physical-test conditions."""

    model_config = ConfigDict(extra="forbid", strict=True)

    candidates: list[CofExperimentCandidate] = Field(min_length=1, max_length=50)


class OutOfDomainFeature(BaseModel):
    """A submitted numeric feature that sits outside the training range."""

    feature: str
    unit: str
    value: float
    training_min: float
    training_max: float
    direction: Literal["below_min", "above_max"]
    message: str


class PredictionMetrics(BaseModel):
    """Held-out and baseline evaluation of the external model that answered."""

    mae: float
    rmse: float
    r2: float
    holdout_rows: int
    selection_basis: str
    baseline_mae: float
    baseline_rmse: float
    baseline_r2: float
    stratified_baseline_mae: float | None = None
    stratified_baseline_rmse: float | None = None
    stratified_baseline_r2: float | None = None


class PredictionProvenance(BaseModel):
    """Traceable description of the shipped external artifact bundle."""

    model_id: str
    source_kind: Literal["external"]
    source_name: str
    source_url: str
    source_workbook: str
    source_workbook_sha256: str
    processed_table: str
    processed_table_sha256: str
    dataset_sha256: str
    measurement_protocol: str
    material_domain: str
    observation_count: int
    training_rows: int
    holdout_rows: int
    training_groups: int
    holdout_groups: int
    selected_model: str
    seed: int
    range_basis: str


class CofPredictionResponse(BaseModel):
    """The single predicted coefficient of friction plus its honest framing."""

    model_id: str
    source_kind: Literal["external"]
    target: str = COF_TARGET_NAME
    target_unit: str = "dimensionless"
    predicted_coefficient_of_friction: float
    domain_status: Literal["IN_DOMAIN", "OUT_OF_DOMAIN"]
    out_of_domain_features: list[OutOfDomainFeature] = Field(default_factory=list)
    domain_limitation: str = COF_DOMAIN_LIMITATION
    interpretation: str
    metrics: PredictionMetrics
    provenance: PredictionProvenance
    composite_targets_trained: bool = False
    note: str


class CofCandidateValidationResult(BaseModel):
    """Domain check for a candidate physical test; contains no model prediction."""

    candidate_id: str
    accepted_for_physical_testing: bool
    out_of_domain_features: list[OutOfDomainFeature] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class CofCandidateValidationResponse(BaseModel):
    """Candidate range-check results without ranking or optimality claims."""

    model_id: str
    source_kind: Literal["external"]
    interpretation: str
    results: list[CofCandidateValidationResult]


class CofRecommendationRequest(BaseModel):
    """Request constrained physical-test candidate recommendations within the training domain."""

    model_config = ConfigDict(extra="forbid", strict=True)

    tow_type: str = Field(min_length=1, max_length=64, description="Carbon-fibre tow sizing label")
    min_load_n: float | None = Field(default=None, description="Lower normal load bound within training limits (N)")
    max_load_n: float | None = Field(default=None, description="Upper normal load bound within training limits (N)")
    num_candidates: int = Field(default=5, ge=2, le=20, description="Number of candidate points to generate")
    target_criterion: Literal[
        "lowest_predicted_cof", "highest_predicted_cof", "load_sweep_grid"
    ] = Field(default="lowest_predicted_cof", description="Ranking criterion for candidate test conditions")


class CofRecommendedCandidate(BaseModel):
    """One ranked test condition proposed for physical validation, not an established optimum."""

    rank: int
    candidate_id: str
    conditions: CofPredictionRequest
    predicted_coefficient_of_friction: float
    is_model_estimate_not_measurement: bool = True
    recommendation_label: str = "Candidate condition for physical laboratory testing (not an established optimum)"


class CofRecommendationResponse(BaseModel):
    """Constrained experiment recommendations bounded strictly to the training domain."""

    model_id: str
    source_kind: Literal["external"] = "external"
    target_criterion: str
    interpretation: str
    causal_disclaimer: str
    reliability_notice: str
    composite_targets_trained: bool = False
    recommendations: list[CofRecommendedCandidate]


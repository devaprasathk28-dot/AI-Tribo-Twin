from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RecordStatus(StrEnum):
    PLANNED = "PLANNED"
    MEASURED = "MEASURED"


class TestConditions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    load_n: float | None = Field(default=None, gt=0)
    sliding_velocity_m_per_s: float | None = Field(default=None, gt=0)
    sliding_distance_m: float | None = Field(default=None, gt=0)
    test_duration_min: float | None = Field(default=None, gt=0)


class Measurement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: float
    unit_as_recorded: str = Field(min_length=1, max_length=120)

    @field_validator("value")
    @classmethod
    def value_must_be_finite(cls, value: float) -> float:
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("measurement value must be finite")
        return value


class Measurements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    coefficient_of_friction: Measurement | None = None
    wear_measurement_name_as_recorded: str = Field(default="", max_length=240)
    wear_measurement: Measurement | None = None
    specific_wear_rate: Measurement | None = None
    wear_volume_loss: Measurement | None = None

    @model_validator(mode="after")
    def wear_name_required_when_value_present(self) -> "Measurements":
        if self.wear_measurement is not None and not self.wear_measurement_name_as_recorded.strip():
            raise ValueError("record the wear measurement name exactly as provided by the source")
        return self


class ExperimentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str = Field(min_length=1, max_length=120)
    record_status: RecordStatus
    material_system_as_recorded: str = Field(min_length=1, max_length=240)
    planned_by: str = Field(default="", max_length=240)
    composition_as_recorded: str = Field(default="", max_length=1000)
    composition_source_reference: str = Field(default="", max_length=1000)
    replicate_group_id: str = Field(default="", max_length=160)
    planned_conditions: TestConditions = Field(default_factory=TestConditions)
    measured_conditions: TestConditions = Field(default_factory=TestConditions)
    measurements: Measurements = Field(default_factory=Measurements)
    instrument_id: str = Field(default="", max_length=240)
    operator: str = Field(default="", max_length=240)
    experiment_date: date | None = None
    source_artifact: str = Field(default="", max_length=1000)
    source_location: str = Field(default="", max_length=1000)
    notes: str = Field(default="", max_length=4000)
    recorded_at_utc: datetime | None = None

    @field_validator("experiment_id", "material_system_as_recorded")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value

    @model_validator(mode="after")
    def validate_status_and_evidence(self) -> "ExperimentCreate":
        measured = self.measured_conditions.model_dump(exclude_none=True)
        planned = self.planned_conditions.model_dump(exclude_none=True)
        measurements = self.measurements.model_dump(exclude_none=True)

        if self.record_status is RecordStatus.PLANNED:
            if measured:
                raise ValueError("planned records cannot contain measured test conditions")
            if measurements.get("coefficient_of_friction") or measurements.get("wear_measurement"):
                raise ValueError("planned records cannot contain measured responses")
            if measurements.get("specific_wear_rate") or measurements.get("wear_volume_loss"):
                raise ValueError("planned records cannot contain measured wear targets")
            if not planned:
                raise ValueError("planned records require at least one planned test condition")
        else:
            required = {
                "load_n",
                "sliding_velocity_m_per_s",
                "sliding_distance_m",
            }
            if not required.issubset(measured):
                raise ValueError("measured records require measured load, velocity, and distance")
            if not any(
                (
                    self.measurements.coefficient_of_friction,
                    self.measurements.wear_measurement,
                    self.measurements.specific_wear_rate,
                    self.measurements.wear_volume_loss,
                )
            ):
                raise ValueError("measured records require at least one measured response")
            if not self.source_artifact.strip() or not self.source_location.strip():
                raise ValueError("measured records require source artifact and source location")
        return self


class ExperimentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material_system_as_recorded: str | None = Field(default=None, min_length=1, max_length=240)
    planned_by: str | None = Field(default=None, max_length=240)
    composition_as_recorded: str | None = Field(default=None, max_length=1000)
    composition_source_reference: str | None = Field(default=None, max_length=1000)
    replicate_group_id: str | None = Field(default=None, max_length=160)
    planned_conditions: TestConditions | None = None
    measured_conditions: TestConditions | None = None
    measurements: Measurements | None = None
    instrument_id: str | None = Field(default=None, max_length=240)
    operator: str | None = Field(default=None, max_length=240)
    experiment_date: date | None = None
    source_artifact: str | None = Field(default=None, max_length=1000)
    source_location: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("material_system_as_recorded")
    @classmethod
    def strip_required_text(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("material_system_as_recorded must not be blank")
        return value


class ExperimentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    experiment_id: str
    record_status: RecordStatus
    material_system_as_recorded: str
    planned_by: str
    composition_as_recorded: str
    composition_source_reference: str
    replicate_group_id: str
    planned_conditions: dict[str, Any]
    measured_conditions: dict[str, Any]
    measurements: dict[str, Any]
    instrument_id: str
    operator: str
    experiment_date: date | None
    source_artifact: str
    source_location: str
    notes: str
    recorded_at_utc: datetime
    created_at_utc: datetime
    import_sha256: str


class ReadinessItem(BaseModel):
    target_id: str
    target_name: str
    status: str
    evidence: str
    required_evidence: str


class ReadinessResponse(BaseModel):
    targets: list[ReadinessItem]
    warning: str


class ImportPreviewResponse(BaseModel):
    filename: str
    sha256: str
    size_bytes: int
    format_name: str
    row_count: int
    valid: bool
    errors: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
    preview_rows: list[dict[str, str | None]]
    can_confirm_import: bool
    accepted_rows: int = 0
    duplicate_rows: int = 0
    rejected_rows: int = 0
    duplicate_experiment_ids: list[str] = Field(default_factory=list)
    is_duplicate_artifact: bool = False


class ImportCommitResponse(BaseModel):
    sha256: str
    records_imported: int
    duplicate: bool
    message: str


class ImportHistoryItem(BaseModel):
    id: int
    sha256: str
    filename: str
    content_type: str
    size_bytes: int
    row_count: int
    format_name: str
    created_at_utc: datetime
    validation_outcome: str
    errors_count: int
    warnings_count: int


class NotReadyResponse(BaseModel):
    code: str = "SCIENTIFIC_READINESS_BLOCKED"
    target_id: str | None = None
    status: str = "BLOCKED"
    message: str
    required_evidence: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    database: str


class ExportRecord(BaseModel):
    records: list[ExperimentRead]
    count: int
    format: str

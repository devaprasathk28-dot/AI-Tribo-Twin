from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import asdict, dataclass
from typing import Any

from src.data.workflow import (
    INTAKE_COLUMNS,
    RAW_REQUIRED_COLUMNS,
    validate_records,
)


@dataclass(frozen=True)
class CsvValidation:
    sha256: str
    size_bytes: int
    format_name: str
    row_count: int
    errors: tuple[dict[str, Any], ...]
    warnings: tuple[dict[str, Any], ...]
    rows: tuple[dict[str, str | None], ...]

    @property
    def valid(self) -> bool:
        return not self.errors


def validate_csv(filename: str, content: bytes) -> CsvValidation:
    if not filename.lower().endswith(".csv"):
        raise ValueError("Only .csv uploads are accepted.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = content.decode("latin-1")
            except Exception as error:
                raise ValueError("CSV encoding could not be decoded. Expected UTF-8.") from error
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""))
        rows = list(reader)
    except csv.Error as error:
        raise ValueError(f"CSV parsing failed: {error}") from error
    names = reader.fieldnames or []
    report = validate_records(names, rows)
    return CsvValidation(
        sha256=hashlib.sha256(content).hexdigest(),
        size_bytes=len(content),
        format_name=report.format_name,
        row_count=report.row_count,
        errors=tuple(asdict(item) for item in report.errors),
        warnings=tuple(asdict(item) for item in report.warnings),
        rows=tuple(rows),
    )


def is_experiment_template(validation: CsvValidation) -> bool:
    return validation.format_name == "experiment-intake" and set(INTAKE_COLUMNS) <= set(
        validation.rows[0].keys() if validation.rows else ()
    )


def is_source_extraction(validation: CsvValidation) -> bool:
    return validation.format_name == "source-extraction" and set(RAW_REQUIRED_COLUMNS) <= set(
        validation.rows[0].keys() if validation.rows else ()
    )


def intake_row_to_payload(row: dict[str, str | None]) -> dict[str, Any]:
    def text(name: str) -> str:
        return (row.get(name) or "").strip()

    def number(name: str) -> float | None:
        value = text(name)
        return float(value) if value else None

    def measurement(value_key: str, unit_key: str) -> dict[str, Any] | None:
        value = number(value_key)
        if value is None:
            return None
        return {"value": value, "unit_as_recorded": text(unit_key)}

    return {
        "experiment_id": text("experiment_id"),
        "record_status": text("record_status").upper(),
        "material_system_as_recorded": text("material_system_as_recorded"),
        "planned_by": text("planned_by"),
        "composition_as_recorded": text("composition_as_recorded"),
        "composition_source_reference": text("composition_source_reference"),
        "replicate_group_id": text("replicate_group_id"),
        "planned_conditions": {
            "load_n": number("planned_load_N"),
            "sliding_velocity_m_per_s": number("planned_sliding_velocity_m_per_s"),
            "sliding_distance_m": number("planned_sliding_distance_m"),
            "test_duration_min": number("planned_test_duration_min"),
        },
        "measured_conditions": {
            "load_n": number("measured_load_N"),
            "sliding_velocity_m_per_s": number("measured_sliding_velocity_m_per_s"),
            "sliding_distance_m": number("measured_sliding_distance_m"),
            "test_duration_min": number("measured_test_duration_min"),
        },
        "measurements": {
            "coefficient_of_friction": measurement(
                "coefficient_of_friction_value",
                "coefficient_of_friction_unit_as_recorded",
            ),
            "wear_measurement_name_as_recorded": text("wear_measurement_name_as_recorded"),
            "wear_measurement": measurement(
                "wear_measurement_value",
                "wear_measurement_unit_as_recorded",
            ),
            "specific_wear_rate": measurement(
                "specific_wear_rate_value",
                "specific_wear_rate_unit_as_recorded",
            ),
            "wear_volume_loss": measurement(
                "wear_volume_loss_value",
                "wear_volume_loss_unit_as_recorded",
            ),
        },
        "instrument_id": text("instrument_id"),
        "operator": text("operator"),
        "experiment_date": text("experiment_date") or None,
        "source_artifact": text("source_artifact"),
        "source_location": text("source_location"),
        "notes": text("notes"),
        "recorded_at_utc": text("recorded_at_utc") or None,
    }

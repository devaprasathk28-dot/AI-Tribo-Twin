"""Read-only validation and provenance-preserving experimental-data intake."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from src.config import DATA_RAW, DATA_VALIDATION, PROJECT_ROOT

RAW_DATA_PATH = DATA_RAW / "tribological_experiments_raw.csv"
RAW_SHA256 = "bc4b438bfcb472bdb92d653953b23acd3ff20dbaf3e0220704aa0a16bddedd1d"
IMPORTS_DIR = PROJECT_ROOT / "data" / "working" / "imports"
PLAN_PATH = PROJECT_ROOT / "data" / "working" / "experiment_plan.csv"
TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "experiment_record_template.csv"

RAW_REQUIRED_COLUMNS = {
    "record_id",
    "material_system_raw",
    "filler_total_wt_percent_as_label",
    "filler_a_wt_percent_interpreted",
    "filler_b_wt_percent_interpreted",
    "sample_no_raw",
    "applied_load_N_raw",
    "sliding_velocity_m_per_s_raw",
    "sliding_distance_m_raw",
    "sliding_diameter_mm_raw",
    "disc_speed_rpm_raw",
    "test_duration_min_raw",
    "test_remarks_raw",
    "temperature_raw",
    "coefficient_of_friction_raw",
    "wear_rate_value_raw",
    "wear_rate_unit_as_table_heading",
    "specific_wear_rate_raw",
    "wear_volume_loss_raw",
    "source_document",
    "source_table_index_zero_based",
    "source_row_index_zero_based",
    "source_table_label_raw",
    "raw_cells_json",
    "extraction_status",
}

INTAKE_COLUMNS = [
    "record_status",
    "experiment_id",
    "recorded_at_utc",
    "planned_by",
    "material_system_as_recorded",
    "composition_as_recorded",
    "composition_source_reference",
    "replicate_group_id",
    "planned_load_N",
    "measured_load_N",
    "planned_sliding_velocity_m_per_s",
    "measured_sliding_velocity_m_per_s",
    "planned_sliding_distance_m",
    "measured_sliding_distance_m",
    "planned_test_duration_min",
    "measured_test_duration_min",
    "coefficient_of_friction_value",
    "coefficient_of_friction_unit_as_recorded",
    "wear_measurement_name_as_recorded",
    "wear_measurement_value",
    "wear_measurement_unit_as_recorded",
    "specific_wear_rate_value",
    "specific_wear_rate_unit_as_recorded",
    "wear_volume_loss_value",
    "wear_volume_loss_unit_as_recorded",
    "instrument_id",
    "operator",
    "experiment_date",
    "source_artifact",
    "source_location",
    "notes",
]

KNOWN_MATERIAL_LABELS = {
    "FeTiO3:SiO2",
    "TiO2:SiO2",
    "ZrSiO4:TiO2",
    "ZrSiO4:SiO2",
}
UNRESOLVED_MATERIAL_LABELS = {"ZrSiO4:TiO2", "ZrSiO4:SiO2"}
RAW_NUMERIC_COLUMNS = {
    "filler_a_wt_percent_interpreted",
    "filler_b_wt_percent_interpreted",
    "applied_load_N_raw",
    "sliding_velocity_m_per_s_raw",
    "sliding_distance_m_raw",
    "sliding_diameter_mm_raw",
    "disc_speed_rpm_raw",
    "test_duration_min_raw",
    "wear_rate_value_raw",
    "source_table_index_zero_based",
    "source_row_index_zero_based",
}
INTAKE_NUMERIC_COLUMNS = {
    "planned_load_N",
    "measured_load_N",
    "planned_sliding_velocity_m_per_s",
    "measured_sliding_velocity_m_per_s",
    "planned_sliding_distance_m",
    "measured_sliding_distance_m",
    "planned_test_duration_min",
    "measured_test_duration_min",
    "coefficient_of_friction_value",
    "wear_measurement_value",
    "specific_wear_rate_value",
    "wear_volume_loss_value",
}
CONDITION_COLUMNS = {
    "planned_load_N",
    "measured_load_N",
    "planned_sliding_velocity_m_per_s",
    "measured_sliding_velocity_m_per_s",
    "planned_sliding_distance_m",
    "measured_sliding_distance_m",
    "planned_test_duration_min",
    "measured_test_duration_min",
}
RESPONSE_UNIT_PAIRS = (
    ("coefficient_of_friction_value", "coefficient_of_friction_unit_as_recorded"),
    ("wear_measurement_value", "wear_measurement_unit_as_recorded"),
    ("specific_wear_rate_value", "specific_wear_rate_unit_as_recorded"),
    ("wear_volume_loss_value", "wear_volume_loss_unit_as_recorded"),
)


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    row_number: int | None = None


@dataclass(frozen=True)
class ValidationReport:
    format_name: str
    row_count: int
    findings: tuple[Finding, ...]

    @property
    def errors(self) -> tuple[Finding, ...]:
        return tuple(item for item in self.findings if item.severity == "ERROR")

    @property
    def warnings(self) -> tuple[Finding, ...]:
        return tuple(item for item in self.findings if item.severity == "WARNING")

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "format_name": self.format_name,
            "row_count": self.row_count,
            "is_valid": self.is_valid,
            "findings": [asdict(item) for item in self.findings],
        }


class IngestionError(ValueError):
    """Raised when an upload cannot be safely preserved as a working import."""


def _finding(
    findings: list[Finding],
    severity: str,
    code: str,
    message: str,
    row_number: int | None = None,
) -> None:
    findings.append(Finding(severity, code, message, row_number))


def _parse_number(value: str, column: str, row_number: int, findings: list[Finding]) -> float | None:
    if not value.strip():
        return None
    try:
        number = float(value)
    except ValueError:
        _finding(findings, "ERROR", "INVALID_NUMBER", f"{column} is not numeric: {value!r}.", row_number)
        return None
    if not math.isfinite(number):
        _finding(findings, "ERROR", "NONFINITE_NUMBER", f"{column} must be finite.", row_number)
        return None
    if column in CONDITION_COLUMNS and number <= 0:
        _finding(findings, "ERROR", "NONPOSITIVE_CONDITION", f"{column} must be greater than zero.", row_number)
    return number


def validate_records(
    fieldnames: Sequence[str] | None,
    rows: Iterable[Mapping[str, str | None]],
) -> ValidationReport:
    """Validate source-extraction CSVs or records using the future intake template."""
    records = list(rows)
    column_names = list(fieldnames or ())
    names = set(column_names)
    findings: list[Finding] = []
    if not records:
        _finding(findings, "ERROR", "NO_ROWS", "CSV contains no data rows.")
        return ValidationReport("unknown", 0, tuple(findings))
    for column in sorted(
        {name for index, name in enumerate(column_names) if name in column_names[:index]}
    ):
        _finding(
            findings,
            "ERROR",
            "DUPLICATE_COLUMN",
            f"CSV header contains duplicate column {column!r}.",
        )
    if RAW_REQUIRED_COLUMNS.issubset(names):
        format_name = "source-extraction"
        required = RAW_REQUIRED_COLUMNS
        id_column = "record_id"
        numeric_columns = RAW_NUMERIC_COLUMNS
        material_column = "material_system_raw"
    elif set(INTAKE_COLUMNS).issubset(names):
        format_name = "experiment-intake"
        required = set(INTAKE_COLUMNS)
        id_column = "experiment_id"
        numeric_columns = INTAKE_NUMERIC_COLUMNS
        material_column = "material_system_as_recorded"
    else:
        _finding(
            findings,
            "ERROR",
            "UNRECOGNIZED_SCHEMA",
            "CSV does not match the known source-extraction schema or experiment-record template.",
        )
        return ValidationReport("unknown", len(records), tuple(findings))

    for column in sorted(required - names):
        _finding(findings, "ERROR", "MISSING_COLUMN", f"Required column {column!r} is missing.")

    seen_ids: set[str] = set()
    unit_values: dict[str, set[str]] = {}
    for index, record in enumerate(records, start=2):
        if None in record:
            _finding(
                findings,
                "ERROR",
                "EXTRA_FIELDS",
                "Row contains more values than the CSV header.",
                index,
            )
        identifier = (record.get(id_column) or "").strip()
        if not identifier:
            _finding(findings, "ERROR", "MISSING_IDENTIFIER", f"{id_column} is blank.", index)
        elif identifier in seen_ids:
            _finding(findings, "ERROR", "DUPLICATE_IDENTIFIER", f"Duplicate {id_column} {identifier!r}.", index)
        if identifier:
            seen_ids.add(identifier)

        for column in numeric_columns & names:
            _parse_number(record.get(column) or "", column, index, findings)

        material = (record.get(material_column) or "").strip()
        if not material:
            _finding(findings, "WARNING", "MISSING_MATERIAL", f"{material_column} is blank.", index)
        elif material not in KNOWN_MATERIAL_LABELS:
            _finding(
                findings,
                "WARNING",
                "UNRECOGNIZED_MATERIAL",
                f"Material label {material!r} is not in the documented source labels; retain it as recorded and verify identity.",
                index,
            )
        elif material in UNRESOLVED_MATERIAL_LABELS:
            _finding(
                findings,
                "WARNING",
                "MATERIAL_IDENTITY_UNRESOLVED",
                f"{material!r} is involved in a documented paper/source identity conflict; do not treat it as verified.",
                index,
            )

        if format_name == "source-extraction":
            for column in (
                "applied_load_N_raw",
                "sliding_velocity_m_per_s_raw",
                "sliding_distance_m_raw",
                "coefficient_of_friction_raw",
                "wear_rate_value_raw",
                "wear_rate_unit_as_table_heading",
            ):
                if not (record.get(column) or "").strip():
                    _finding(
                        findings,
                        "WARNING",
                        "MISSING_SOURCE_VALUE",
                        f"{column} is blank.",
                        index,
                    )
            cof = (record.get("coefficient_of_friction_raw") or "").strip()
            if cof:
                try:
                    number = float(cof)
                except ValueError:
                    _finding(
                        findings,
                        "WARNING",
                        "COF_NOT_NUMERIC",
                        f"Preserved COF source string {cof!r} requires authoritative review; it was not modified.",
                        index,
                    )
                else:
                    if not math.isfinite(number):
                        _finding(findings, "ERROR", "NONFINITE_NUMBER", "COF must be finite.", index)

            unit = (record.get("wear_rate_unit_as_table_heading") or "").strip()
            if unit:
                unit_values.setdefault("wear_rate_value_raw", set()).add(unit)
        else:
            status = (record.get("record_status") or "").strip().upper()
            if status not in {"PLANNED", "MEASURED"}:
                _finding(
                    findings,
                    "ERROR",
                    "INVALID_RECORD_STATUS",
                    "record_status must be PLANNED or MEASURED.",
                    index,
                )

            if status == "PLANNED":
                measured_values = [
                    (record.get(value_column) or "").strip()
                    for value_column, _ in RESPONSE_UNIT_PAIRS
                ]
                if any(measured_values):
                    _finding(
                        findings,
                        "ERROR",
                        "PLANNED_HAS_RESPONSE",
                        "Planned records cannot contain measured response values.",
                        index,
                    )
                if any((record.get(f"measured_{name}") or "").strip() for name in (
                    "load_N", "sliding_velocity_m_per_s", "sliding_distance_m", "test_duration_min"
                )):
                    _finding(
                        findings,
                        "ERROR",
                        "PLANNED_HAS_ACTUAL_CONDITIONS",
                        "Planned records cannot contain measured-condition values.",
                        index,
                    )
                if not any((record.get(name) or "").strip() for name in (
                    "planned_load_N",
                    "planned_sliding_velocity_m_per_s",
                    "planned_sliding_distance_m",
                    "planned_test_duration_min",
                )):
                    _finding(
                        findings,
                        "WARNING",
                        "NO_PLANNED_CONDITIONS",
                        "No planned test conditions are recorded.",
                        index,
                    )

            if status == "MEASURED":
                actual_conditions = [
                    (record.get(name) or "").strip()
                    for name in (
                        "measured_load_N",
                        "measured_sliding_velocity_m_per_s",
                        "measured_sliding_distance_m",
                        "measured_test_duration_min",
                    )
                ]
                if not all(actual_conditions):
                    _finding(
                        findings,
                        "WARNING",
                        "MISSING_MEASURED_CONDITIONS",
                        "One or more actual test conditions are missing.",
                        index,
                    )
                populated_responses = 0
                for value_column, unit_column in RESPONSE_UNIT_PAIRS:
                    value = (record.get(value_column) or "").strip()
                    unit = (record.get(unit_column) or "").strip()
                    if value:
                        populated_responses += 1
                        if not unit:
                            _finding(
                                findings,
                                "ERROR",
                                "MISSING_MEASUREMENT_UNIT",
                                f"{value_column} has a value but {unit_column} is blank.",
                                index,
                            )
                        unit_values.setdefault(value_column, set()).add(unit)
                if not populated_responses:
                    _finding(
                        findings,
                        "WARNING",
                        "NO_RESPONSE_MEASUREMENTS",
                        "Measured record has no populated response target.",
                        index,
                    )
                if not (record.get("composition_source_reference") or "").strip():
                    _finding(
                        findings,
                        "WARNING",
                        "MISSING_COMPOSITION_PROVENANCE",
                        "No composition source reference is recorded; material identity is not verified.",
                        index,
                    )
                if not (record.get("replicate_group_id") or "").strip():
                    _finding(
                        findings,
                        "WARNING",
                        "MISSING_EXPERIMENTAL_GROUP",
                        "No replicate/shared-control group ID is recorded; independence and leakage cannot be assessed.",
                        index,
                    )

            experiment_date = (record.get("experiment_date") or "").strip()
            if experiment_date:
                try:
                    date.fromisoformat(experiment_date)
                except ValueError:
                    _finding(
                        findings,
                        "ERROR",
                        "INVALID_EXPERIMENT_DATE",
                        "experiment_date must use ISO YYYY-MM-DD format.",
                        index,
                    )

    if format_name == "source-extraction":
        for column in ("specific_wear_rate_raw", "wear_volume_loss_raw"):
            populated = sum(bool((record.get(column) or "").strip()) for record in records)
            if populated == 0:
                _finding(
                    findings,
                    "WARNING",
                    "TARGET_MEASUREMENTS_MISSING",
                    f"{column} is blank in all {len(records)} records; do not synthesize values.",
                )
        all_wear_units = {
            (record.get("wear_rate_unit_as_table_heading") or "").strip()
            for record in records
            if (record.get("wear_rate_unit_as_table_heading") or "").strip()
        }
        if len(all_wear_units) > 1:
            _finding(
                findings,
                "WARNING",
                "CROSS_SYSTEM_UNIT_DIFFERENCE",
                "Wear-rate headings differ in the source records; do not assume the values share a target definition or unit.",
            )

    for target, units in unit_values.items():
        if len(units) > 1:
            _finding(
                findings,
                "WARNING",
                "UNIT_MISMATCH",
                f"Multiple recorded unit strings occur for {target}: {', '.join(sorted(units))}.",
            )

    return ValidationReport(format_name, len(records), tuple(findings))


def validate_csv_bytes(content: bytes) -> ValidationReport:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise IngestionError("CSV must be UTF-8 or UTF-8 with BOM.") from error
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""))
        return validate_records(reader.fieldnames, reader)
    except csv.Error as error:
        raise IngestionError(f"CSV parsing failed: {error}") from error


def verify_protected_raw_data() -> tuple[int, int, str]:
    """Fail closed if the immutable source no longer matches its recorded fingerprint."""
    if not RAW_DATA_PATH.is_file():
        raise FileNotFoundError(f"Protected raw dataset not found: {RAW_DATA_PATH}")
    digest = hashlib.sha256(RAW_DATA_PATH.read_bytes()).hexdigest()
    if digest != RAW_SHA256:
        raise IngestionError("Protected raw dataset SHA-256 differs from the recorded source fingerprint.")
    with RAW_DATA_PATH.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        column_count = len(reader.fieldnames or ())
    if (len(rows), column_count) != (108, 25):
        raise IngestionError("Protected raw dataset dimensions differ from the expected 108 x 25.")
    return len(rows), column_count, digest


def load_target_readiness() -> list[dict[str, str]]:
    path = DATA_VALIDATION / "TARGET_READINESS.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Target-readiness register not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _safe_filename(filename: str) -> str:
    basename = Path(filename.replace("\\", "/")).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", basename).strip("._")
    if not cleaned or Path(cleaned).suffix.lower() != ".csv":
        raise IngestionError("Upload must have a filename ending in .csv.")
    return cleaned


def store_import(
    filename: str,
    content: bytes,
) -> tuple[Path, bool]:
    """Persist original CSV bytes in the ignored working area with a hash sidecar."""
    report = validate_csv_bytes(content)
    if not report.is_valid:
        raise IngestionError("CSV has schema or data errors; correct the source before storing an import.")
    safe_name = _safe_filename(filename)
    digest = hashlib.sha256(content).hexdigest()
    IMPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stem = Path(safe_name).stem[:80]
    destination = IMPORTS_DIR / f"{stem}_{digest[:12]}.csv"
    metadata_path = destination.with_suffix(".json")
    if destination.exists():
        if hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
            raise IngestionError("Import filename collision; refusing to overwrite an existing artifact.")
        if not metadata_path.exists():
            metadata = {
                "original_filename": safe_name,
                "sha256": digest,
                "size_bytes": len(content),
                "imported_at_utc": datetime.now(timezone.utc).isoformat(),
                "validation": report.to_dict(),
                "note": "Import timestamp is not the experiment date; source bytes are preserved unchanged.",
            }
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return destination, False

    destination.write_bytes(content)
    metadata = {
        "original_filename": safe_name,
        "sha256": digest,
        "size_bytes": len(content),
        "imported_at_utc": datetime.now(timezone.utc).isoformat(),
        "validation": report.to_dict(),
        "note": "Import timestamp is not the experiment date; source bytes are preserved unchanged.",
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return destination, True


def save_planned_experiment(values: Mapping[str, str]) -> Path:
    """Append a plan-only record; measured-response fields must stay empty."""
    row = {column: str(values.get(column, "")) for column in INTAKE_COLUMNS}
    row["record_status"] = "PLANNED"
    row["recorded_at_utc"] = datetime.now(timezone.utc).isoformat()
    planned_conditions = (
        "planned_load_N",
        "planned_sliding_velocity_m_per_s",
        "planned_sliding_distance_m",
        "planned_test_duration_min",
    )
    if any(not row[column].strip() for column in planned_conditions):
        raise IngestionError("All four planned test conditions must be recorded.")
    report = validate_records(INTAKE_COLUMNS, [row])
    if not report.is_valid:
        raise IngestionError("; ".join(finding.message for finding in report.errors))
    experiment_id = row["experiment_id"].strip()
    if not experiment_id:
        raise IngestionError("An experiment_id is required for a saved plan.")

    PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict[str, str]] = []
    if PLAN_PATH.exists():
        with PLAN_PATH.open("r", encoding="utf-8-sig", newline="") as stream:
            existing = list(csv.DictReader(stream))
    if any(item.get("experiment_id") == experiment_id for item in existing):
        raise IngestionError(f"Experiment ID {experiment_id!r} already exists in the plan.")

    write_header = not PLAN_PATH.exists()
    with PLAN_PATH.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=INTAKE_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
    return PLAN_PATH

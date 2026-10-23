"""Build a traceable, non-training COF evidence map from protected source records."""

from __future__ import annotations

import csv
from pathlib import Path

from src.data.workflow import RAW_DATA_PATH, verify_protected_raw_data

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_VERIFICATION_PATH = PROJECT_ROOT / "data" / "validation" / "ROW_LEVEL_SOURCE_VERIFICATION.csv"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "validation" / "COF_EVIDENCE_MAPPING.csv"

MAPPING_COLUMNS = (
    "record_id",
    "source_document",
    "source_table_index_zero_based",
    "source_row_index_zero_based",
    "source_table_context_paragraph",
    "sample_no_raw",
    "experimental_run_id",
    "experimental_run_id_status",
    "validation_group_id",
    "validation_group_status",
    "material_system_raw",
    "filler_total_wt_percent_as_label",
    "filler_a_wt_percent_interpreted",
    "filler_b_wt_percent_interpreted",
    "applied_load_N_raw",
    "sliding_velocity_m_per_s_raw",
    "sliding_distance_m_raw",
    "sliding_diameter_mm_raw",
    "disc_speed_rpm_raw",
    "test_duration_min_raw",
    "temperature_raw",
    "coefficient_of_friction_raw",
    "cof_numeric_status",
    "cof_unit_as_recorded",
    "source_cells_match",
    "source_verification_status",
    "evidence_reference",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _cof_numeric_status(value: str) -> str:
    try:
        float(value)
    except ValueError:
        return "SOURCE_STRING_NOT_NUMERIC_DO_NOT_CORRECT"
    return "NUMERIC_SOURCE_STRING"


def build_cof_evidence_mapping(output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    """Write a derived mapping while preserving source literals and unknown run structure."""
    verify_protected_raw_data()
    raw_rows = _read_csv(RAW_DATA_PATH)
    verified_rows = _read_csv(SOURCE_VERIFICATION_PATH)
    verification_by_id = {row["record_id"]: row for row in verified_rows}
    if len(raw_rows) != 108 or len(verification_by_id) != 108:
        raise ValueError("COF evidence map requires the complete 108-row source-verification manifest.")

    mapped_rows: list[dict[str, str]] = []
    for raw in raw_rows:
        record_id = raw["record_id"]
        verified = verification_by_id.get(record_id)
        if verified is None or verified.get("raw_cells_match", "").lower() != "true":
            raise ValueError(f"{record_id} does not have exact source-cell verification.")
        mapped_rows.append(
            {
                "record_id": record_id,
                "source_document": raw["source_document"],
                "source_table_index_zero_based": raw["source_table_index_zero_based"],
                "source_row_index_zero_based": raw["source_row_index_zero_based"],
                "source_table_context_paragraph": verified.get("source_table_context_paragraph", ""),
                "sample_no_raw": raw["sample_no_raw"],
                "experimental_run_id": "",
                "experimental_run_id_status": "NOT_PRESENT_IN_AVAILABLE_SOURCE_EVIDENCE",
                "validation_group_id": "",
                "validation_group_status": "NOT_ESTABLISHED_DO_NOT_SPLIT_OR_TRAIN",
                "material_system_raw": raw["material_system_raw"],
                "filler_total_wt_percent_as_label": raw["filler_total_wt_percent_as_label"],
                "filler_a_wt_percent_interpreted": raw["filler_a_wt_percent_interpreted"],
                "filler_b_wt_percent_interpreted": raw["filler_b_wt_percent_interpreted"],
                "applied_load_N_raw": raw["applied_load_N_raw"],
                "sliding_velocity_m_per_s_raw": raw["sliding_velocity_m_per_s_raw"],
                "sliding_distance_m_raw": raw["sliding_distance_m_raw"],
                "sliding_diameter_mm_raw": raw["sliding_diameter_mm_raw"],
                "disc_speed_rpm_raw": raw["disc_speed_rpm_raw"],
                "test_duration_min_raw": raw["test_duration_min_raw"],
                "temperature_raw": raw["temperature_raw"],
                "coefficient_of_friction_raw": raw["coefficient_of_friction_raw"],
                "cof_numeric_status": _cof_numeric_status(raw["coefficient_of_friction_raw"]),
                "cof_unit_as_recorded": "",
                "source_cells_match": verified["raw_cells_match"],
                "source_verification_status": verified["verification_status"],
                "evidence_reference": (
                    f"{raw['source_document']}; table {raw['source_table_index_zero_based']}; "
                    f"row {raw['source_row_index_zero_based']}"
                ),
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=MAPPING_COLUMNS)
        writer.writeheader()
        writer.writerows(mapped_rows)
    return output_path

from __future__ import annotations

import csv
import hashlib
import io

import pytest

from src.data import workflow
from src.data.cof_evidence import build_cof_evidence_mapping
from src.optimization.interface import OptimizationBlockedError, optimize
from src.prediction.interface import PredictionBlockedError, predict


def intake_record(**updates: str) -> dict[str, str]:
    record = {column: "" for column in workflow.INTAKE_COLUMNS}
    record.update(
        {
            "record_status": "MEASURED",
            "experiment_id": "EXP-001",
            "material_system_as_recorded": "FeTiO3:SiO2",
            "composition_as_recorded": "as recorded in preparation sheet",
            "composition_source_reference": "lab-book/page-1",
            "measured_load_N": "10",
            "measured_sliding_velocity_m_per_s": "0.5",
            "measured_sliding_distance_m": "100",
            "measured_test_duration_min": "10",
            "coefficient_of_friction_value": "0.31",
            "coefficient_of_friction_unit_as_recorded": "dimensionless",
        }
    )
    record.update(updates)
    return record


def source_record(**updates: str) -> dict[str, str]:
    record = {column: "" for column in workflow.RAW_REQUIRED_COLUMNS}
    record.update(
        {
            "record_id": "RAW-TEST-1",
            "material_system_raw": "FeTiO3:SiO2",
            "applied_load_N_raw": "10",
            "sliding_velocity_m_per_s_raw": "0.5",
            "sliding_distance_m_raw": "100",
            "coefficient_of_friction_raw": "0.31",
            "wear_rate_value_raw": "405.89",
            "wear_rate_unit_as_table_heading": "Micron",
            "source_document": "source.docx",
            "source_row_index_zero_based": "3",
        }
    )
    record.update(updates)
    return record


def validate_intake(*records: dict[str, str]) -> workflow.ValidationReport:
    return workflow.validate_records(workflow.INTAKE_COLUMNS, records)


def test_valid_measured_record_passes_schema_validation() -> None:
    report = validate_intake(intake_record())

    assert report.format_name == "experiment-intake"
    assert report.is_valid
    assert not report.errors


def test_missing_response_measurements_are_reported_without_fabrication() -> None:
    record = intake_record(
        coefficient_of_friction_value="",
        coefficient_of_friction_unit_as_recorded="",
    )

    report = validate_intake(record)

    assert report.is_valid
    assert any(item.code == "NO_RESPONSE_MEASUREMENTS" for item in report.warnings)
    assert record["coefficient_of_friction_value"] == ""


def test_inconsistent_units_are_flagged() -> None:
    first = intake_record(experiment_id="EXP-001")
    second = intake_record(
        experiment_id="EXP-002",
        coefficient_of_friction_unit_as_recorded="unknown-unit-label",
    )

    report = validate_intake(first, second)

    assert report.is_valid
    assert any(item.code == "UNIT_MISMATCH" for item in report.warnings)


def test_unresolved_material_identity_is_not_marked_verified() -> None:
    report = validate_intake(intake_record(material_system_as_recorded="ZrSiO4:TiO2"))

    assert report.is_valid
    assert any(item.code == "MATERIAL_IDENTITY_UNRESOLVED" for item in report.warnings)


def test_duplicate_experiment_identifiers_are_errors() -> None:
    report = validate_intake(intake_record(), intake_record())

    assert not report.is_valid
    assert any(item.code == "DUPLICATE_IDENTIFIER" for item in report.errors)


def test_invalid_numeric_value_and_missing_measurement_unit_are_errors() -> None:
    report = validate_intake(
        intake_record(
            measured_load_N="ten",
            coefficient_of_friction_unit_as_recorded="",
        )
    )

    assert not report.is_valid
    assert {item.code for item in report.errors} >= {
        "INVALID_NUMBER",
        "MISSING_MEASUREMENT_UNIT",
    }


def test_planned_record_cannot_contain_measured_response() -> None:
    report = validate_intake(
        intake_record(
            record_status="PLANNED",
            planned_load_N="10",
            coefficient_of_friction_value="0.3",
        )
    )

    assert not report.is_valid
    assert any(item.code == "PLANNED_HAS_RESPONSE" for item in report.errors)


def test_planned_record_cannot_contain_measured_conditions() -> None:
    report = validate_intake(
        intake_record(
            record_status="PLANNED",
            planned_load_N="10",
            measured_load_N="10",
        )
    )

    assert not report.is_valid
    assert any(item.code == "PLANNED_HAS_ACTUAL_CONDITIONS" for item in report.errors)


def test_measured_record_without_experimental_group_is_flagged() -> None:
    report = validate_intake(intake_record(replicate_group_id=""))

    assert any(item.code == "MISSING_EXPERIMENTAL_GROUP" for item in report.warnings)


def test_source_validation_preserves_and_flags_source_anomalies() -> None:
    first = source_record(specific_wear_rate_raw="", wear_volume_loss_raw="")
    second = source_record(record_id="RAW-TEST-2", coefficient_of_friction_raw="0. 29")

    report = workflow.validate_records(
        list(workflow.RAW_REQUIRED_COLUMNS),
        [first, second],
    )

    assert report.is_valid
    assert any(item.code == "COF_NOT_NUMERIC" for item in report.warnings)
    assert any(item.code == "TARGET_MEASUREMENTS_MISSING" for item in report.warnings)
    assert second["coefficient_of_friction_raw"] == "0. 29"


def test_known_source_unit_heading_variants_are_not_pooled() -> None:
    rows = [
        source_record(),
        source_record(
            record_id="RAW-TEST-2",
            wear_rate_unit_as_table_heading="Wear rate (Micron)",
        ),
    ]

    report = workflow.validate_records(list(workflow.RAW_REQUIRED_COLUMNS), rows)

    assert any(item.code == "CROSS_SYSTEM_UNIT_DIFFERENCE" for item in report.warnings)


def test_import_stores_original_bytes_only_in_working_area(tmp_path, monkeypatch) -> None:
    record = intake_record()
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=workflow.INTAKE_COLUMNS)
    writer.writeheader()
    writer.writerow(record)
    original = buffer.getvalue().encode("utf-8")
    imports_dir = tmp_path / "imports"
    monkeypatch.setattr(workflow, "IMPORTS_DIR", imports_dir)

    path, created = workflow.store_import("../incoming/record.csv", original)

    assert created
    assert path.parent == imports_dir
    assert path.read_bytes() == original
    assert hashlib.sha256(path.read_bytes()).hexdigest() == hashlib.sha256(original).hexdigest()
    assert path.with_suffix(".json").is_file()


def test_prediction_is_blocked_for_current_targets() -> None:
    with pytest.raises(PredictionBlockedError, match="BLOCKED"):
        predict("TARGET-COF", {})


def test_prediction_requires_model_and_evaluation_provenance(monkeypatch) -> None:
    from src.prediction import interface

    class UntrackedPredictor:
        target_id = "TARGET-COF"

        def predict(self, inputs: dict[str, str]) -> float:
            return 0.3

    monkeypatch.setattr(
        interface,
        "load_target_readiness",
        lambda: [{"target_id": "TARGET-COF", "ml_readiness": "READY"}],
    )

    with pytest.raises(PredictionBlockedError, match="artifact and legitimate evaluation evidence"):
        interface.predict("TARGET-COF", {}, UntrackedPredictor())


def test_optimization_is_blocked_for_current_targets() -> None:
    with pytest.raises(OptimizationBlockedError, match="BLOCKED"):
        optimize(["TARGET-COF"])


def test_protected_raw_dataset_fingerprint_and_dimensions() -> None:
    rows, columns, digest = workflow.verify_protected_raw_data()

    assert (rows, columns) == (108, 25)
    assert digest == workflow.RAW_SHA256


def test_cof_evidence_map_preserves_anomalies_and_refuses_to_invent_run_groups(tmp_path) -> None:
    output_path = build_cof_evidence_mapping(tmp_path / "COF_EVIDENCE_MAPPING.csv")
    with output_path.open("r", encoding="utf-8", newline="") as stream:
        rows = {row["record_id"]: row for row in csv.DictReader(stream)}

    assert len(rows) == 108
    for record_id, literal in (("RAW-096", "0. 29"), ("RAW-105", "0. 36")):
        row = rows[record_id]
        assert row["coefficient_of_friction_raw"] == literal
        assert row["cof_numeric_status"] == "SOURCE_STRING_NOT_NUMERIC_DO_NOT_CORRECT"
        assert row["source_cells_match"] == "true"
        assert row["experimental_run_id"] == ""
        assert row["validation_group_id"] == ""
    assert {
        row["validation_group_status"] for row in rows.values()
    } == {"NOT_ESTABLISHED_DO_NOT_SPLIT_OR_TRAIN"}


def test_planning_records_are_saved_separately_as_planned(tmp_path, monkeypatch) -> None:
    plan_path = tmp_path / "working" / "experiment_plan.csv"
    monkeypatch.setattr(workflow, "PLAN_PATH", plan_path)

    saved = workflow.save_planned_experiment(
        {
            "experiment_id": "PLAN-001",
            "material_system_as_recorded": "not yet confirmed",
            "planned_load_N": "10",
            "planned_sliding_velocity_m_per_s": "0.5",
            "planned_sliding_distance_m": "100",
            "planned_test_duration_min": "10",
        }
    )

    with saved.open("r", encoding="utf-8", newline="") as stream:
        stored = next(csv.DictReader(stream))
    assert stored["record_status"] == "PLANNED"
    assert stored["coefficient_of_friction_value"] == ""
    assert stored["wear_measurement_value"] == ""
    assert stored["recorded_at_utc"]


def test_duplicate_plan_id_is_rejected(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(workflow, "PLAN_PATH", tmp_path / "experiment_plan.csv")
    values = {
        "experiment_id": "PLAN-001",
        "planned_load_N": "10",
        "planned_sliding_velocity_m_per_s": "0.5",
        "planned_sliding_distance_m": "100",
        "planned_test_duration_min": "10",
    }
    workflow.save_planned_experiment(values)

    with pytest.raises(workflow.IngestionError, match="already exists"):
        workflow.save_planned_experiment(values)


def test_template_header_matches_validator_schema() -> None:
    with workflow.TEMPLATE_PATH.open("r", encoding="utf-8", newline="") as stream:
        header = next(csv.reader(stream))

    assert header == workflow.INTAKE_COLUMNS


def test_import_revalidates_content_instead_of_trusting_external_report(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(workflow, "IMPORTS_DIR", tmp_path / "imports")

    with pytest.raises(workflow.IngestionError, match="schema or data errors"):
        workflow.store_import("invalid.csv", b"not,a,recognized,schema\n1,2,3,4\n")

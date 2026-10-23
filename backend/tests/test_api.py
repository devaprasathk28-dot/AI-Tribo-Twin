from __future__ import annotations

import csv
import hashlib
import io

from fastapi.testclient import TestClient

from app.services.validation import INTAKE_COLUMNS


def measured_payload(experiment_id: str = "RUN-001") -> dict[str, object]:
    return {
        "experiment_id": experiment_id,
        "record_status": "MEASURED",
        "material_system_as_recorded": "FeTiO3:SiO2",
        "composition_as_recorded": "As prepared, see record",
        "composition_source_reference": "lab-book/entry-10",
        "replicate_group_id": "BATCH-A-R1",
        "measured_conditions": {
            "load_n": 10,
            "sliding_velocity_m_per_s": 0.5,
            "sliding_distance_m": 100,
            "test_duration_min": 10,
        },
        "measurements": {
            "coefficient_of_friction": {
                "value": 0.31,
                "unit_as_recorded": "dimensionless",
            }
        },
        "source_artifact": "instrument-export.csv",
        "source_location": "run RUN-001",
        "operator": "Operator A",
        "instrument_id": "POD-01",
        "experiment_date": "2026-10-10",
    }


def planned_payload(experiment_id: str = "PLAN-001") -> dict[str, object]:
    return {
        "experiment_id": experiment_id,
        "record_status": "PLANNED",
        "planned_by": "Researcher",
        "material_system_as_recorded": "as proposed",
        "composition_as_recorded": "to be confirmed by lab",
        "planned_conditions": {
            "load_n": 10,
            "sliding_velocity_m_per_s": 0.5,
            "sliding_distance_m": 100,
            "test_duration_min": 10,
        },
    }


def template_csv(rows: list[dict[str, str]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=INTAKE_COLUMNS)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def planned_csv_row(experiment_id: str) -> dict[str, str]:
    return {
        **{column: "" for column in INTAKE_COLUMNS},
        "record_status": "PLANNED",
        "experiment_id": experiment_id,
        "planned_by": "Researcher",
        "material_system_as_recorded": "as proposed",
        "composition_as_recorded": "pending lab verification",
        "planned_load_N": "10",
        "planned_sliding_velocity_m_per_s": "0.5",
        "planned_sliding_distance_m": "100",
        "planned_test_duration_min": "10",
    }


def test_health_includes_database_status(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_readiness_returns_independent_blocked_targets(client: TestClient) -> None:
    response = client.get("/api/v1/readiness")

    assert response.status_code == 200
    targets = response.json()["targets"]
    assert {target["target_id"] for target in targets} == {
        "TARGET-COF",
        "TARGET-WEAR",
        "TARGET-SWR",
        "TARGET-WVL",
    }
    assert all(target["status"] == "BLOCKED" for target in targets)


def test_model_status_separates_synthetic_demo_from_experimental_targets(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/models/status")

    assert response.status_code == 200
    body = response.json()
    assert body["training_source"] == "synthetic_fixture_only"
    assert body["experimental_model_trained"] is False
    assert {target["target_id"] for target in body["experimental_targets"]} == {
        "TARGET-COF",
        "TARGET-WEAR",
        "TARGET-SWR",
        "TARGET-WVL",
    }
    assert all(target["status"] == "BLOCKED" for target in body["experimental_targets"])
    if body["demo_report"] is not None:
        assert body["demo_report"]["synthetic_only"] is True
        assert body["demo_report"]["experimental_results"] is False


def test_model_status_serves_report_only_with_synthetic_provenance(
    client: TestClient, monkeypatch, tmp_path
) -> None:
    import json

    from app.services import model_status

    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "status": "EVALUATED_SYNTHETIC_DEMO",
                "source_kind": "synthetic",
                "synthetic_only": True,
                "experimental_results": False,
                "target_id": "SYNTHETIC-DEMO",
                "selected_model": "ridge_regression",
                "training_rows": 12,
                "holdout_rows": 4,
                "training_groups": 10,
                "holdout_groups": 2,
                "holdout_metrics": {"mae": 0.1, "rmse": 0.2, "r2": 0.8},
                "interpretation": "Synthetic fixture only.",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(model_status, "DEMO_REPORT_PATH", report_path)
    monkeypatch.setattr(model_status, "DEMO_PLOT_PATH", tmp_path / "plot.png")

    response = client.get("/api/v1/models/status")

    assert response.status_code == 200
    assert response.json()["demo_status"] == "EVALUATED_SYNTHETIC_DEMO"
    assert response.json()["demo_report"]["target_id"] == "SYNTHETIC-DEMO"
    assert response.json()["experimental_model_trained"] is False


def test_model_demo_plot_has_clear_not_generated_response(
    client: TestClient, monkeypatch, tmp_path
) -> None:
    from app.api import routes

    monkeypatch.setattr(routes, "DEMO_PLOT_PATH", tmp_path / "missing.png")

    response = client.get("/api/v1/models/demo/predictions.png")

    assert response.status_code == 404
    assert response.json()["detail"] == "Synthetic evaluation plot has not been generated."


def test_model_demo_plot_serves_generated_image(client: TestClient, monkeypatch, tmp_path) -> None:
    from app.api import routes

    plot_path = tmp_path / "predictions.png"
    plot_path.write_bytes(b"\x89PNG\r\n\x1a\nfixture-image")
    monkeypatch.setattr(routes, "DEMO_PLOT_PATH", plot_path)

    response = client.get("/api/v1/models/demo/predictions.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == plot_path.read_bytes()


def test_measured_experiment_can_be_created_retrieved_and_exported(client: TestClient) -> None:
    created = client.post("/api/v1/experiments", json=measured_payload())

    assert created.status_code == 201
    assert created.json()["record_status"] == "MEASURED"
    assert created.json()["measurements"]["coefficient_of_friction"]["value"] == 0.31

    retrieved = client.get("/api/v1/experiments/RUN-001")
    assert retrieved.status_code == 200
    assert retrieved.json()["source_artifact"] == "instrument-export.csv"
    assert retrieved.json()["replicate_group_id"] == "BATCH-A-R1"

    exported = client.get("/api/v1/exports/experiments.csv")
    assert exported.status_code == 200
    assert "RUN-001" in exported.text
    assert "instrument-export.csv" in exported.text


def test_duplicate_experiment_identifier_is_rejected(client: TestClient) -> None:
    assert client.post("/api/v1/experiments", json=measured_payload()).status_code == 201

    duplicate = client.post("/api/v1/experiments", json=measured_payload())

    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "DUPLICATE_EXPERIMENT_ID"


def test_invalid_measured_record_is_rejected(client: TestClient) -> None:
    payload = measured_payload()
    payload["measured_conditions"] = {"load_n": 10}

    response = client.post("/api/v1/experiments", json=payload)

    assert response.status_code == 422


def test_plan_is_persisted_as_planned_without_measured_responses(client: TestClient) -> None:
    response = client.post("/api/v1/plans", json=planned_payload())

    assert response.status_code == 201
    assert response.json()["record_status"] == "PLANNED"
    assert response.json()["measurements"] == {"wear_measurement_name_as_recorded": ""}
    assert client.get("/api/v1/experiments/PLAN-001").status_code == 200


def test_planning_endpoint_rejects_measured_records(client: TestClient) -> None:
    response = client.post("/api/v1/plans", json=measured_payload())

    assert response.status_code == 422


def test_csv_preview_does_not_persist_records(client: TestClient) -> None:
    content = template_csv([planned_csv_row("PLAN-PREVIEW")])
    preview = client.post(
        "/api/v1/imports/preview",
        files={"file": ("plans.csv", content, "text/csv")},
    )

    assert preview.status_code == 200
    assert preview.json()["valid"] is True
    assert preview.json()["can_confirm_import"] is True
    assert client.get("/api/v1/experiments").json() == []


def test_csv_preview_rejects_rows_with_extra_values_without_server_error(client: TestClient) -> None:
    content = template_csv([planned_csv_row("PLAN-EXTRA")])
    header, row = content.decode("utf-8").splitlines()
    malformed = f"{header}\n{row},unexpected-value\n".encode("utf-8")

    response = client.post(
        "/api/v1/imports/preview",
        files={"file": ("extra-values.csv", malformed, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["can_confirm_import"] is False
    assert any(error["code"] == "EXTRA_FIELDS" for error in response.json()["errors"])
    assert response.json()["preview_rows"][0]["experiment_id"] == "PLAN-EXTRA"


def test_csv_preview_rejects_duplicate_headers(client: TestClient) -> None:
    content = template_csv([planned_csv_row("PLAN-DUPLICATE-HEADER")])
    header, row = content.decode("utf-8").splitlines()
    duplicate_header = f"{header},experiment_id\n{row},SHADOW-ID\n".encode("utf-8")

    response = client.post(
        "/api/v1/imports/preview",
        files={"file": ("duplicate-header.csv", duplicate_header, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["can_confirm_import"] is False
    assert any(error["code"] == "DUPLICATE_COLUMN" for error in response.json()["errors"])


def test_confirm_import_requires_preview_hash_and_explicit_confirmation(client: TestClient) -> None:
    content = template_csv([planned_csv_row("PLAN-IMPORT")])
    digest = hashlib.sha256(content).hexdigest()

    no_confirm = client.post(
        "/api/v1/imports/confirm",
        files={"file": ("plans.csv", content, "text/csv")},
        data={"expected_sha256": digest, "confirmation": "false"},
    )
    mismatch = client.post(
        "/api/v1/imports/confirm",
        files={"file": ("plans.csv", content, "text/csv")},
        data={"expected_sha256": "0" * 64, "confirmation": "true"},
    )

    assert no_confirm.status_code == 400
    assert mismatch.status_code == 409
    assert client.get("/api/v1/experiments").json() == []


def test_confirm_import_persists_original_and_records_and_blocks_duplicate_hash(client: TestClient) -> None:
    content = template_csv([planned_csv_row("PLAN-IMPORTED")])
    digest = hashlib.sha256(content).hexdigest()
    imported = client.post(
        "/api/v1/imports/confirm",
        files={"file": ("plans.csv", content, "text/csv")},
        data={"expected_sha256": digest, "confirmation": "true"},
    )
    duplicate = client.post(
        "/api/v1/imports/confirm",
        files={"file": ("plans.csv", content, "text/csv")},
        data={"expected_sha256": digest, "confirmation": "true"},
    )

    assert imported.status_code == 200
    assert imported.json()["records_imported"] == 1
    assert imported.json()["sha256"] == digest
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "DUPLICATE_IMPORT"
    records = client.get("/api/v1/experiments").json()
    assert len(records) == 1
    assert records[0]["import_sha256"] == digest


def test_import_rejects_duplicate_ids_in_one_file(client: TestClient) -> None:
    content = template_csv([planned_csv_row("DUPLICATE"), planned_csv_row("DUPLICATE")])
    digest = hashlib.sha256(content).hexdigest()

    response = client.post(
        "/api/v1/imports/confirm",
        files={"file": ("plans.csv", content, "text/csv")},
        data={"expected_sha256": digest, "confirmation": "true"},
    )

    assert response.status_code == 422
    assert client.get("/api/v1/experiments").json() == []


def test_source_extraction_can_be_previewed_but_not_imported_as_new_runs(client: TestClient) -> None:
    from pathlib import Path

    raw_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "tribological_experiments_raw.csv"
    content = raw_path.read_bytes()
    preview = client.post(
        "/api/v1/imports/preview",
        files={"file": ("tribological_experiments_raw.csv", content, "text/csv")},
    )

    assert preview.status_code == 200
    assert preview.json()["format_name"] == "source-extraction"
    assert preview.json()["can_confirm_import"] is False


def test_blocked_prediction_and_optimization_return_structured_not_ready(client: TestClient) -> None:
    prediction = client.post("/api/v1/predictions/TARGET-COF")
    optimization = client.post(
        "/api/v1/optimizations",
        params=[("objective_ids", "TARGET-COF"), ("objective_ids", "TARGET-WEAR")],
    )

    assert prediction.status_code == 409
    assert prediction.json()["code"] == "SCIENTIFIC_READINESS_BLOCKED"
    assert prediction.json()["target_id"] == "TARGET-COF"
    assert prediction.json()["required_evidence"]
    assert optimization.status_code == 409
    assert optimization.json()["code"] == "SCIENTIFIC_READINESS_BLOCKED"
def test_model_status_exposes_separate_external_real_data_model(client: TestClient) -> None:
    body = client.get("/api/v1/models/status").json()

    external = body["external_model"]
    assert external["status"] in {"NOT_RUN", "EVALUATED_EXTERNAL_COF"}
    assert body["experimental_model_trained"] is False
    if external["status"] == "EVALUATED_EXTERNAL_COF":
        report = external["report"]
        assert report["source_kind"] == "external"
        assert report["is_ai_tribotwin_model"] is False
        assert report["model_id"] == "TOW-TOOL-COF-CAMBRIDGE"
        for name in ("mae", "rmse", "r2"):
            assert isinstance(report["holdout_metrics"][name], (int, float))
            assert isinstance(report["baseline_metrics"][name], (int, float))


def test_external_model_status_is_not_run_without_artifacts(tmp_path) -> None:
    from app.services import model_status

    status = model_status.get_external_model_status(tmp_path)

    assert status["status"] == "NOT_RUN"
    assert status["report"] is None


def test_external_model_plot_reports_clear_not_generated_response(
    client: TestClient, monkeypatch, tmp_path
) -> None:
    from app.api import routes

    monkeypatch.setattr(routes, "EXTERNAL_PLOT_PATH", tmp_path / "missing.png")

    response = client.get("/api/v1/models/external/predictions.png")

    assert response.status_code == 404
    assert response.json()["detail"] == "External-model evaluation plot has not been generated."


def test_external_model_plot_serves_generated_image(client: TestClient, monkeypatch, tmp_path) -> None:
    from app.api import routes

    plot_path = tmp_path / "external.png"
    plot_path.write_bytes(b"\x89PNG\r\n\x1a\nfixture-image")
    monkeypatch.setattr(routes, "EXTERNAL_PLOT_PATH", plot_path)

    response = client.get("/api/v1/models/external/predictions.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == plot_path.read_bytes()


def test_update_measured_record(client: TestClient) -> None:
    client.post("/api/v1/experiments", json=measured_payload("EXP-UPD-01"))

    update_payload = {
        "material_system_as_recorded": "Ti-6Al-4V modified",
        "notes": "Updated tribological evaluation notes",
        "operator": "Senior Metallurgist",
        "measured_conditions": {
            "load_n": 15,
            "sliding_velocity_m_per_s": 0.8,
            "sliding_distance_m": 250,
            "test_duration_min": 15,
        },
        "measurements": {
            "coefficient_of_friction": {
                "value": 0.285,
                "unit_as_recorded": "dimensionless",
            }
        },
    }
    response = client.put("/api/v1/experiments/EXP-UPD-01", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["material_system_as_recorded"] == "Ti-6Al-4V modified"
    assert data["notes"] == "Updated tribological evaluation notes"
    assert data["operator"] == "Senior Metallurgist"
    assert data["measured_conditions"]["load_n"] == 15
    assert data["measurements"]["coefficient_of_friction"]["value"] == 0.285

    # Verify persistence via get
    fetched = client.get("/api/v1/experiments/EXP-UPD-01").json()
    assert fetched["material_system_as_recorded"] == "Ti-6Al-4V modified"
    assert fetched["notes"] == "Updated tribological evaluation notes"


def test_update_planned_record(client: TestClient) -> None:
    client.post("/api/v1/plans", json=planned_payload("EXP-PLAN-UPD"))

    update_payload = {
        "material_system_as_recorded": "Proposed Alloy B",
        "notes": "Planned for Q4 testing",
        "planned_conditions": {
            "load_n": 25,
            "sliding_velocity_m_per_s": 1.2,
            "sliding_distance_m": 500,
        },
    }
    response = client.put("/api/v1/experiments/EXP-PLAN-UPD", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["material_system_as_recorded"] == "Proposed Alloy B"
    assert data["planned_conditions"]["load_n"] == 25


def test_update_scientific_safeguards_prevent_cross_state_contamination(client: TestClient) -> None:
    client.post("/api/v1/plans", json=planned_payload("PLAN-SAFEGUARD-01"))

    # Attempt to inject measurements into a planned record
    response = client.put(
        "/api/v1/experiments/PLAN-SAFEGUARD-01",
        json={
            "measured_conditions": {
                "load_n": 20,
                "sliding_velocity_m_per_s": 0.5,
                "sliding_distance_m": 100,
            }
        },
    )
    assert response.status_code == 422
    assert "Planned records cannot contain measured test conditions" in response.json()["detail"]

    response2 = client.put(
        "/api/v1/experiments/PLAN-SAFEGUARD-01",
        json={
            "measurements": {
                "coefficient_of_friction": {
                    "value": 0.25,
                    "unit_as_recorded": "dimensionless",
                }
            }
        },
    )
    assert response2.status_code == 422
    assert "Planned records cannot contain measured responses" in response2.json()["detail"]


def test_update_measured_record_rejects_missing_required_conditions(client: TestClient) -> None:
    client.post("/api/v1/experiments", json=measured_payload("EXP-REQ-COND"))

    # Attempt to update measured conditions missing sliding_distance_m
    response = client.put(
        "/api/v1/experiments/EXP-REQ-COND",
        json={
            "measured_conditions": {
                "load_n": 10,
                "sliding_velocity_m_per_s": 0.5,
            }
        },
    )
    assert response.status_code == 422
    assert "require measured load, velocity, and distance" in response.json()["detail"]


def test_update_nonexistent_experiment_returns_404(client: TestClient) -> None:
    response = client.put(
        "/api/v1/experiments/NONEXISTENT-ID",
        json={"notes": "Some notes"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment record not found."


def test_delete_experiment_record_and_verify(client: TestClient) -> None:
    client.post("/api/v1/experiments", json=measured_payload("EXP-TO-DELETE"))

    # Confirm it exists
    assert client.get("/api/v1/experiments/EXP-TO-DELETE").status_code == 200

    # Delete
    response = client.delete("/api/v1/experiments/EXP-TO-DELETE")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Experiment record deleted",
        "experiment_id": "EXP-TO-DELETE",
    }

    # Verify it is gone
    assert client.get("/api/v1/experiments/EXP-TO-DELETE").status_code == 404

    # Deleting again returns 404
    assert client.delete("/api/v1/experiments/EXP-TO-DELETE").status_code == 404


def test_list_experiments_filter_search_sort_and_headers(client: TestClient) -> None:
    client.post("/api/v1/experiments", json=measured_payload("FILTER-ALPHA-01"))
    client.post("/api/v1/plans", json=planned_payload("FILTER-BETA-02"))

    # Test query search
    res_query = client.get("/api/v1/experiments?query=ALPHA")
    assert res_query.status_code == 200
    data_query = res_query.json()
    assert any(r["experiment_id"] == "FILTER-ALPHA-01" for r in data_query)
    assert not any(r["experiment_id"] == "FILTER-BETA-02" for r in data_query)
    assert "X-Total-Count" in res_query.headers

    # Test status filter
    res_status = client.get("/api/v1/experiments?record_status=PLANNED")
    assert res_status.status_code == 200
    assert all(r["record_status"] == "PLANNED" for r in res_status.json())

    # Test sorting
    res_sort = client.get("/api/v1/experiments?sort_by=experiment_id&sort_desc=true")
    assert res_sort.status_code == 200
    ids = [r["experiment_id"] for r in res_sort.json()]
    assert ids == sorted(ids, reverse=True)


def test_export_experiments_with_filters_and_explicit_units(client: TestClient) -> None:
    client.post("/api/v1/experiments", json=measured_payload("EXPORT-MEASURED-01"))
    client.post("/api/v1/plans", json=planned_payload("EXPORT-PLANNED-02"))

    # Export with query filter
    response = client.get("/api/v1/exports/experiments.csv?query=EXPORT-MEASURED-01")
    assert response.status_code == 200
    text = response.text
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    assert len(rows) == 1
    row = rows[0]
    assert row["experiment_id"] == "EXPORT-MEASURED-01"
    assert row["record_status"] == "MEASURED"
    assert float(row["load_n"]) == 10.0
    assert float(row["sliding_velocity_m_per_s"]) == 0.5
    assert float(row["sliding_distance_m"]) == 100.0
    assert float(row["coefficient_of_friction"]) == 0.31


def test_analytics_aggregates_and_kpis(client: TestClient) -> None:
    # Seed known records
    client.post("/api/v1/experiments", json=measured_payload("ANL-EXP-01"))
    client.post("/api/v1/experiments", json=measured_payload("ANL-EXP-02"))
    client.post("/api/v1/plans", json=planned_payload("ANL-PLAN-01"))

    response = client.get("/api/v1/analytics")
    assert response.status_code == 200
    data = response.json()

    kpis = data["kpis"]
    assert kpis["total_records"] >= 3
    assert kpis["measured_records"] >= 2
    assert kpis["planned_records"] >= 1
    assert kpis["distinct_materials_count"] >= 1
    assert kpis["records_with_cof"] >= 2

    # Check COF distribution
    cof_dist = data["cof_distribution"]
    assert cof_dist["has_data"] is True
    assert cof_dist["observation_count"] >= 2
    assert cof_dist["stats"]["mean"] is not None

    # Check relationships
    relationships = data["cof_relationships"]
    assert "scientific_disclaimer" in relationships
    assert len(relationships["points"]) >= 2

    # Check materials
    assert len(data["materials"]) >= 1
    assert "distinct_material_names" in data


def test_analytics_filtering_and_empty_dataset(client: TestClient) -> None:
    client.post("/api/v1/experiments", json=measured_payload("ANL-FILTER-01"))

    # Filter for non-existent material
    response = client.get("/api/v1/analytics?material_system=NON_EXISTENT_MATERIAL_XYZ")
    assert response.status_code == 200
    data = response.json()
    assert data["kpis"]["total_records"] == 0
    assert data["cof_distribution"]["has_data"] is False
    assert data["cof_relationships"]["has_sufficient_data"] is False
    assert len(data["materials"]) == 0


def test_analytics_date_filter_validation(client: TestClient) -> None:
    # Invalid date range: date_from > date_to
    response = client.get("/api/v1/analytics?date_from=2026-12-31&date_to=2026-01-01")
    assert response.status_code == 422
    assert "date_from must not be after date_to" in response.json()["detail"]


def test_analytics_incompatible_wear_units_not_combined(client: TestClient) -> None:
    # Seed record with wear
    p1 = measured_payload("ANL-WEAR-01")
    p1["measurements"]["wear_measurement"] = {
        "value": 1.2e-5,
        "unit_as_recorded": "mm3/N-m",
    }
    p1["measurements"]["wear_measurement_name_as_recorded"] = "specific wear rate"

    p2 = measured_payload("ANL-WEAR-02")
    p2["measurements"]["wear_measurement"] = {
        "value": 4.5,
        "unit_as_recorded": "mm3",
    }
    p2["measurements"]["wear_measurement_name_as_recorded"] = "wear volume loss"

    client.post("/api/v1/experiments", json=p1)
    client.post("/api/v1/experiments", json=p2)

    response = client.get("/api/v1/analytics")
    assert response.status_code == 200
    wear_dist = response.json()["wear_distribution"]
    assert wear_dist["has_data"] is True

    # Groups must not combine mm3/N-m and mm3
    units = [g["unit"] for g in wear_dist["groups"]]
    assert "mm3/N-m" in units
    assert "mm3" in units
    assert len(wear_dist["groups"]) >= 2


def test_import_history_endpoint_lists_persisted_batches(client: TestClient) -> None:
    # Initially history may be empty or contain past fixtures
    initial_history = client.get("/api/v1/imports/history").json()
    assert isinstance(initial_history, list)

    # Commit a batch
    content = template_csv([planned_csv_row("HIST-IMPORT-01")])
    digest = hashlib.sha256(content).hexdigest()
    imported = client.post(
        "/api/v1/imports/confirm",
        files={"file": ("batch_history_test.csv", content, "text/csv")},
        data={"expected_sha256": digest, "confirmation": "true"},
    )
    assert imported.status_code == 200

    # Query history
    history = client.get("/api/v1/imports/history").json()
    assert len(history) >= 1
    latest = history[0]
    assert latest["sha256"] == digest
    assert latest["filename"] == "batch_history_test.csv"
    assert latest["row_count"] == 1
    assert latest["validation_outcome"] == "VALID"
    assert "created_at_utc" in latest


def test_preview_duplicate_detection_and_row_breakdown(client: TestClient) -> None:
    # Seed an experiment ID
    client.post("/api/v1/experiments", json=planned_payload("EXISTING-EXP-ID"))

    # Prepare CSV containing: 1 existing ID, 1 intra-file duplicate pair, 1 fresh ID
    rows = [
        planned_csv_row("EXISTING-EXP-ID"),  # collides with DB
        planned_csv_row("INTRA-DUP-01"),
        planned_csv_row("INTRA-DUP-01"),     # collides within file
        planned_csv_row("FRESH-PLAN-01"),    # clean
    ]
    content = template_csv(rows)

    preview = client.post(
        "/api/v1/imports/preview",
        files={"file": ("duplicate_check.csv", content, "text/csv")},
    )
    assert preview.status_code == 200
    data = preview.json()

    assert data["row_count"] == 4
    assert data["duplicate_rows"] == 3
    assert data["accepted_rows"] == 1
    assert "EXISTING-EXP-ID" in data["duplicate_experiment_ids"]
    assert "INTRA-DUP-01" in data["duplicate_experiment_ids"]
    assert data["can_confirm_import"] is False  # Cannot confirm import with duplicate collisions
    assert any("DUPLICATE_EXPERIMENT_IDS" in w["code"] for w in data["warnings"])


def test_import_encoding_fallback_utf8_bom_and_latin1(client: TestClient) -> None:
    # 1. UTF-8 with BOM (\xef\xbb\xbf)
    row_text = template_csv([planned_csv_row("BOM-PLAN-01")]).decode("utf-8")
    bom_content = b"\xef\xbb\xbf" + row_text.encode("utf-8")

    preview_bom = client.post(
        "/api/v1/imports/preview",
        files={"file": ("bom_test.csv", bom_content, "text/csv")},
    )
    assert preview_bom.status_code == 200
    assert preview_bom.json()["valid"] is True
    assert preview_bom.json()["row_count"] == 1

    # 2. Latin-1 encoded content with accented notes
    latin1_row = planned_csv_row("LATIN1-PLAN-02")
    latin1_row["notes"] = "Test café résumé"
    latin1_text = template_csv([latin1_row]).decode("utf-8")
    latin1_bytes = latin1_text.encode("latin-1")

    preview_latin1 = client.post(
        "/api/v1/imports/preview",
        files={"file": ("latin1_test.csv", latin1_bytes, "text/csv")},
    )
    assert preview_latin1.status_code == 200
    assert preview_latin1.json()["row_count"] == 1


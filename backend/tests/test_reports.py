from __future__ import annotations

import csv
import io
import pytest
from fastapi.testclient import TestClient


def sample_measured_experiment() -> dict[str, object]:
    return {
        "experiment_id": "EXP-REP-001",
        "record_status": "MEASURED",
        "material_system_as_recorded": "Carbon-Fibre:Epoxy",
        "composition_as_recorded": "CF 60% vol, Epoxy 40%",
        "composition_source_reference": "LabBook-2026-p14",
        "replicate_group_id": "GRP-ALPHA-1",
        "measured_conditions": {
            "load_n": 15.0,
            "sliding_velocity_m_per_s": 0.5,
            "sliding_distance_m": 250.0,
            "test_duration_min": 8.33,
        },
        "measurements": {
            "coefficient_of_friction": {
                "value": 0.285,
                "unit_as_recorded": "dimensionless",
            },
            "wear_measurement_name_as_recorded": "Specific Wear Rate",
            "wear_measurement": {
                "value": 4.12e-6,
                "unit_as_recorded": "mm3/N.m",
            },
        },
        "source_artifact": "screening_runs_oct2026.csv",
        "source_location": "Row 14",
        "operator": "Dr. D. Prasath",
        "instrument_id": "TRIBOMETER-01",
        "experiment_date": "2026-10-15",
        "notes": "Verified baseline run under ambient temperature.",
    }


def sample_planned_experiment() -> dict[str, object]:
    return {
        "experiment_id": "PLAN-REP-001",
        "record_status": "PLANNED",
        "planned_by": "Researcher K.",
        "material_system_as_recorded": "Carbon-Fibre:Epoxy",
        "composition_as_recorded": "CF 65% vol, Epoxy 35%",
        "composition_source_reference": "Screening Matrix Rev 2",
        "planned_conditions": {
            "load_n": 20.0,
            "sliding_velocity_m_per_s": 1.0,
            "sliding_distance_m": 500.0,
            "test_duration_min": 16.67,
        },
        "notes": "Prospective candidate for physical validation.",
    }


@pytest.fixture(autouse=True)
def setup_sample_records(client: TestClient) -> None:
    # Seed one measured experiment and one planned experiment
    resp1 = client.post("/api/v1/experiments", json=sample_measured_experiment())
    assert resp1.status_code in (201, 409), resp1.text

    resp2 = client.post("/api/v1/plans", json=sample_planned_experiment())
    assert resp2.status_code in (201, 409), resp2.text


def test_export_single_experiment_pdf_measured(client: TestClient) -> None:
    response = client.get("/api/v1/reports/experiment/EXP-REP-001/pdf")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert "attachment" in response.headers["Content-Disposition"]
    assert "EXP-REP-001" in response.headers["Content-Disposition"]

    content = response.content
    assert content.startswith(b"%PDF"), "Response must be valid PDF bytes"
    assert len(content) > 1500


def test_export_single_experiment_pdf_planned(client: TestClient) -> None:
    response = client.get("/api/v1/reports/experiment/PLAN-REP-001/pdf")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert "attachment" in response.headers["Content-Disposition"]
    assert "PLAN-REP-001" in response.headers["Content-Disposition"]

    content = response.content
    assert content.startswith(b"%PDF"), "Response must be valid PDF bytes"
    assert len(content) > 1500


def test_export_single_experiment_pdf_404(client: TestClient) -> None:
    response = client.get("/api/v1/reports/experiment/NON-EXISTENT-ID/pdf")
    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment record not found."


def test_export_registry_pdf_with_filters(client: TestClient) -> None:
    # 1. All records
    response = client.get("/api/v1/reports/experiments/pdf")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")

    # 2. Filtered by status
    response_meas = client.get("/api/v1/reports/experiments/pdf?status=MEASURED")
    assert response_meas.status_code == 200
    assert response_meas.content.startswith(b"%PDF")

    # 3. Filtered with 0 results
    response_empty = client.get("/api/v1/reports/experiments/pdf?material_system=NonExistentMaterialXYZ")
    assert response_empty.status_code == 200
    assert response_empty.content.startswith(b"%PDF")
    assert len(response_empty.content) > 1000


def test_export_registry_csv_with_explicit_units(client: TestClient) -> None:
    response = client.get("/api/v1/reports/experiments/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["Content-Type"]
    assert "attachment" in response.headers["Content-Disposition"]

    content = response.text
    reader = csv.DictReader(io.StringIO(content))
    fieldnames = reader.fieldnames or []

    # Verify explicit engineering units are present in column names
    assert "normal_load_n" in fieldnames
    assert "sliding_velocity_mps" in fieldnames
    assert "sliding_distance_m" in fieldnames
    assert "coefficient_of_friction" in fieldnames
    assert "wear_measurement_unit" in fieldnames
    assert "record_status" in fieldnames
    assert "import_sha256" in fieldnames

    rows = list(reader)
    assert len(rows) >= 2
    statuses = {r["record_status"] for r in rows}
    assert "MEASURED" in statuses
    assert "PLANNED" in statuses


def test_export_analytics_pdf_and_csv(client: TestClient) -> None:
    # 1. Analytics PDF
    response_pdf = client.get("/api/v1/reports/analytics/pdf")
    assert response_pdf.status_code == 200
    assert response_pdf.headers["Content-Type"] == "application/pdf"
    assert response_pdf.content.startswith(b"%PDF")
    assert len(response_pdf.content) > 2000

    # 2. Analytics CSV
    response_csv = client.get("/api/v1/reports/analytics/csv")
    assert response_csv.status_code == 200
    assert "text/csv" in response_csv.headers["Content-Type"]
    csv_text = response_csv.text
    assert "metric_name,value,unit_or_basis" in csv_text
    assert "total_records" in csv_text
    assert "measured_records" in csv_text
    assert "planned_records" in csv_text


def test_export_models_report_pdf(client: TestClient) -> None:
    response = client.get("/api/v1/reports/models/pdf")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert "AI-TriboTwin-Model-Evaluation-Provenance.pdf" in response.headers["Content-Disposition"]
    assert response.content.startswith(b"%PDF")
    assert len(response.content) > 5000

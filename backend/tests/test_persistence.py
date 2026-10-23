from __future__ import annotations

import csv
import hashlib
import io
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.util.exc import CommandError
from app.db.session import get_db
from app.db.models import ExperimentRecord
from app.main import app
from app.services.validation import INTAKE_COLUMNS
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def migration_config(database_url: str) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def make_sqlite_engine(path: Path) -> tuple[str, Engine]:
    database_url = f"sqlite+pysqlite:///{path.as_posix()}"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    return database_url, engine


def install_database_override(engine: Engine) -> None:
    test_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db() -> Generator[Session, None, None]:
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db


def planned_csv(experiment_id: str) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=INTAKE_COLUMNS)
    writer.writeheader()
    writer.writerow(
        {
            **{column: "" for column in INTAKE_COLUMNS},
            "record_status": "PLANNED",
            "experiment_id": experiment_id,
            "planned_by": "Integration test",
            "material_system_as_recorded": "Candidate as proposed",
            "composition_as_recorded": "Awaiting qualified source confirmation",
            "planned_load_N": "10",
            "planned_sliding_velocity_m_per_s": "0.5",
            "planned_sliding_distance_m": "100",
            "planned_test_duration_min": "10",
        }
    )
    return output.getvalue().encode("utf-8")


def measured_record(experiment_id: str) -> dict[str, object]:
    return {
        "experiment_id": experiment_id,
        "record_status": "MEASURED",
        "material_system_as_recorded": "Material as recorded by the lab",
        "composition_as_recorded": "Composition verified in lab record",
        "composition_source_reference": "lab-notebook/page-12",
        "replicate_group_id": "IT-BATCH-1",
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
        "source_artifact": "integration-fixture.csv",
        "source_location": "run IT-001",
        "operator": "Integration test",
        "instrument_id": "TEST-POD",
        "experiment_date": "2026-10-10",
    }


def planned_record(experiment_id: str) -> dict[str, object]:
    return {
        "experiment_id": experiment_id,
        "record_status": "PLANNED",
        "planned_by": "Integration test",
        "material_system_as_recorded": "Candidate as proposed",
        "composition_as_recorded": "Awaiting qualified source confirmation",
        "planned_conditions": {
            "load_n": 10,
            "sliding_velocity_m_per_s": 0.5,
            "sliding_distance_m": 100,
            "test_duration_min": 10,
        },
    }


def test_migrated_database_workflows_persist_after_api_restart(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url, first_engine = make_sqlite_engine(tmp_path / "app.sqlite3")
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = migration_config(database_url)
    command.upgrade(config, "head")
    command.upgrade(config, "head")

    try:
        with first_engine.connect() as connection:
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "20261010_0002"
        install_database_override(first_engine)
        with TestClient(app) as first_client:
            assert first_client.get("/api/v1/health").json() == {
                "status": "ok",
                "database": "ok",
            }
            assert all(
                target["status"] == "BLOCKED"
                for target in first_client.get("/api/v1/readiness").json()["targets"]
            )

            import_bytes = planned_csv("IT-PLAN-IMPORTED")
            import_sha256 = hashlib.sha256(import_bytes).hexdigest()
            preview = first_client.post(
                "/api/v1/imports/preview",
                files={"file": ("planned-record.csv", import_bytes, "text/csv")},
            )
            assert preview.status_code == 200
            assert preview.json()["can_confirm_import"] is True
            assert first_client.get("/api/v1/experiments").json() == []

            malformed = first_client.post(
                "/api/v1/imports/preview",
                files={"file": ("malformed.csv", b"not,a,template\nx,y,z\n", "text/csv")},
            )
            assert malformed.status_code == 200
            assert malformed.json()["can_confirm_import"] is False

            imported = first_client.post(
                "/api/v1/imports/confirm",
                files={"file": ("planned-record.csv", import_bytes, "text/csv")},
                data={"expected_sha256": import_sha256, "confirmation": "true"},
            )
            assert imported.status_code == 200
            assert imported.json()["records_imported"] == 1

            measured = measured_record("IT-RUN-MEASURED")
            created = first_client.post("/api/v1/experiments", json=measured)
            assert created.status_code == 201
            assert created.json()["record_status"] == "MEASURED"
            assert first_client.get("/api/v1/experiments/IT-RUN-MEASURED").json()[
                "source_artifact"
            ] == "integration-fixture.csv"

            plan = first_client.post(
                "/api/v1/plans",
                json=planned_record("IT-PLAN-DIRECT"),
            )
            assert plan.status_code == 201
            assert plan.json()["record_status"] == "PLANNED"
            assert plan.json()["measurements"] == {"wear_measurement_name_as_recorded": ""}

            invalid = measured_record("IT-RUN-INVALID")
            invalid["measured_conditions"] = {"load_n": 10}
            assert first_client.post("/api/v1/experiments", json=invalid).status_code == 422
            duplicate = first_client.post("/api/v1/experiments", json=measured)
            assert duplicate.status_code == 409
            assert duplicate.json()["detail"]["code"] == "DUPLICATE_EXPERIMENT_ID"
            duplicate_import = first_client.post(
                "/api/v1/imports/confirm",
                files={"file": ("planned-record.csv", import_bytes, "text/csv")},
                data={"expected_sha256": import_sha256, "confirmation": "true"},
            )
            assert duplicate_import.status_code == 409

            prediction = first_client.post("/api/v1/predictions/TARGET-COF")
            optimization = first_client.post(
                "/api/v1/optimizations",
                params=[("objective_ids", "TARGET-COF"), ("objective_ids", "TARGET-WEAR")],
            )
            assert prediction.status_code == 409
            assert prediction.json()["code"] == "SCIENTIFIC_READINESS_BLOCKED"
            assert optimization.status_code == 409
            assert optimization.json()["code"] == "SCIENTIFIC_READINESS_BLOCKED"

        app.dependency_overrides.clear()
        first_engine.dispose()

        _, restarted_engine = make_sqlite_engine(tmp_path / "app.sqlite3")
        install_database_override(restarted_engine)
        with TestClient(app) as restarted_client:
            records = restarted_client.get("/api/v1/experiments").json()
            assert {record["experiment_id"] for record in records} == {
                "IT-PLAN-IMPORTED",
                "IT-RUN-MEASURED",
                "IT-PLAN-DIRECT",
            }
            assert restarted_client.get("/api/v1/experiments/IT-PLAN-IMPORTED").json()[
                "record_status"
            ] == "PLANNED"
            assert restarted_client.get("/api/v1/experiments/count").json() == {
                "PLANNED": 2,
                "MEASURED": 1,
                "total": 3,
            }
            assert restarted_client.post(
                "/api/v1/imports/confirm",
                files={"file": ("planned-record.csv", import_bytes, "text/csv")},
                data={"expected_sha256": import_sha256, "confirmation": "true"},
            ).status_code == 409
        app.dependency_overrides.clear()
        restarted_engine.dispose()
    finally:
        app.dependency_overrides.clear()
        first_engine.dispose()


def test_migrated_database_rejects_invalid_record_status_and_blank_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url, engine = make_sqlite_engine(tmp_path / "constraints.sqlite3")
    monkeypatch.setenv("DATABASE_URL", database_url)
    command.upgrade(migration_config(database_url), "head")
    invalid_records = (
        ExperimentRecord(
            experiment_id="INVALID-STATUS",
            record_status="UNKNOWN",
            material_system_as_recorded="Test-only fixture",
        ),
        ExperimentRecord(
            experiment_id="   ",
            record_status="PLANNED",
            material_system_as_recorded="Test-only fixture",
        ),
        ExperimentRecord(
            experiment_id="BLANK-MATERIAL",
            record_status="PLANNED",
            material_system_as_recorded="   ",
        ),
    )
    try:
        with Session(engine) as db:
            for record in invalid_records:
                db.add(record)
                with pytest.raises(IntegrityError):
                    db.commit()
                db.rollback()
            assert db.scalar(text("SELECT COUNT(*) FROM experiment_records")) == 0
    finally:
        engine.dispose()


def test_migration_failure_is_reported_without_mutating_test_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "migration-failure.sqlite3"
    database_url, engine = make_sqlite_engine(database_path)
    monkeypatch.setenv("DATABASE_URL", database_url)
    try:
        with pytest.raises(CommandError, match="Can't locate revision"):
            command.upgrade(migration_config(database_url), "missing-test-revision")
        with engine.connect() as connection:
            tables = connection.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
                )
            ).scalars().all()
        assert "experiment_records" not in tables
        assert "import_artifacts" not in tables
    finally:
        engine.dispose()


def test_database_unavailable_health_check_returns_503(tmp_path: Path) -> None:
    unavailable_engine = create_engine(
        f"sqlite+pysqlite:///{(tmp_path / 'missing-directory' / 'unavailable.sqlite3').as_posix()}",
        connect_args={"check_same_thread": False},
    )
    install_database_override(unavailable_engine)
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/health")
        assert response.status_code == 503
        assert response.json()["detail"]["database"] == "unavailable"
    finally:
        app.dependency_overrides.clear()
        unavailable_engine.dispose()

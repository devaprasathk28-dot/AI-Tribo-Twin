from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Integer,
    JSON,
    LargeBinary,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExperimentRecord(Base):
    __tablename__ = "experiment_records"
    __table_args__ = (
        UniqueConstraint("experiment_id", name="uq_experiment_records_experiment_id"),
        CheckConstraint(
            "record_status IN ('PLANNED', 'MEASURED')",
            name="ck_experiment_records_status",
        ),
        CheckConstraint(
            "length(trim(experiment_id)) > 0",
            name="ck_experiment_records_experiment_id_nonblank",
        ),
        CheckConstraint(
            "length(trim(material_system_as_recorded)) > 0",
            name="ck_experiment_records_material_nonblank",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    record_status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    material_system_as_recorded: Mapped[str] = mapped_column(String(240), nullable=False)
    planned_by: Mapped[str] = mapped_column(String(240), nullable=False, default="")
    composition_as_recorded: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    composition_source_reference: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    replicate_group_id: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    planned_conditions: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    measured_conditions: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    measurements: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    instrument_id: Mapped[str] = mapped_column(String(240), nullable=False, default="")
    operator: Mapped[str] = mapped_column(String(240), nullable=False, default="")
    experiment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_artifact: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    source_location: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    notes: Mapped[str] = mapped_column(String(4000), nullable=False, default="")
    recorded_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    created_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    import_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="", index=True)


class ImportArtifact(Base):
    __tablename__ = "import_artifacts"
    __table_args__ = (
        CheckConstraint("length(sha256) = 64", name="ck_import_artifacts_sha256_length"),
        CheckConstraint("size_bytes > 0", name="ck_import_artifacts_size_positive"),
        CheckConstraint("row_count > 0", name="ck_import_artifacts_rows_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False, default="text/csv")
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    validation_report: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    original_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

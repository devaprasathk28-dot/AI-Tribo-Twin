"""Create experiments and original import artifacts.

Revision ID: 20261010_0001
Revises:
Create Date: 2026-10-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261010_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "experiment_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("experiment_id", sa.String(length=120), nullable=False),
        sa.Column("record_status", sa.String(length=20), nullable=False),
        sa.Column("material_system_as_recorded", sa.String(length=240), nullable=False),
        sa.Column("planned_by", sa.String(length=240), nullable=False),
        sa.Column("composition_as_recorded", sa.String(length=1000), nullable=False),
        sa.Column("composition_source_reference", sa.String(length=1000), nullable=False),
        sa.Column("replicate_group_id", sa.String(length=160), nullable=False),
        sa.Column("planned_conditions", sa.JSON(), nullable=False),
        sa.Column("measured_conditions", sa.JSON(), nullable=False),
        sa.Column("measurements", sa.JSON(), nullable=False),
        sa.Column("instrument_id", sa.String(length=240), nullable=False),
        sa.Column("operator", sa.String(length=240), nullable=False),
        sa.Column("experiment_date", sa.Date(), nullable=True),
        sa.Column("source_artifact", sa.String(length=1000), nullable=False),
        sa.Column("source_location", sa.String(length=1000), nullable=False),
        sa.Column("notes", sa.String(length=4000), nullable=False),
        sa.Column("recorded_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("import_sha256", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("experiment_id", name="uq_experiment_records_experiment_id"),
    )
    op.create_index("ix_experiment_records_experiment_id", "experiment_records", ["experiment_id"])
    op.create_index("ix_experiment_records_record_status", "experiment_records", ["record_status"])
    op.create_index("ix_experiment_records_import_sha256", "experiment_records", ["import_sha256"])

    op.create_table(
        "import_artifacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("validation_report", sa.JSON(), nullable=False),
        sa.Column("original_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sha256"),
    )
    op.create_index("ix_import_artifacts_sha256", "import_artifacts", ["sha256"])


def downgrade() -> None:
    op.drop_index("ix_import_artifacts_sha256", table_name="import_artifacts")
    op.drop_table("import_artifacts")
    op.drop_index("ix_experiment_records_import_sha256", table_name="experiment_records")
    op.drop_index("ix_experiment_records_record_status", table_name="experiment_records")
    op.drop_index("ix_experiment_records_experiment_id", table_name="experiment_records")
    op.drop_table("experiment_records")

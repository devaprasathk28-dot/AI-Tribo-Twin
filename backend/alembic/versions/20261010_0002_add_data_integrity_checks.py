"""Add database-level checks for experiment and import records.

Revision ID: 20261010_0002
Revises: 20261010_0001
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20261010_0002"
down_revision: Union[str, None] = "20261010_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("experiment_records") as batch_op:
        batch_op.create_check_constraint(
            "ck_experiment_records_status",
            "record_status IN ('PLANNED', 'MEASURED')",
        )
        batch_op.create_check_constraint(
            "ck_experiment_records_experiment_id_nonblank",
            "length(trim(experiment_id)) > 0",
        )
        batch_op.create_check_constraint(
            "ck_experiment_records_material_nonblank",
            "length(trim(material_system_as_recorded)) > 0",
        )

    with op.batch_alter_table("import_artifacts") as batch_op:
        batch_op.create_check_constraint(
            "ck_import_artifacts_sha256_length",
            "length(sha256) = 64",
        )
        batch_op.create_check_constraint(
            "ck_import_artifacts_size_positive",
            "size_bytes > 0",
        )
        batch_op.create_check_constraint(
            "ck_import_artifacts_rows_positive",
            "row_count > 0",
        )


def downgrade() -> None:
    with op.batch_alter_table("import_artifacts") as batch_op:
        batch_op.drop_constraint("ck_import_artifacts_rows_positive", type_="check")
        batch_op.drop_constraint("ck_import_artifacts_size_positive", type_="check")
        batch_op.drop_constraint("ck_import_artifacts_sha256_length", type_="check")

    with op.batch_alter_table("experiment_records") as batch_op:
        batch_op.drop_constraint("ck_experiment_records_material_nonblank", type_="check")
        batch_op.drop_constraint("ck_experiment_records_experiment_id_nonblank", type_="check")
        batch_op.drop_constraint("ck_experiment_records_status", type_="check")

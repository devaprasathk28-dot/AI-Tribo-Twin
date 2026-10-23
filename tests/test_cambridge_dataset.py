from __future__ import annotations

import numpy as np
import pytest

from src.data.cambridge import (
    GROUP_COLUMN,
    LEAKAGE_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    TARGET_COLUMN,
    CambridgeDataError,
    build_towtool_dataset,
    load_towtool_measurements,
    sha256_file,
)


@pytest.fixture(scope="module")
def dataset():
    return load_towtool_measurements()


def test_loader_returns_traceable_tidy_table(dataset) -> None:
    frame = dataset.measurements
    assert len(frame) == 140
    assert frame[GROUP_COLUMN].nunique() == 10
    assert set(frame["tow_type"]) == {"T700-12k-60E", "T700-12k-50C"}
    assert frame.groupby(GROUP_COLUMN).size().eq(14).all()
    for column in (*MODEL_FEATURE_COLUMNS, TARGET_COLUMN, GROUP_COLUMN, "step"):
        assert column in frame.columns


def test_target_is_finite_and_leakage_columns_are_excluded_from_features(dataset) -> None:
    frame = dataset.measurements
    assert np.isfinite(frame[TARGET_COLUMN].to_numpy(dtype=float)).all()
    for column in LEAKAGE_COLUMNS:
        assert column in frame.columns
        assert column not in MODEL_FEATURE_COLUMNS
    assert TARGET_COLUMN not in MODEL_FEATURE_COLUMNS


def test_metadata_records_source_hash_and_scope(dataset) -> None:
    metadata = dataset.metadata
    assert metadata["workbook_sha256"] == sha256_file(
        __import__("src.data.cambridge", fromlist=["TOW_TOOL_WORKBOOK"]).TOW_TOOL_WORKBOOK
    )
    assert metadata["observation_count"] == 140
    assert metadata["test_run_count"] == 10
    assert "carbon" in str(metadata["material_domain"]).lower()
    assert metadata["caveats"]


def test_build_persists_dataset_and_provenance(tmp_path) -> None:
    table_path, provenance_path = build_towtool_dataset(tmp_path)

    assert table_path.is_file()
    assert provenance_path.is_file()
    import json

    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    assert provenance["measurements_sha256"] == sha256_file(table_path)
    assert provenance["observation_count"] == 140


def test_validate_rejects_too_few_groups(dataset) -> None:
    from src.data.cambridge import _validate_dataset

    frame = dataset.measurements
    truncated = frame[frame[GROUP_COLUMN].isin(sorted(frame[GROUP_COLUMN].unique())[:5])]
    with pytest.raises(CambridgeDataError, match="at least 10 independent test runs"):
        _validate_dataset(truncated, min_groups=10)

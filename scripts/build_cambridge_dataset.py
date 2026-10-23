"""Build the processed Cambridge tow-on-tool dataset and report its provenance.

Run from the repository root:

    .\\.venv\\Scripts\\python.exe -m scripts.build_cambridge_dataset
"""

from __future__ import annotations

import json
from pathlib import Path

from src.data.cambridge import (
    CAMBRIDGE_PROCESSED_DIR,
    TARGET_COLUMN,
    build_towtool_dataset,
    load_towtool_measurements,
)
from src.data.workflow import RAW_DATA_PATH, verify_protected_raw_data


def main() -> None:
    rows, columns, raw_digest = verify_protected_raw_data()
    print(f"protected raw CSV: {RAW_DATA_PATH.name} {rows}x{columns}")
    print(f"protected raw CSV SHA-256: {raw_digest}")

    dataset = load_towtool_measurements()
    frame = dataset.measurements
    print(f"tow-on-tool observations: {len(frame)}")
    print(f"tow-on-tool independent test runs: {frame['test_run_id'].nunique()}")
    print(f"target column: {TARGET_COLUMN}")
    print(f"target range: {frame[TARGET_COLUMN].min():.6f} .. {frame[TARGET_COLUMN].max():.6f}")
    print(f"workbook SHA-256: {dataset.metadata['workbook_sha256']}")

    table_path, provenance_path = build_towtool_dataset(CAMBRIDGE_PROCESSED_DIR)
    print(f"wrote: {_relative(table_path)}")
    print(f"wrote: {_relative(provenance_path)}")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    print(json.dumps(
        {
            "measurements_sha256": provenance["measurements_sha256"],
            "observation_count": provenance["observation_count"],
            "test_run_count": provenance["test_run_count"],
        },
        indent=2,
    ))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()

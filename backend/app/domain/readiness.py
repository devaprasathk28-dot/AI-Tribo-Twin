from __future__ import annotations

import csv
from pathlib import Path

from app.core.config import DATA_VALIDATION
from app.schemas.experiments import ReadinessItem


READINESS_WARNING = (
    "The current experimental source is not cleared for supervised training. "
    "Transcription verification does not establish paper-to-run mapping or independent experiment groups."
)


def load_target_readiness(path: Path | None = None) -> list[ReadinessItem]:
    readiness_path = path or DATA_VALIDATION / "TARGET_READINESS.csv"
    if not readiness_path.is_file():
        raise FileNotFoundError(f"Target-readiness register not found: {readiness_path}")
    with readiness_path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    return [
        ReadinessItem(
            target_id=row.get("target_id", ""),
            target_name=row.get("target_name", row.get("target_id", "")),
            status=row.get("ml_readiness", "UNKNOWN"),
            evidence=row.get("evidence", ""),
            required_evidence=row.get("required_evidence_to_unlock", ""),
        )
        for row in rows
    ]


def target_gate(target_id: str) -> ReadinessItem | None:
    return next((item for item in load_target_readiness() if item.target_id == target_id), None)

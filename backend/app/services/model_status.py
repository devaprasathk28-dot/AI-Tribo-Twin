from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from app.core.config import EXTERNAL_MODEL_DIR, MODEL_DEMO_DIR
from app.domain.readiness import load_target_readiness

from src.models.external_cof import verify_external_artifact_bundle
from src.models.training import verify_model_artifact_bundle

DEMO_ARTIFACT_DIR = MODEL_DEMO_DIR
DEMO_REPORT_PATH = DEMO_ARTIFACT_DIR / "report.json"
DEMO_PLOT_PATH = DEMO_ARTIFACT_DIR / "predictions_vs_observations.png"

EXTERNAL_ARTIFACT_DIR = EXTERNAL_MODEL_DIR
EXTERNAL_REPORT_PATH = EXTERNAL_ARTIFACT_DIR / "report.json"
EXTERNAL_MANIFEST_PATH = EXTERNAL_ARTIFACT_DIR / "manifest.json"
EXTERNAL_PLOT_PATH = EXTERNAL_ARTIFACT_DIR / "predictions_vs_observations.png"

_EXTERNAL_COUNT_KEYS = (
    "observation_count",
    "training_rows",
    "holdout_rows",
    "training_groups",
    "holdout_groups",
)


def _check_external_report(report: dict[str, Any]) -> None:
    if (
        report.get("status") != "EVALUATED_EXTERNAL_COF"
        or report.get("source_kind") != "external"
        or report.get("is_ai_tribotwin_model") is not False
        or report.get("model_id") != "TOW-TOOL-COF-CAMBRIDGE"
        or not isinstance(report.get("material_domain"), str)
        or not isinstance(report.get("interpretation"), str)
    ):
        raise ValueError("Saved external model report failed provenance checks.")
    for count_key in _EXTERNAL_COUNT_KEYS:
        count = report.get(count_key)
        if not isinstance(count, int) or count < 1:
            raise ValueError(f"External model report has invalid {count_key}.")
    for key in ("holdout_metrics", "baseline_metrics"):
        metrics = report.get(key)
        if not isinstance(metrics, dict) or any(
            not isinstance(metrics.get(name), (int, float)) or not math.isfinite(metrics[name])
            for name in ("mae", "rmse", "r2")
        ):
            raise ValueError(f"External model report has invalid {key}.")


def get_external_model_status(artifact_dir: Path | None = None) -> dict[str, Any]:
    directory = artifact_dir or EXTERNAL_ARTIFACT_DIR
    report_path = directory / "report.json"
    manifest_path = directory / "manifest.json"
    plot_path = directory / "predictions_vs_observations.png"
    status: dict[str, Any] = {
        "status": "NOT_RUN",
        "plot_available": plot_path.is_file(),
        "report": None,
    }
    if not report_path.is_file() or not manifest_path.is_file():
        return status
    report = verify_external_artifact_bundle(directory)
    _check_external_report(report)
    status["status"] = "EVALUATED_EXTERNAL_COF"
    status["report"] = report
    return status


def get_model_status() -> dict[str, Any]:
    targets = [target.model_dump() for target in load_target_readiness()]
    response: dict[str, Any] = {
        "demo_status": "NOT_RUN",
        "training_source": "synthetic_fixture_only",
        "experimental_model_trained": False,
        "experimental_targets": targets,
        "demo_report": None,
        "plot_available": DEMO_PLOT_PATH.is_file(),
        "external_model": get_external_model_status(),
    }
    if not DEMO_REPORT_PATH.is_file():
        return response

    report = verify_model_artifact_bundle(DEMO_ARTIFACT_DIR)
    if (
        not isinstance(report, dict)
        or report.get("status") != "EVALUATED_SYNTHETIC_DEMO"
        or report.get("source_kind") != "synthetic"
        or report.get("synthetic_only") is not True
        or report.get("experimental_results") is not False
        or report.get("target_id") != "SYNTHETIC-DEMO"
        or not isinstance(report.get("selected_model"), str)
        or not isinstance(report.get("interpretation"), str)
    ):
        raise ValueError("Saved model report does not meet synthetic-demo provenance checks.")
    for count_key in ("training_rows", "holdout_rows", "training_groups", "holdout_groups"):
        count = report.get(count_key)
        if not isinstance(count, int) or count < 1:
            raise ValueError(f"Synthetic model report has invalid {count_key}.")
    metrics = report.get("holdout_metrics")
    if not isinstance(metrics, dict) or any(
        not isinstance(metrics.get(key), (int, float))
        or not math.isfinite(metrics[key])
        for key in ("mae", "rmse", "r2")
    ):
        raise ValueError("Synthetic model report has invalid holdout metrics.")
    response["demo_status"] = "EVALUATED_SYNTHETIC_DEMO"
    response["demo_report"] = report
    return response

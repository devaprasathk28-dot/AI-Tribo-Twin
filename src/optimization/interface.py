"""Fail-closed boundary for future evidence-backed multi-objective optimization."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from src.prediction.interface import prediction_gate


class OptimizationBlockedError(RuntimeError):
    """Raised unless objectives and optimization evidence are explicitly ready."""


def optimize(
    objective_ids: Sequence[str],
    constraints: Mapping[str, object] | None = None,
    *,
    validated_model_evidence: str | None = None,
    validated_constraints_evidence: str | None = None,
) -> list[dict[str, object]]:
    if not objective_ids:
        raise OptimizationBlockedError("At least one evidence-backed objective is required.")
    blocked = [
        f"{target_id}: {prediction_gate(target_id).status}"
        for target_id in objective_ids
        if prediction_gate(target_id).status != "READY"
    ]
    if blocked:
        raise OptimizationBlockedError(
            "Optimization is disabled because target readiness is blocked (" + ", ".join(blocked) + ")."
        )
    if not validated_model_evidence or not validated_constraints_evidence:
        raise OptimizationBlockedError(
            "A validated model evaluation and experimentally defensible constraint evidence are required."
        )
    raise OptimizationBlockedError(
        "No validated optimizer implementation is registered; no candidate or optimum was generated."
    )

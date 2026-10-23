"""Fail-closed boundary for future target-specific prediction models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

from src.data.workflow import load_target_readiness


class PredictionBlockedError(RuntimeError):
    """Raised instead of returning a prediction for an unreleased target."""


class Predictor(Protocol):
    @property
    def target_id(self) -> str:
        """The single readiness-approved target this model predicts."""

    @property
    def model_artifact_reference(self) -> str:
        """Stable location or identifier for the preserved model artifact."""

    @property
    def evaluation_evidence_reference(self) -> str:
        """Reference to a legitimate, leakage-aware evaluation record."""

    def predict(self, inputs: Mapping[str, str]) -> float:
        """Return a prediction only from a separately validated model."""


@dataclass(frozen=True)
class PredictionGate:
    target_id: str
    status: str
    reason: str
    evidence_needed: str


def prediction_gate(target_id: str) -> PredictionGate:
    matches = [row for row in load_target_readiness() if row.get("target_id") == target_id]
    if not matches:
        return PredictionGate(target_id, "BLOCKED", "Target is not in the approved readiness register.", "")
    row = matches[0]
    status = row.get("ml_readiness", "BLOCKED")
    if status != "READY":
        return PredictionGate(
            target_id,
            status,
            row.get("evidence", "Readiness evidence is unavailable."),
            row.get("required_evidence_to_unlock", ""),
        )
    return PredictionGate(target_id, "READY", "Target passed the data-readiness gate.", "")


def predict(
    target_id: str,
    inputs: Mapping[str, str],
    predictor: Predictor | None = None,
) -> float:
    gate = prediction_gate(target_id)
    if gate.status != "READY":
        raise PredictionBlockedError(
            f"{target_id} is {gate.status}: {gate.reason} Required evidence: {gate.evidence_needed}"
        )
    if predictor is None:
        raise PredictionBlockedError(f"No validated predictor is registered for {target_id}.")
    model_target = getattr(predictor, "target_id", "")
    model_artifact = getattr(predictor, "model_artifact_reference", "")
    evaluation_evidence = getattr(predictor, "evaluation_evidence_reference", "")
    if model_target != target_id:
        raise PredictionBlockedError(
            f"Predictor target {model_target!r} does not match requested target {target_id!r}."
        )
    if not model_artifact or not evaluation_evidence:
        raise PredictionBlockedError(
            "Predictor must identify its preserved model artifact and legitimate evaluation evidence."
        )
    return predictor.predict(inputs)

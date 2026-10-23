from __future__ import annotations

import json
import shutil

import pytest
from fastapi.testclient import TestClient

from app.services.model_status import EXTERNAL_ARTIFACT_DIR

PREDICT_URL = "/api/v1/models/external/predict"
CANDIDATE_URL = "/api/v1/models/external/candidates/validate"
RECOMMEND_URL = "/api/v1/models/external/recommendations"

IN_DOMAIN_PAYLOAD: dict[str, float | str] = {
    "normal_load_n": 10.0,
    "nominal_pressure_mpa": 10.0 / 150.0,
    "contact_width_mm": 6.5,
    "contact_area_mm2": 150.0,
    "contact_length_scanned_mm": 1400.0,
    "contact_half_width_a_mm": 3e-5,
    "percent_contact_length": 18.0,
    "tow_type": "T700-12k-60E",
}

requires_bundle = pytest.mark.skipif(
    not (EXTERNAL_ARTIFACT_DIR / "manifest.json").is_file(),
    reason="external model bundle has not been trained",
)


def _post_raw(client: TestClient, body: str):
    return client.post(
        PREDICT_URL, content=body, headers={"content-type": "application/json"}
    )


@requires_bundle
def test_valid_prediction_returns_cof_with_provenance_and_metrics(client: TestClient) -> None:
    response = client.post(PREDICT_URL, json=IN_DOMAIN_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["model_id"] == "TOW-TOOL-COF-CAMBRIDGE"
    assert body["source_kind"] == "external"
    assert body["target"] == "coefficient_of_friction"
    assert isinstance(body["predicted_coefficient_of_friction"], float)
    assert body["domain_status"] == "IN_DOMAIN"
    assert body["out_of_domain_features"] == []
    assert body["composite_targets_trained"] is False
    assert body["metrics"]["holdout_rows"] == 42
    assert body["provenance"]["model_id"] == "TOW-TOOL-COF-CAMBRIDGE"
    assert body["provenance"]["dataset_sha256"]
    assert "no prediction interval" in body["note"].lower()


@requires_bundle
def test_prediction_labels_the_external_domain_and_disclaims_composites(client: TestClient) -> None:
    body = client.post(PREDICT_URL, json=IN_DOMAIN_PAYLOAD).json()

    limitation = body["domain_limitation"].lower()
    assert "cambridge" in limitation
    assert "not a predictor" in limitation
    assert "composite" in limitation
    assert "external" in body["interpretation"].lower()


@requires_bundle
def test_out_of_domain_feature_is_rejected_without_a_prediction(client: TestClient) -> None:
    response = client.post(PREDICT_URL, json={**IN_DOMAIN_PAYLOAD, "normal_load_n": 500.0})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "normal_load_n=500" in detail
    assert "not validated for decision-making" in detail
    assert "predicted_coefficient_of_friction" not in response.json()


@requires_bundle
def test_reported_extreme_load_extrapolation_is_blocked_before_model_scoring(
    client: TestClient, monkeypatch
) -> None:
    from app.services import external_prediction

    def unexpected_score(*args, **kwargs):
        pytest.fail("Out-of-domain input must be rejected before model scoring.")

    monkeypatch.setattr(external_prediction, "_predict", unexpected_score)
    response = client.post(
        PREDICT_URL,
        json={**IN_DOMAIN_PAYLOAD, "normal_load_n": 50010.1},
    )

    assert response.status_code == 422
    assert "50010.1" in response.json()["detail"]
    assert "not validated for decision-making" in response.json()["detail"]
    assert "217" not in response.json()["detail"]


@requires_bundle
def test_below_minimum_feature_is_flagged_as_below_min(client: TestClient) -> None:
    response = client.post(PREDICT_URL, json={**IN_DOMAIN_PAYLOAD, "contact_width_mm": 0.001})

    assert response.status_code == 422
    assert "contact_width_mm=0.001" in response.json()["detail"]


@requires_bundle
def test_prediction_rejects_inconsistent_pressure_load_and_area(client: TestClient) -> None:
    response = client.post(
        PREDICT_URL,
        json={**IN_DOMAIN_PAYLOAD, "nominal_pressure_mpa": 0.1},
    )

    assert response.status_code == 422
    assert "normal_load_n / contact_area_mm2" in response.json()["detail"]


@requires_bundle
def test_candidate_validation_accepts_supported_physical_test_condition(client: TestClient) -> None:
    response = client.post(
        CANDIDATE_URL,
        json={
            "candidates": [
                {"candidate_id": "in-domain", "conditions": IN_DOMAIN_PAYLOAD},
            ]
        },
    )

    assert response.status_code == 200
    body = response.json()
    candidate = body["results"][0]
    assert candidate["accepted_for_physical_testing"] is True
    assert candidate["out_of_domain_features"] == []
    assert "not ranked recommendations" in body["interpretation"]
    assert "predicted_coefficient_of_friction" not in candidate


@requires_bundle
def test_candidate_validation_rejects_out_of_range_and_unsupported_tow(client: TestClient) -> None:
    response = client.post(
        CANDIDATE_URL,
        json={
            "candidates": [
                {
                    "candidate_id": "extreme-load",
                    "conditions": {**IN_DOMAIN_PAYLOAD, "normal_load_n": 50010.1},
                },
                {
                    "candidate_id": "unknown-tow",
                    "conditions": {**IN_DOMAIN_PAYLOAD, "tow_type": "T800-24k"},
                },
            ]
        },
    )

    assert response.status_code == 200
    results = {item["candidate_id"]: item for item in response.json()["results"]}
    assert results["extreme-load"]["accepted_for_physical_testing"] is False
    assert results["extreme-load"]["out_of_domain_features"][0]["feature"] == "normal_load_n"
    assert results["unknown-tow"]["accepted_for_physical_testing"] is False
    assert any("tow_type" in issue for issue in results["unknown-tow"]["issues"])


@requires_bundle
def test_unknown_tow_type_is_rejected(client: TestClient) -> None:
    response = client.post(PREDICT_URL, json={**IN_DOMAIN_PAYLOAD, "tow_type": "T800-24k"})

    assert response.status_code == 422
    assert "tow_type" in response.json()["detail"]


@requires_bundle
def test_missing_feature_is_rejected(client: TestClient) -> None:
    payload = {key: value for key, value in IN_DOMAIN_PAYLOAD.items() if key != "contact_area_mm2"}

    response = client.post(PREDICT_URL, json=payload)

    assert response.status_code == 422


@requires_bundle
def test_extra_feature_is_rejected(client: TestClient) -> None:
    response = client.post(PREDICT_URL, json={**IN_DOMAIN_PAYLOAD, "friction_force_n": 3.2})

    assert response.status_code == 422


@requires_bundle
def test_non_numeric_value_is_rejected(client: TestClient) -> None:
    response = client.post(PREDICT_URL, json={**IN_DOMAIN_PAYLOAD, "percent_contact_length": "18"})

    assert response.status_code == 422


@requires_bundle
@pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_values_are_rejected(client: TestClient, literal: str) -> None:
    payload = {**IN_DOMAIN_PAYLOAD, "normal_load_n": literal}

    response = _post_raw(client, json.dumps(payload))

    assert response.status_code == 422


@requires_bundle
def test_non_positive_value_is_rejected(client: TestClient) -> None:
    response = client.post(PREDICT_URL, json={**IN_DOMAIN_PAYLOAD, "contact_area_mm2": 0})

    assert response.status_code == 422


def test_missing_artifacts_fail_safe_with_503(client: TestClient, monkeypatch, tmp_path) -> None:
    from app.services import external_prediction

    monkeypatch.setattr(external_prediction, "EXTERNAL_ARTIFACT_DIR", tmp_path)

    response = client.post(PREDICT_URL, json=IN_DOMAIN_PAYLOAD)

    assert response.status_code == 503
    assert "provenance" in response.json()["detail"].lower()


@requires_bundle
def test_tampered_model_artifact_fails_safe_with_503(
    client: TestClient, monkeypatch, tmp_path
) -> None:
    from app.services import external_prediction

    bundle = tmp_path / "bundle"
    shutil.copytree(EXTERNAL_ARTIFACT_DIR, bundle)
    model_path = bundle / "model.joblib"
    model_path.write_bytes(model_path.read_bytes() + b"tamper")
    monkeypatch.setattr(external_prediction, "EXTERNAL_ARTIFACT_DIR", bundle)

    response = client.post(PREDICT_URL, json=IN_DOMAIN_PAYLOAD)

    assert response.status_code == 503


def test_composite_targets_remain_blocked_alongside_external_prediction(client: TestClient) -> None:
    blocked = client.post("/api/v1/predictions/TARGET-COF")

    assert blocked.status_code == 409
    assert blocked.json()["code"] == "SCIENTIFIC_READINESS_BLOCKED"
    status = client.get("/api/v1/models/status").json()
    assert status["experimental_model_trained"] is False
    assert all(target["status"] == "BLOCKED" for target in status["experimental_targets"])


@requires_bundle
def test_recommendations_generates_valid_ranked_candidates_within_training_bounds(
    client: TestClient,
) -> None:
    response = client.post(
        RECOMMEND_URL,
        json={
            "tow_type": "T700-12k-60E",
            "num_candidates": 4,
            "target_criterion": "lowest_predicted_cof",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["model_id"] == "TOW-TOOL-COF-CAMBRIDGE"
    assert body["source_kind"] == "external"
    assert body["composite_targets_trained"] is False
    assert "not proven optima" in body["interpretation"].lower()
    assert "no causal relationship" in body["causal_disclaimer"].lower()
    assert "negative r²" in body["reliability_notice"].lower()
    assert len(body["recommendations"]) == 4

    recs = body["recommendations"]
    for i, rec in enumerate(recs):
        assert rec["rank"] == i + 1
        assert rec["is_model_estimate_not_measurement"] is True
        assert isinstance(rec["predicted_coefficient_of_friction"], float)
        assert "candidate condition" in rec["recommendation_label"].lower()
        conds = rec["conditions"]
        assert conds["tow_type"] == "T700-12k-60E"
        assert conds["normal_load_n"] >= 0.07
        assert conds["normal_load_n"] <= 50.0
        # Check nominal pressure consistency
        assert abs(conds["nominal_pressure_mpa"] - (conds["normal_load_n"] / conds["contact_area_mm2"])) < 1e-6

    # Verify ranking by lowest predicted COF
    cofs = [r["predicted_coefficient_of_friction"] for r in recs]
    assert cofs == sorted(cofs)


@requires_bundle
def test_recommendations_rejects_unsupported_tow_type(client: TestClient) -> None:
    response = client.post(
        RECOMMEND_URL,
        json={"tow_type": "T800-24k", "num_candidates": 3},
    )

    assert response.status_code == 422
    assert "tow_type" in response.json()["detail"]


@requires_bundle
def test_recommendations_rejects_out_of_bound_load_range(client: TestClient) -> None:
    # Test below min load
    resp_low = client.post(
        RECOMMEND_URL,
        json={"tow_type": "T700-12k-50C", "min_load_n": 0.001},
    )
    assert resp_low.status_code == 422
    assert "outside the training range" in resp_low.json()["detail"]

    # Test extreme high load
    resp_high = client.post(
        RECOMMEND_URL,
        json={"tow_type": "T700-12k-50C", "max_load_n": 50010.1},
    )
    assert resp_high.status_code == 422
    assert "outside the training range" in resp_high.json()["detail"]


@requires_bundle
def test_recommendations_rejects_inverted_load_range(client: TestClient) -> None:
    response = client.post(
        RECOMMEND_URL,
        json={"tow_type": "T700-12k-50C", "min_load_n": 35.0, "max_load_n": 10.0},
    )

    assert response.status_code == 422
    assert "less than" in response.json()["detail"]


@requires_bundle
def test_candidate_validation_and_prediction_reject_inconsistent_contact_geometry(
    client: TestClient,
) -> None:
    # contact_width_mm: 7.5 mm is in-domain [5.13, 8.0]
    # contact_area_mm2: 135.0 mm2 is in-domain [121.8, 189.9]
    # However, 7.5 * 23.75 mm = 178.125 mm2, which disagrees with 135.0 mm2 by 24.2% (> 5%).
    bad_payload = {
        **IN_DOMAIN_PAYLOAD,
        "contact_width_mm": 7.5,
        "contact_area_mm2": 135.0,
        "nominal_pressure_mpa": 10.0 / 135.0,
    }

    # Test candidate validation flags it
    resp_val = client.post(
        CANDIDATE_URL,
        json={"candidates": [{"candidate_id": "geom-bad", "conditions": bad_payload}]},
    )
    assert resp_val.status_code == 200
    res = resp_val.json()["results"][0]
    assert res["accepted_for_physical_testing"] is False
    assert any("23.75 mm" in issue for issue in res["issues"])

    # Test prediction endpoint rejects it with 422
    resp_pred = client.post(PREDICT_URL, json=bad_payload)
    assert resp_pred.status_code == 422
    assert "23.75 mm" in resp_pred.json()["detail"]


@requires_bundle
def test_candidate_validation_flags_duplicate_candidate_ids(client: TestClient) -> None:
    response = client.post(
        CANDIDATE_URL,
        json={
            "candidates": [
                {"candidate_id": "dup-id", "conditions": IN_DOMAIN_PAYLOAD},
                {"candidate_id": "dup-id", "conditions": {**IN_DOMAIN_PAYLOAD, "normal_load_n": 20.0, "nominal_pressure_mpa": 20.0 / 150.0}},
            ]
        },
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert results[0]["accepted_for_physical_testing"] is True
    assert results[1]["accepted_for_physical_testing"] is False
    assert any("Duplicate candidate_id" in issue for issue in results[1]["issues"])


@requires_bundle
def test_candidate_validation_flags_duplicate_physical_conditions(client: TestClient) -> None:
    response = client.post(
        CANDIDATE_URL,
        json={
            "candidates": [
                {"candidate_id": "first-candidate", "conditions": IN_DOMAIN_PAYLOAD},
                {"candidate_id": "second-candidate", "conditions": IN_DOMAIN_PAYLOAD},
            ]
        },
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert results[0]["accepted_for_physical_testing"] is True
    assert results[1]["accepted_for_physical_testing"] is False
    assert any("duplicate of candidate 'first-candidate'" in issue for issue in results[1]["issues"])


@requires_bundle
def test_recommendations_uses_tow_type_specific_geometry(client: TestClient) -> None:
    resp_50c = client.post(
        RECOMMEND_URL,
        json={"tow_type": "T700-12k-50C", "num_candidates": 3},
    )
    resp_60e = client.post(
        RECOMMEND_URL,
        json={"tow_type": "T700-12k-60E", "num_candidates": 3},
    )

    assert resp_50c.status_code == 200
    assert resp_60e.status_code == 200

    cond_50c = resp_50c.json()["recommendations"][0]["conditions"]
    cond_60e = resp_60e.json()["recommendations"][0]["conditions"]

    # 50C median contact area is ~136.2 mm2 vs 60E ~175.5 mm2
    assert cond_50c["contact_area_mm2"] < 150.0
    assert cond_60e["contact_area_mm2"] > 165.0

    # 50C width is ~5.74 mm vs 60E ~7.39 mm
    assert cond_50c["contact_width_mm"] < 6.5
    assert cond_60e["contact_width_mm"] > 7.0

    # Both satisfy tool contact length (23.75 mm)
    assert abs(cond_50c["contact_area_mm2"] / cond_50c["contact_width_mm"] - 23.75) < 0.2
    assert abs(cond_60e["contact_area_mm2"] / cond_60e["contact_width_mm"] - 23.75) < 0.2

    # 50C response includes specific 50C warning
    assert "T700-12k-50C" in resp_50c.json()["reliability_notice"]


@requires_bundle
def test_recommendations_rejects_near_identical_load_bounds(client: TestClient) -> None:
    response = client.post(
        RECOMMEND_URL,
        json={"tow_type": "T700-12k-60E", "min_load_n": 10.0, "max_load_n": 10.00005},
    )
    assert response.status_code == 422
    assert "at least 1e-4 N" in response.json()["detail"]


@requires_bundle
def test_recommendations_ranking_criteria_ordering(client: TestClient) -> None:
    for criterion in ("lowest_predicted_cof", "highest_predicted_cof", "load_sweep_grid"):
        resp = client.post(
            RECOMMEND_URL,
            json={"tow_type": "T700-12k-60E", "num_candidates": 5, "target_criterion": criterion},
        )
        assert resp.status_code == 200
        recs = resp.json()["recommendations"]
        assert len(recs) == 5
        preds = [r["predicted_coefficient_of_friction"] for r in recs]
        loads = [r["conditions"]["normal_load_n"] for r in recs]

        if criterion == "lowest_predicted_cof":
            assert preds == sorted(preds)
        elif criterion == "highest_predicted_cof":
            assert preds == sorted(preds, reverse=True)
        elif criterion == "load_sweep_grid":
            assert loads == sorted(loads)


@requires_bundle
def test_prediction_response_includes_stratified_baseline_metrics(client: TestClient) -> None:
    response = client.post(PREDICT_URL, json=IN_DOMAIN_PAYLOAD)
    assert response.status_code == 200
    metrics = response.json()["metrics"]
    assert metrics["stratified_baseline_mae"] is not None
    assert metrics["stratified_baseline_rmse"] is not None
    assert metrics["stratified_baseline_r2"] is not None
    assert metrics["mae"] < metrics["stratified_baseline_mae"]



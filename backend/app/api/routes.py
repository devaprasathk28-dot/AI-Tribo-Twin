from __future__ import annotations

import csv
import io
import json
import logging
import re
from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import MAX_UPLOAD_BYTES
from app.db.models import ExperimentRecord, ImportArtifact
from app.db.session import get_db
from app.domain.readiness import READINESS_WARNING, load_target_readiness, target_gate
from app.services.model_status import DEMO_PLOT_PATH, EXTERNAL_PLOT_PATH, get_model_status
from app.services.external_prediction import (
    ExternalModelUnavailable,
    ExternalPredictionInputError,
    predict_external_cof,
    recommend_external_experiments,
    validate_external_candidates,
)
from app.services.analytics import compute_analytics
from app.schemas.analytics import AnalyticsResponse
from app.schemas.experiments import (
    ExperimentCreate,
    ExperimentRead,
    ExperimentUpdate,
    HealthResponse,
    ImportCommitResponse,
    ImportHistoryItem,
    ImportPreviewResponse,
    NotReadyResponse,
    ReadinessResponse,
)
from app.schemas.predictions import (
    CofCandidateValidationRequest,
    CofCandidateValidationResponse,
    CofPredictionRequest,
    CofPredictionResponse,
    CofRecommendationRequest,
    CofRecommendationResponse,
)
from app.services.reports import (
    build_analytics_csv,
    build_analytics_pdf,
    build_experiment_pdf,
    build_experiments_csv,
    build_models_pdf,
    build_registry_pdf,
)
from app.services.validation import intake_row_to_payload, is_experiment_template, validate_csv

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")


def record_to_model(
    payload: ExperimentCreate,
    *,
    import_sha256: str = "",
    recorded_at: datetime | None = None,
) -> ExperimentRecord:
    now = datetime.now(timezone.utc)
    return ExperimentRecord(
        experiment_id=payload.experiment_id,
        record_status=payload.record_status.value,
        material_system_as_recorded=payload.material_system_as_recorded,
        planned_by=payload.planned_by,
        composition_as_recorded=payload.composition_as_recorded,
        composition_source_reference=payload.composition_source_reference,
        replicate_group_id=payload.replicate_group_id,
        planned_conditions=payload.planned_conditions.model_dump(exclude_none=True),
        measured_conditions=payload.measured_conditions.model_dump(exclude_none=True),
        measurements=payload.measurements.model_dump(exclude_none=True),
        instrument_id=payload.instrument_id,
        operator=payload.operator,
        experiment_date=payload.experiment_date,
        source_artifact=payload.source_artifact,
        source_location=payload.source_location,
        notes=payload.notes,
        recorded_at_utc=payload.recorded_at_utc or recorded_at or now,
        created_at_utc=now,
        import_sha256=import_sha256,
    )


@router.get("/health", response_model=HealthResponse)
def health(db: Annotated[Session, Depends(get_db)]) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        logger.exception("Database health check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "degraded", "database": "unavailable"},
        ) from error
    return HealthResponse(status="ok", database="ok")


@router.get("/readiness", response_model=ReadinessResponse)
def readiness() -> ReadinessResponse:
    try:
        targets = load_target_readiness()
    except (FileNotFoundError, OSError, csv.Error) as error:
        logger.exception("Could not read target readiness register")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Target-readiness evidence is unavailable.",
        ) from error
    return ReadinessResponse(targets=targets, warning=READINESS_WARNING)


@router.get("/models/status")
def model_status() -> dict[str, object]:
    try:
        return get_model_status()
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        logger.exception("Could not read synthetic model status")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Saved model status is invalid or unavailable.",
        ) from error


@router.get("/models/demo/predictions.png")
def model_demo_plot() -> FileResponse:
    if not DEMO_PLOT_PATH.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Synthetic evaluation plot has not been generated.",
        )
    return FileResponse(
        DEMO_PLOT_PATH,
        media_type="image/png",
        filename="synthetic-demo-predictions-vs-observations.png",
    )


@router.get("/models/external/predictions.png")
def external_model_plot() -> FileResponse:
    if not EXTERNAL_PLOT_PATH.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="External-model evaluation plot has not been generated.",
        )
    return FileResponse(
        EXTERNAL_PLOT_PATH,
        media_type="image/png",
        filename="external-cof-predictions-vs-observations.png",
    )


@router.post("/models/external/predict", response_model=CofPredictionResponse)
def predict_external(payload: CofPredictionRequest) -> CofPredictionResponse:
    """Score one tow-on-tool observation with the provenance-verified external model."""
    try:
        return predict_external_cof(payload)
    except ExternalModelUnavailable as error:
        logger.exception("External model prediction bundle is unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="External model artifacts failed provenance verification.",
        ) from error
    except ExternalPredictionInputError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error


@router.post(
    "/models/external/candidates/validate",
    response_model=CofCandidateValidationResponse,
)
def validate_external_experiment_candidates(
    payload: CofCandidateValidationRequest,
) -> CofCandidateValidationResponse:
    """Validate proposed Cambridge conditions without ranking or scoring them."""
    try:
        return validate_external_candidates(payload)
    except ExternalModelUnavailable as error:
        logger.exception("External model candidate validation bundle is unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="External model artifacts failed provenance verification.",
        ) from error


@router.post(
    "/models/external/recommendations",
    response_model=CofRecommendationResponse,
)
def recommend_external_experiment_candidates(
    payload: CofRecommendationRequest,
) -> CofRecommendationResponse:
    """Generate and rank candidate test conditions bounded to the training domain."""
    try:
        return recommend_external_experiments(payload)
    except ExternalModelUnavailable as error:
        logger.exception("External model recommendation bundle is unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="External model artifacts failed provenance verification.",
        ) from error
    except ExternalPredictionInputError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error



@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    db: Annotated[Session, Depends(get_db)],
    material_system: str | None = Query(default=None, max_length=240),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    record_status: str | None = Query(default=None, pattern="^(PLANNED|MEASURED)$"),
) -> AnalyticsResponse:
    try:
        return compute_analytics(
            db=db,
            material_system=material_system,
            date_from=date_from,
            date_to=date_to,
            record_status=record_status,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error


@router.get("/experiments", response_model=list[ExperimentRead])
def list_experiments(
    db: Annotated[Session, Depends(get_db)],
    response: Response,
    record_status: str | None = Query(default=None, pattern="^(PLANNED|MEASURED)$"),
    query: str | None = Query(default=None, max_length=200),
    material_system: str | None = Query(default=None, max_length=240),
    sort_by: str = Query(default="id", pattern="^(id|experiment_id|record_status|material_system_as_recorded|experiment_date|created_at_utc)$"),
    sort_desc: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[ExperimentRecord]:
    base_statement = select(ExperimentRecord)
    if record_status:
        base_statement = base_statement.where(ExperimentRecord.record_status == record_status)
    if material_system and material_system.strip():
        base_statement = base_statement.where(
            ExperimentRecord.material_system_as_recorded.ilike(f"%{material_system.strip()}%")
        )
    if query and query.strip():
        q = f"%{query.strip()}%"
        base_statement = base_statement.where(
            or_(
                ExperimentRecord.experiment_id.ilike(q),
                ExperimentRecord.material_system_as_recorded.ilike(q),
                ExperimentRecord.composition_as_recorded.ilike(q),
                ExperimentRecord.operator.ilike(q),
                ExperimentRecord.notes.ilike(q),
                ExperimentRecord.source_artifact.ilike(q),
            )
        )

    total_count = db.scalar(select(func.count()).select_from(base_statement.subquery())) or 0
    response.headers["X-Total-Count"] = str(total_count)

    column = getattr(ExperimentRecord, sort_by)
    if sort_desc:
        statement = base_statement.order_by(column.desc())
    else:
        statement = base_statement.order_by(column.asc())

    statement = statement.limit(limit).offset(offset)
    return list(db.scalars(statement))


@router.get("/experiments/count")
def experiment_counts(db: Annotated[Session, Depends(get_db)]) -> dict[str, int]:
    counts = db.execute(
        select(ExperimentRecord.record_status, func.count(ExperimentRecord.id)).group_by(
            ExperimentRecord.record_status
        )
    ).all()
    result = {"PLANNED": 0, "MEASURED": 0, "total": 0}
    for record_status, count in counts:
        result[record_status] = count
        result["total"] += count
    return result


@router.post("/experiments", response_model=ExperimentRead, status_code=status.HTTP_201_CREATED)
def create_experiment(
    payload: ExperimentCreate,
    db: Annotated[Session, Depends(get_db)],
) -> ExperimentRecord:
    if db.scalar(select(ExperimentRecord.id).where(ExperimentRecord.experiment_id == payload.experiment_id)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DUPLICATE_EXPERIMENT_ID", "experiment_id": payload.experiment_id},
        )
    record = record_to_model(payload)
    db.add(record)
    try:
        db.commit()
        db.refresh(record)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DUPLICATE_EXPERIMENT_ID", "experiment_id": payload.experiment_id},
        ) from error
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Experiment record could not be saved")
        raise HTTPException(status_code=500, detail="Experiment record could not be saved.") from error
    return record


@router.post("/plans", response_model=ExperimentRead, status_code=status.HTTP_201_CREATED)
def create_plan(
    payload: ExperimentCreate,
    db: Annotated[Session, Depends(get_db)],
) -> ExperimentRecord:
    if payload.record_status.value != "PLANNED":
        raise HTTPException(status_code=422, detail="The planning endpoint accepts PLANNED records only.")
    return create_experiment(payload, db)


@router.get("/experiments/{experiment_id}", response_model=ExperimentRead)
def get_experiment(
    experiment_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> ExperimentRecord:
    record = db.scalar(
        select(ExperimentRecord).where(ExperimentRecord.experiment_id == experiment_id)
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Experiment record not found.")
    return record


@router.put("/experiments/{experiment_id}", response_model=ExperimentRead)
def update_experiment(
    experiment_id: str,
    payload: ExperimentUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> ExperimentRecord:
    record = db.scalar(
        select(ExperimentRecord).where(ExperimentRecord.experiment_id == experiment_id)
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment record not found.")

    update_data = payload.model_dump(exclude_unset=True)

    # Determine merged conditions and measurements
    merged_planned = (
        payload.planned_conditions.model_dump(exclude_none=True)
        if payload.planned_conditions is not None
        else (dict(record.planned_conditions) if record.planned_conditions else {})
    )
    merged_measured = (
        payload.measured_conditions.model_dump(exclude_none=True)
        if payload.measured_conditions is not None
        else (dict(record.measured_conditions) if record.measured_conditions else {})
    )
    merged_measurements = (
        payload.measurements.model_dump(exclude_none=True)
        if payload.measurements is not None
        else (dict(record.measurements) if record.measurements else {})
    )
    merged_source_artifact = (
        payload.source_artifact.strip()
        if payload.source_artifact is not None
        else (record.source_artifact or "")
    )
    merged_source_location = (
        payload.source_location.strip()
        if payload.source_location is not None
        else (record.source_location or "")
    )

    # Scientific validation based on record_status
    if record.record_status == "PLANNED":
        if merged_measured:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Planned records cannot contain measured test conditions.",
            )
        if (
            merged_measurements.get("coefficient_of_friction")
            or merged_measurements.get("wear_measurement")
            or merged_measurements.get("specific_wear_rate")
            or merged_measurements.get("wear_volume_loss")
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Planned records cannot contain measured responses.",
            )
        if not merged_planned:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Planned records require at least one planned test condition.",
            )
    else:  # MEASURED
        required_conditions = {"load_n", "sliding_velocity_m_per_s", "sliding_distance_m"}
        if not required_conditions.issubset(merged_measured):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Measured records require measured load, velocity, and distance.",
            )
        has_measurement = any(
            merged_measurements.get(k)
            for k in (
                "coefficient_of_friction",
                "wear_measurement",
                "specific_wear_rate",
                "wear_volume_loss",
            )
        )
        if not has_measurement:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Measured records require at least one measured response.",
            )
        if not merged_source_artifact or not merged_source_location:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Measured records require source artifact and source location.",
            )

    # Apply updates
    for field, value in update_data.items():
        if field == "planned_conditions":
            record.planned_conditions = merged_planned
        elif field == "measured_conditions":
            record.measured_conditions = merged_measured
        elif field == "measurements":
            record.measurements = merged_measurements
        elif field in {"material_system_as_recorded", "source_artifact", "source_location"}:
            setattr(record, field, value.strip())
        elif field == "notes":
            record.notes = value or ""
        else:
            setattr(record, field, value)

    try:
        db.commit()
        db.refresh(record)
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Failed to update experiment record %s", experiment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Experiment record could not be updated.",
        ) from error

    return record


@router.delete("/experiments/{experiment_id}", status_code=status.HTTP_200_OK)
def delete_experiment(
    experiment_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    record = db.scalar(
        select(ExperimentRecord).where(ExperimentRecord.experiment_id == experiment_id)
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment record not found.")

    try:
        db.delete(record)
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Failed to delete experiment record %s", experiment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Experiment record could not be deleted.",
        ) from error

    return {"message": "Experiment record deleted", "experiment_id": experiment_id}


@router.post("/imports/preview", response_model=ImportPreviewResponse)
async def preview_import(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
) -> ImportPreviewResponse:
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"CSV exceeds {MAX_UPLOAD_BYTES} bytes.")
    try:
        result = validate_csv(file.filename or "", content)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    template = is_experiment_template(result)
    warnings = list(result.warnings)
    if result.format_name == "source-extraction":
        warnings.append(
            {
                "severity": "WARNING",
                "code": "SOURCE_ARCHIVE_ONLY",
                "message": "Source-extraction CSV can be reviewed but not imported as new measured records without explicit run mapping.",
            }
        )

    # Check for duplicate artifact by cryptographic hash
    existing_artifact = db.scalar(
        select(ImportArtifact.id).where(ImportArtifact.sha256 == result.sha256)
    )
    is_duplicate_artifact = existing_artifact is not None
    if is_duplicate_artifact:
        warnings.append(
            {
                "severity": "WARNING",
                "code": "DUPLICATE_IMPORT_ARTIFACT",
                "message": f"This exact CSV artifact has already been persisted (SHA-256: {result.sha256[:12]}…).",
            }
        )

    # Detect row-level duplicate experiment IDs (intra-file and in PostgreSQL)
    file_ids: list[str] = [
        str(r.get("experiment_id") or "").strip()
        for r in result.rows
        if str(r.get("experiment_id") or "").strip()
    ]
    seen_ids: set[str] = set()
    intra_file_duplicates: set[str] = set()
    for eid in file_ids:
        if eid in seen_ids:
            intra_file_duplicates.add(eid)
        seen_ids.add(eid)

    existing_db_ids: set[str] = set()
    if file_ids:
        existing_db_ids = set(
            db.scalars(
                select(ExperimentRecord.experiment_id).where(
                    ExperimentRecord.experiment_id.in_(file_ids)
                )
            )
        )

    colliding_ids = sorted(intra_file_duplicates | existing_db_ids)
    if colliding_ids:
        warnings.append(
            {
                "severity": "WARNING",
                "code": "DUPLICATE_EXPERIMENT_IDS",
                "message": f"{len(colliding_ids)} experiment identifier(s) collide with existing database records or repeat within the file: {', '.join(colliding_ids[:5])}{'…' if len(colliding_ids) > 5 else ''}.",
            }
        )

    error_row_numbers = {
        err.get("row_number")
        for err in result.errors
        if err.get("code") != "DUPLICATE_IDENTIFIER" and err.get("row_number") is not None
    }
    duplicate_rows = 0
    rejected_rows = 0
    accepted_rows = 0
    has_schema_level_error = any(err.get("row_number") is None for err in result.errors)

    if has_schema_level_error:
        rejected_rows = result.row_count
    else:
        for idx, r in enumerate(result.rows, start=2):
            eid = str(r.get("experiment_id") or "").strip()
            if eid in (intra_file_duplicates | existing_db_ids):
                duplicate_rows += 1
            elif idx in error_row_numbers:
                rejected_rows += 1
            else:
                accepted_rows += 1

    confirmable = (
        result.valid
        and template
        and not is_duplicate_artifact
        and len(colliding_ids) == 0
    )

    return ImportPreviewResponse(
        filename=file.filename or "",
        sha256=result.sha256,
        size_bytes=result.size_bytes,
        format_name=result.format_name,
        row_count=result.row_count,
        valid=result.valid,
        errors=list(result.errors),
        warnings=warnings,
        preview_rows=[
            {
                key: value
                for key, value in row.items()
                if isinstance(key, str) and (value is None or isinstance(value, str))
            }
            for row in result.rows[:10]
        ],
        can_confirm_import=confirmable,
        accepted_rows=accepted_rows,
        duplicate_rows=duplicate_rows,
        rejected_rows=rejected_rows,
        duplicate_experiment_ids=colliding_ids,
        is_duplicate_artifact=is_duplicate_artifact,
    )


@router.get("/imports/history", response_model=list[ImportHistoryItem])
def get_import_history(
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=25, ge=1, le=100),
) -> list[ImportHistoryItem]:
    statement = select(ImportArtifact).order_by(ImportArtifact.id.desc()).limit(limit)
    artifacts = list(db.scalars(statement))
    results: list[ImportHistoryItem] = []
    for art in artifacts:
        rep = art.validation_report if isinstance(art.validation_report, dict) else {}
        errors = rep.get("errors", []) if isinstance(rep, dict) else []
        warnings = rep.get("warnings", []) if isinstance(rep, dict) else []
        format_name = rep.get("format_name", "unknown") if isinstance(rep, dict) else "unknown"
        outcome = "VALID" if not errors else "WITH_ERRORS"
        results.append(
            ImportHistoryItem(
                id=art.id,
                sha256=art.sha256,
                filename=art.filename,
                content_type=art.content_type,
                size_bytes=art.size_bytes,
                row_count=art.row_count,
                format_name=str(format_name),
                created_at_utc=art.created_at_utc,
                validation_outcome=outcome,
                errors_count=len(errors) if isinstance(errors, list) else 0,
                warnings_count=len(warnings) if isinstance(warnings, list) else 0,
            )
        )
    return results


@router.post("/imports/confirm", response_model=ImportCommitResponse)
async def confirm_import(
    db: Annotated[Session, Depends(get_db)],
    file: Annotated[UploadFile, File()],
    expected_sha256: Annotated[str, Form()],
    confirmation: Annotated[bool, Form()],
) -> ImportCommitResponse:
    if not confirmation:
        raise HTTPException(status_code=400, detail="Explicit confirmation is required.")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"CSV exceeds {MAX_UPLOAD_BYTES} bytes.")
    try:
        result = validate_csv(file.filename or "", content)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if result.sha256 != expected_sha256.lower():
        raise HTTPException(status_code=409, detail="Upload differs from the previewed file hash.")
    if not result.valid:
        raise HTTPException(status_code=422, detail={"errors": result.errors})
    if not is_experiment_template(result):
        raise HTTPException(
            status_code=422,
            detail="Only the experiment-record template can be confirmed as database records.",
        )
    if db.scalar(select(ImportArtifact.id).where(ImportArtifact.sha256 == result.sha256)):
        raise HTTPException(
            status_code=409,
            detail={"code": "DUPLICATE_IMPORT", "sha256": result.sha256},
        )

    records: list[ExperimentRecord] = []
    try:
        for row in result.rows:
            payload = ExperimentCreate.model_validate(intake_row_to_payload(row))
            records.append(record_to_model(payload, import_sha256=result.sha256))
    except (ValueError, TypeError) as error:
        raise HTTPException(status_code=422, detail=f"Import row validation failed: {error}") from error

    ids = [record.experiment_id for record in records]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=422, detail="Import contains duplicate experiment identifiers.")
    existing_ids = set(
        db.scalars(select(ExperimentRecord.experiment_id).where(ExperimentRecord.experiment_id.in_(ids)))
    )
    if existing_ids:
        raise HTTPException(
            status_code=409,
            detail={"code": "DUPLICATE_EXPERIMENT_ID", "experiment_ids": sorted(existing_ids)},
        )
    artifact = ImportArtifact(
        sha256=result.sha256,
        filename=re.sub(r"[^A-Za-z0-9._-]+", "_", file.filename or "import.csv")[:255],
        content_type=file.content_type or "text/csv",
        size_bytes=result.size_bytes,
        row_count=result.row_count,
        validation_report={
            "format_name": result.format_name,
            "errors": list(result.errors),
            "warnings": list(result.warnings),
        },
        original_bytes=content,
    )
    db.add(artifact)
    db.add_all(records)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"code": "DUPLICATE_IMPORT_OR_EXPERIMENT"},
        ) from error
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("CSV import transaction failed")
        raise HTTPException(status_code=500, detail="CSV import could not be persisted.") from error
    return ImportCommitResponse(
        sha256=result.sha256,
        records_imported=len(records),
        duplicate=False,
        message="Original CSV artifact and records were persisted without changing the uploaded values.",
    )


@router.get("/exports/experiments.csv")
def export_experiments(
    db: Annotated[Session, Depends(get_db)],
    record_status: str | None = Query(default=None, pattern="^(PLANNED|MEASURED)$"),
    query: str | None = Query(default=None, max_length=200),
    material_system: str | None = Query(default=None, max_length=240),
) -> StreamingResponse:
    statement = select(ExperimentRecord).order_by(ExperimentRecord.id)
    if record_status:
        statement = statement.where(ExperimentRecord.record_status == record_status)
    if material_system and material_system.strip():
        statement = statement.where(
            ExperimentRecord.material_system_as_recorded.ilike(f"%{material_system.strip()}%")
        )
    if query and query.strip():
        q = f"%{query.strip()}%"
        statement = statement.where(
            or_(
                ExperimentRecord.experiment_id.ilike(q),
                ExperimentRecord.material_system_as_recorded.ilike(q),
                ExperimentRecord.composition_as_recorded.ilike(q),
                ExperimentRecord.operator.ilike(q),
                ExperimentRecord.notes.ilike(q),
                ExperimentRecord.source_artifact.ilike(q),
            )
        )
    records = list(db.scalars(statement))
    output = io.StringIO(newline="")
    fields = [
        "experiment_id",
        "record_status",
        "material_system_as_recorded",
        "planned_by",
        "composition_as_recorded",
        "composition_source_reference",
        "replicate_group_id",
        "load_n",
        "sliding_velocity_m_per_s",
        "sliding_distance_m",
        "test_duration_min",
        "coefficient_of_friction",
        "wear_measurement_name",
        "wear_measurement_value",
        "wear_measurement_unit",
        "planned_conditions",
        "measured_conditions",
        "measurements",
        "instrument_id",
        "operator",
        "experiment_date",
        "source_artifact",
        "source_location",
        "notes",
        "recorded_at_utc",
        "import_sha256",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for record in records:
        cond = record.measured_conditions if record.record_status == "MEASURED" else record.planned_conditions
        meas = record.measurements or {}
        cof_obj = meas.get("coefficient_of_friction") if isinstance(meas, dict) else None
        cof_val = cof_obj.get("value") if isinstance(cof_obj, dict) else None

        wear_obj = meas.get("wear_measurement") if isinstance(meas, dict) else None
        wear_val = wear_obj.get("value") if isinstance(wear_obj, dict) else None
        wear_unit = wear_obj.get("unit_as_recorded") if isinstance(wear_obj, dict) else None
        wear_name = meas.get("wear_measurement_name_as_recorded", "") if isinstance(meas, dict) else ""

        writer.writerow(
            {
                "experiment_id": record.experiment_id,
                "record_status": record.record_status,
                "material_system_as_recorded": record.material_system_as_recorded,
                "planned_by": record.planned_by,
                "composition_as_recorded": record.composition_as_recorded,
                "composition_source_reference": record.composition_source_reference,
                "replicate_group_id": record.replicate_group_id,
                "load_n": cond.get("load_n", "") if isinstance(cond, dict) else "",
                "sliding_velocity_m_per_s": cond.get("sliding_velocity_m_per_s", "") if isinstance(cond, dict) else "",
                "sliding_distance_m": cond.get("sliding_distance_m", "") if isinstance(cond, dict) else "",
                "test_duration_min": cond.get("test_duration_min", "") if isinstance(cond, dict) else "",
                "coefficient_of_friction": cof_val if cof_val is not None else "",
                "wear_measurement_name": wear_name or "",
                "wear_measurement_value": wear_val if wear_val is not None else "",
                "wear_measurement_unit": wear_unit or "",
                "planned_conditions": json_dumps(record.planned_conditions),
                "measured_conditions": json_dumps(record.measured_conditions),
                "measurements": json_dumps(record.measurements),
                "instrument_id": record.instrument_id,
                "operator": record.operator,
                "experiment_date": record.experiment_date.isoformat() if record.experiment_date is not None else "",
                "source_artifact": record.source_artifact,
                "source_location": record.source_location,
                "notes": record.notes,
                "recorded_at_utc": record.recorded_at_utc.isoformat() if record.recorded_at_utc else "",
                "import_sha256": record.import_sha256,
            }
        )
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="ai-tribotwin-experiments.csv"'},
    )


def json_dumps(value: object) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, sort_keys=True)


@router.post("/predictions/{target_id}", response_model=NotReadyResponse)
def blocked_prediction(target_id: str) -> Response:
    gate = target_gate(target_id)
    if gate is None:
        raise HTTPException(status_code=404, detail="Unknown response target.")
    details = NotReadyResponse(
        target_id=target_id,
        status=gate.status,
        message="No prediction was produced. Scientific target evidence and a validated, evaluated model are required.",
        required_evidence=[gate.required_evidence],
    )
    return Response(
        content=details.model_dump_json(),
        status_code=status.HTTP_409_CONFLICT,
        media_type="application/json",
    )


@router.post("/optimizations", response_model=NotReadyResponse)
def blocked_optimization(objective_ids: list[str] = Query(..., min_length=1)) -> Response:
    statuses = [target_gate(target_id) for target_id in objective_ids]
    if any(item is None for item in statuses):
        raise HTTPException(status_code=404, detail="Unknown response target.")
    details = NotReadyResponse(
        target_id=None,
        status="BLOCKED",
        message="No optimization was run. Every objective needs released targets, validated models, evaluation evidence, and defensible constraints.",
        required_evidence=[
            item.required_evidence
            for item in statuses
            if item is not None and item.status != "READY"
        ]
        + ["validated model evaluation and experimentally supported optimization constraints"],
    )
    return Response(
        content=details.model_dump_json(),
        status_code=status.HTTP_409_CONFLICT,
        media_type="application/json",
    )


# =========================================================================
# REPORTING & EXPORT ENDPOINTS (STEP 7)
# =========================================================================
@router.get("/reports/experiment/{experiment_id}/pdf")
def export_experiment_report_pdf(
    experiment_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Generate a publication-grade PDF engineering report for a single experiment."""
    record = db.scalar(
        select(ExperimentRecord).where(ExperimentRecord.experiment_id == experiment_id)
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment record not found.")

    pdf_bytes = build_experiment_pdf(record)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="AI-TriboTwin-Experiment-{experiment_id}.pdf"'
        },
    )


@router.get("/reports/experiments/pdf")
def export_registry_report_pdf(
    db: Annotated[Session, Depends(get_db)],
    material_system: str | None = None,
    record_status: str | None = Query(default=None, alias="status"),
    query: str | None = None,
    limit: int = Query(default=200, ge=1, le=500),
) -> Response:
    """Generate a downloadable PDF summary of the filtered experimental registry."""
    base_statement = select(ExperimentRecord)
    if record_status and record_status != "ALL":
        base_statement = base_statement.where(ExperimentRecord.record_status == record_status)
    if material_system and material_system.strip() and material_system != "ALL":
        base_statement = base_statement.where(
            ExperimentRecord.material_system_as_recorded.ilike(f"%{material_system.strip()}%")
        )
    if query and query.strip():
        q = f"%{query.strip()}%"
        base_statement = base_statement.where(
            or_(
                ExperimentRecord.experiment_id.ilike(q),
                ExperimentRecord.material_system_as_recorded.ilike(q),
                ExperimentRecord.composition_as_recorded.ilike(q),
                ExperimentRecord.operator.ilike(q),
                ExperimentRecord.notes.ilike(q),
                ExperimentRecord.source_artifact.ilike(q),
            )
        )
    records = list(db.scalars(base_statement.order_by(ExperimentRecord.id.asc()).limit(limit)))
    filters = {
        "material_system": material_system,
        "status": record_status,
        "query": query,
    }
    pdf_bytes = build_registry_pdf(records, filters)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="AI-TriboTwin-Experiment-Registry-Summary.pdf"'
        },
    )


@router.get("/reports/experiments/csv")
def export_registry_report_csv(
    db: Annotated[Session, Depends(get_db)],
    material_system: str | None = None,
    record_status: str | None = Query(default=None, alias="status"),
    query: str | None = None,
) -> Response:
    """Export filtered experiments registry to clean RFC 4180 CSV with explicit units."""
    base_statement = select(ExperimentRecord)
    if record_status and record_status != "ALL":
        base_statement = base_statement.where(ExperimentRecord.record_status == record_status)
    if material_system and material_system.strip() and material_system != "ALL":
        base_statement = base_statement.where(
            ExperimentRecord.material_system_as_recorded.ilike(f"%{material_system.strip()}%")
        )
    if query and query.strip():
        q = f"%{query.strip()}%"
        base_statement = base_statement.where(
            or_(
                ExperimentRecord.experiment_id.ilike(q),
                ExperimentRecord.material_system_as_recorded.ilike(q),
                ExperimentRecord.composition_as_recorded.ilike(q),
                ExperimentRecord.operator.ilike(q),
                ExperimentRecord.notes.ilike(q),
                ExperimentRecord.source_artifact.ilike(q),
            )
        )
    records = list(db.scalars(base_statement.order_by(ExperimentRecord.id.asc())))
    csv_text = build_experiments_csv(records)
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="AI-TriboTwin-Experiments.csv"'
        },
    )


@router.get("/reports/analytics/pdf")
def export_analytics_report_pdf(
    db: Annotated[Session, Depends(get_db)],
    material_system: str | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
) -> Response:
    """Generate a downloadable PDF analytics summary report."""
    analytics = compute_analytics(
        db,
        material_system=material_system,
        date_from=date_start,
        date_to=date_end,
        record_status=status_filter,
    )
    filters = {
        "material_system": material_system,
        "date_start": date_start,
        "date_end": date_end,
        "status": status_filter,
    }
    pdf_bytes = build_analytics_pdf(analytics, filters)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="AI-TriboTwin-Analytics-Summary.pdf"'
        },
    )


@router.get("/reports/analytics/csv")
def export_analytics_report_csv(
    db: Annotated[Session, Depends(get_db)],
    material_system: str | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
) -> Response:
    """Export analytics summary KPIs and distributions to CSV."""
    analytics = compute_analytics(
        db,
        material_system=material_system,
        date_from=date_start,
        date_to=date_end,
        record_status=status_filter,
    )
    csv_text = build_analytics_csv(analytics)
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="AI-TriboTwin-Analytics-Summary.csv"'
        },
    )


@router.get("/reports/models/pdf")
def export_models_report_pdf() -> Response:
    """Generate a scientific audit report detailing model evaluation, provenance, and readiness gates."""
    model_status_data = get_model_status()
    pdf_bytes = build_models_pdf(model_status_data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="AI-TriboTwin-Model-Evaluation-Provenance.pdf"'
        },
    )


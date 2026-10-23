from __future__ import annotations

import math
import statistics
from collections import defaultdict
from datetime import date
from typing import Any

from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from app.db.models import ExperimentRecord
from app.schemas.analytics import (
    AnalyticsKpis,
    AnalyticsResponse,
    CofConditionPoint,
    CofDistribution,
    CofRelationships,
    DistributionBin,
    MaterialDistributionItem,
    NumericStats,
    TimeSeriesPoint,
    WearDistribution,
    WearDistributionGroup,
)


def compute_numeric_stats(values: list[float], unit: str = "") -> NumericStats | None:
    if not values:
        return None
    return NumericStats(
        count=len(values),
        min=round(min(values), 4),
        max=round(max(values), 4),
        mean=round(statistics.mean(values), 4),
        median=round(statistics.median(values), 4),
        unit=unit,
    )


def make_histogram_bins(values: list[float], num_bins: int = 8) -> list[DistributionBin]:
    if not values:
        return []
    min_val = min(values)
    max_val = max(values)
    if min_val == max_val or len(values) <= 1:
        return [
            DistributionBin(
                bin_start=round(min_val, 4),
                bin_end=round(max_val, 4),
                bin_label=f"{min_val:.3f}",
                count=len(values),
            )
        ]
    step = (max_val - min_val) / num_bins
    bins = [0] * num_bins
    bin_ranges: list[tuple[float, float]] = []
    for i in range(num_bins):
        b_start = min_val + i * step
        b_end = min_val + (i + 1) * step if i < num_bins - 1 else max_val
        bin_ranges.append((b_start, b_end))

    for val in values:
        idx = int((val - min_val) / step)
        if idx >= num_bins:
            idx = num_bins - 1
        elif idx < 0:
            idx = 0
        bins[idx] += 1

    return [
        DistributionBin(
            bin_start=round(b_start, 4),
            bin_end=round(b_end, 4),
            bin_label=f"{b_start:.3f}–{b_end:.3f}",
            count=count,
        )
        for (b_start, b_end), count in zip(bin_ranges, bins)
    ]


def compute_analytics(
    db: Session,
    material_system: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    record_status: str | None = None,
) -> AnalyticsResponse:
    if date_from and date_to and date_from > date_to:
        raise ValueError("date_from must not be after date_to")

    # Distinct materials across entire database for filter dropdowns
    all_distinct_materials = list(
        db.scalars(
            select(ExperimentRecord.material_system_as_recorded)
            .distinct()
            .where(ExperimentRecord.material_system_as_recorded != "")
            .order_by(ExperimentRecord.material_system_as_recorded)
        )
    )

    # Base query for analytics data matching filters
    query = select(ExperimentRecord)
    if record_status:
        query = query.where(ExperimentRecord.record_status == record_status)
    if material_system and material_system.strip():
        query = query.where(ExperimentRecord.material_system_as_recorded == material_system.strip())
    if date_from:
        query = query.where(ExperimentRecord.experiment_date >= date_from)
    if date_to:
        query = query.where(ExperimentRecord.experiment_date <= date_to)

    records = list(db.scalars(query.order_by(ExperimentRecord.id)))

    # KPIs
    total_records = len(records)
    measured_records = sum(1 for r in records if r.record_status == "MEASURED")
    planned_records = sum(1 for r in records if r.record_status == "PLANNED")
    distinct_materials_in_scope = len(
        {r.material_system_as_recorded for r in records if r.material_system_as_recorded}
    )

    cof_records_count = 0
    wear_records_count = 0

    # Data collectors
    timeline_dict: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "measured": 0, "planned": 0})
    materials_dict: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "measured": 0, "planned": 0})
    cof_values: list[float] = []
    wear_groups_data: dict[tuple[str, str], list[float]] = defaultdict(list)
    cof_condition_points: list[CofConditionPoint] = []

    for r in records:
        # Timeline period
        period: str
        if r.experiment_date:
            period = r.experiment_date.strftime("%Y-%m")
        elif r.created_at_utc:
            period = r.created_at_utc.strftime("%Y-%m")
        else:
            period = "Unspecified"

        timeline_dict[period]["total"] += 1
        if r.record_status == "MEASURED":
            timeline_dict[period]["measured"] += 1
        else:
            timeline_dict[period]["planned"] += 1

        # Material distribution
        mat = r.material_system_as_recorded or "Unspecified"
        materials_dict[mat]["total"] += 1
        if r.record_status == "MEASURED":
            materials_dict[mat]["measured"] += 1
        else:
            materials_dict[mat]["planned"] += 1

        # For MEASURED records: inspect measurements
        if r.record_status == "MEASURED":
            meas: dict[str, Any] = r.measurements if isinstance(r.measurements, dict) else {}
            has_cof = False
            has_wear = False

            # COF extraction
            cof_item = meas.get("coefficient_of_friction")
            if isinstance(cof_item, dict) and "value" in cof_item:
                val = cof_item["value"]
                if isinstance(val, (int, float)) and not math.isnan(val) and not math.isinf(val):
                    cof_values.append(float(val))
                    has_cof = True

                    # Extract condition point for relationships
                    cond: dict[str, Any] = (
                        r.measured_conditions if isinstance(r.measured_conditions, dict) else {}
                    )
                    load = cond.get("load_n")
                    vel = cond.get("sliding_velocity_m_per_s")
                    dist = cond.get("sliding_distance_m")

                    cof_condition_points.append(
                        CofConditionPoint(
                            experiment_id=r.experiment_id,
                            material_system=r.material_system_as_recorded,
                            load_n=float(load) if isinstance(load, (int, float)) else None,
                            sliding_velocity_m_per_s=float(vel) if isinstance(vel, (int, float)) else None,
                            sliding_distance_m=float(dist) if isinstance(dist, (int, float)) else None,
                            coefficient_of_friction=float(val),
                        )
                    )

            # Wear extraction: check wear_measurement, specific_wear_rate, wear_volume_loss
            wear_item = meas.get("wear_measurement")
            if isinstance(wear_item, dict) and "value" in wear_item:
                val = wear_item["value"]
                unit = str(wear_item.get("unit_as_recorded", "unspecified"))
                name = str(meas.get("wear_measurement_name_as_recorded") or "wear measurement")
                if isinstance(val, (int, float)) and not math.isnan(val) and not math.isinf(val):
                    wear_groups_data[(name, unit)].append(float(val))
                    has_wear = True

            swr_item = meas.get("specific_wear_rate")
            if isinstance(swr_item, dict) and "value" in swr_item:
                val = swr_item["value"]
                unit = str(swr_item.get("unit_as_recorded", "mm3/N-m"))
                if isinstance(val, (int, float)) and not math.isnan(val) and not math.isinf(val):
                    wear_groups_data[("specific wear rate", unit)].append(float(val))
                    has_wear = True

            vol_item = meas.get("wear_volume_loss")
            if isinstance(vol_item, dict) and "value" in vol_item:
                val = vol_item["value"]
                unit = str(vol_item.get("unit_as_recorded", "mm3"))
                if isinstance(val, (int, float)) and not math.isnan(val) and not math.isinf(val):
                    wear_groups_data[("wear volume loss", unit)].append(float(val))
                    has_wear = True

            if has_cof:
                cof_records_count += 1
            if has_wear:
                wear_records_count += 1

    # Format timeline
    timeline_points = [
        TimeSeriesPoint(
            period=period,
            total=data["total"],
            measured=data["measured"],
            planned=data["planned"],
        )
        for period, data in sorted(timeline_dict.items(), key=lambda x: x[0])
    ]

    # Format materials
    material_items = [
        MaterialDistributionItem(
            material_system=mat,
            total_count=data["total"],
            measured_count=data["measured"],
            planned_count=data["planned"],
        )
        for mat, data in sorted(materials_dict.items(), key=lambda x: x[1]["total"], reverse=True)
    ]

    # Format COF distribution
    cof_has_data = len(cof_values) > 0
    cof_dist = CofDistribution(
        has_data=cof_has_data,
        observation_count=len(cof_values),
        stats=compute_numeric_stats(cof_values, "dimensionless"),
        bins=make_histogram_bins(cof_values, num_bins=8),
        unit="dimensionless",
        note=(
            f"Distribution computed from {len(cof_values)} verified laboratory measurements."
            if cof_has_data
            else "No measured friction coefficients exist in the selected filter range."
        ),
    )

    # Format Wear distribution (strictly grouped by compatible name and unit)
    wear_groups: list[WearDistributionGroup] = []
    total_wear_points = sum(len(v) for v in wear_groups_data.values())
    for (name, unit), vals in sorted(wear_groups_data.items(), key=lambda x: len(x[1]), reverse=True):
        wear_groups.append(
            WearDistributionGroup(
                measurement_name=name,
                unit=unit,
                observation_count=len(vals),
                stats=compute_numeric_stats(vals, unit),
                bins=make_histogram_bins(vals, num_bins=6),
            )
        )

    wear_dist = WearDistribution(
        has_data=len(wear_groups) > 0,
        total_wear_observations=total_wear_points,
        groups=wear_groups,
        note=(
            f"Computed from {total_wear_points} observations across {len(wear_groups)} distinct, un-combined measurement-unit pairs."
            if wear_groups
            else "No measured wear observations exist in the selected filter range."
        ),
    )

    # Format COF relationships
    cof_relationships = CofRelationships(
        has_sufficient_data=len(cof_condition_points) >= 3,
        observation_count=len(cof_condition_points),
        points=cof_condition_points,
    )

    return AnalyticsResponse(
        kpis=AnalyticsKpis(
            total_records=total_records,
            measured_records=measured_records,
            planned_records=planned_records,
            distinct_materials_count=distinct_materials_in_scope,
            records_with_cof=cof_records_count,
            records_with_wear=wear_records_count,
        ),
        timeline=timeline_points,
        materials=material_items,
        distinct_material_names=all_distinct_materials,
        cof_distribution=cof_dist,
        wear_distribution=wear_dist,
        cof_relationships=cof_relationships,
        filter_echo={
            "material_system": material_system,
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "record_status": record_status,
        },
    )

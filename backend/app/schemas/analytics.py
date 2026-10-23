from __future__ import annotations

from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class AnalyticsKpis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_records: int = 0
    measured_records: int = 0
    planned_records: int = 0
    distinct_materials_count: int = 0
    records_with_cof: int = 0
    records_with_wear: int = 0


class TimeSeriesPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period: str  # YYYY-MM
    total: int
    measured: int
    planned: int


class MaterialDistributionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material_system: str
    total_count: int
    measured_count: int
    planned_count: int


class DistributionBin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bin_start: float
    bin_end: float
    bin_label: str
    count: int


class NumericStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    median: float | None = None
    unit: str = ""


class CofDistribution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    has_data: bool
    observation_count: int
    stats: NumericStats | None = None
    bins: list[DistributionBin] = Field(default_factory=list)
    unit: str = "dimensionless"
    note: str = ""


class WearDistributionGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    measurement_name: str
    unit: str
    observation_count: int
    stats: NumericStats | None = None
    bins: list[DistributionBin] = Field(default_factory=list)


class WearDistribution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    has_data: bool
    total_wear_observations: int
    groups: list[WearDistributionGroup] = Field(default_factory=list)
    note: str = ""


class CofConditionPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str
    material_system: str
    load_n: float | None = None
    sliding_velocity_m_per_s: float | None = None
    sliding_distance_m: float | None = None
    coefficient_of_friction: float


class CofRelationships(BaseModel):
    model_config = ConfigDict(extra="forbid")

    has_sufficient_data: bool  # requires >= 3 compatible observations
    observation_count: int
    points: list[CofConditionPoint] = Field(default_factory=list)
    scientific_disclaimer: str = (
        "Descriptive visualization only. Descriptive correlation between test conditions "
        "and friction does not imply causation. Do not infer optimal test conditions without "
        "mechanistic physics or causal experimental controls."
    )


class AnalyticsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kpis: AnalyticsKpis
    timeline: list[TimeSeriesPoint]
    materials: list[MaterialDistributionItem]
    distinct_material_names: list[str]
    cof_distribution: CofDistribution
    wear_distribution: WearDistribution
    cof_relationships: CofRelationships
    filter_echo: dict[str, str | None]

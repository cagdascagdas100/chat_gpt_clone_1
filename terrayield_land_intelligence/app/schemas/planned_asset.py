from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class PlannedAssetItem(BaseModel):
    id: int | None = None
    source_id: str | None = None
    source_name: str | None = None
    source_type: str | None = None
    source_url: str | None = None
    asset_type: str | None = None
    asset_subtype: str | None = None
    title: str | None = None
    description: str | None = None
    planning_reference: str | None = None
    local_authority: str | None = None
    region: str | None = None
    country: str | None = None
    status: str | None = None
    probability: float | None = None
    completion_month: str | None = None
    value: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PlannedAssetSourceItem(BaseModel):
    id: int | None = None
    name: str
    source_type: str | None = None
    url: str | None = None
    last_source_update_at: str | None = None
    licence: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PlannedAssetsIngestRequest(BaseModel):
    source_name: str
    source_url: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class PlannedAssetsIngestResponse(BaseModel):
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[str] = Field(default_factory=list)


class PlannedAssetsRecalculateRequest(BaseModel):
    parcel_ids: list[str] | None = None
    bbox: list[float] | None = None
    force: bool = False


class PlannedAssetsRecalculateResponse(BaseModel):
    recalculated: int = 0
    errors: list[str] = Field(default_factory=list)


class ParcelPlannedFeatureSummary(BaseModel):
    parcel_id: str
    layer_kind: str = "planned_buildings_v1"
    planned_asset_count: int = 0
    planned_buildings: list[dict[str, Any]] = Field(default_factory=list)
    planned_building_1_value: float | None = None
    planned_building_1_probability: float | None = None
    planned_building_1_completion_month: str | None = None
    planned_building_2_value: float | None = None
    planned_building_2_probability: float | None = None
    planned_building_2_completion_month: str | None = None
    planned_building_3_value: float | None = None
    planned_building_3_probability: float | None = None
    planned_building_3_completion_month: str | None = None
    planned_asset_type: str | None = None
    project_name: str | None = None
    planning_status: str | None = None
    source_evidence: str | None = None
    source_date: str | None = None
    confidence_score: float | None = None
    relation_type: str | None = None
    matching_method: str | None = None
    distance_m: float | None = None
    color_category: str | None = None
    calculation_explanation: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParcelFutureGrowthScoreResponse(BaseModel):
    parcel_id: str
    score: float | None = None
    category: str | None = None
    planned_assets: list[ParcelPlannedFeatureSummary] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

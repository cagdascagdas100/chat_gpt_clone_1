from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, Field


class FutureGrowthLayerFeatureProperties(BaseModel):
    parcel_id: int
    future_growth_percent: float
    growth_probability_percent: float | None = None
    probability_not_calibrated: bool = True
    confidence_score: float
    color_class: str
    hex_color: str


class FutureGrowthLayerFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: dict[str, Any] | None = None
    properties: FutureGrowthLayerFeatureProperties


class FutureGrowthLayerResponse(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[FutureGrowthLayerFeature] = Field(default_factory=list)


class FutureGrowthEvidenceItem(BaseModel):
    id: int
    parcel_id: int
    score_id: int
    factor_type: str
    evidence_title: str
    source_title: str | None = None
    source_url: str | None = None
    source_publisher: str | None = None
    publication_date: dt.date | None = None
    data_date: dt.date | None = None
    geography_level: str | None = None
    relation_type: str
    relation_label: str | None = None
    distance_m: float | None = None
    impact_weight: float
    extracted_claim: str | None = None
    confidence: float | None = None
    display_warning: str | None = None
    raw_json: dict[str, Any] = Field(default_factory=dict)


class FutureGrowthParcelDetailResponse(BaseModel):
    parcel_id: int
    local_authority_code: str | None = None
    score_total: float
    future_growth_percent: float
    growth_probability_percent: float | None = None
    probability_not_calibrated: bool = True
    score_breakdown: dict[str, float]
    confidence_score: float
    color_class: str
    hex_color: str
    color_explanation: str
    city_growth_direction_label: str
    top_reasons: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence: list[FutureGrowthEvidenceItem] = Field(default_factory=list)
    calculation_version: str
    horizon_years: int
    calculated_at: dt.datetime | None = None


class FutureGrowthVectorResponse(BaseModel):
    city_id: str
    local_authority_code: str | None = None
    city_name: str | None = None
    base_centroid: dict[str, Any] | None = None
    weighted_future_centroid: dict[str, Any] | None = None
    vector_geometry: dict[str, Any] | None = None
    direction_label: str | None = None
    strength_score: float
    confidence_score: float
    horizon_years: int
    calculation_version: str | None = None
    calculated_at: dt.datetime | None = None
    evidence_summary: dict[str, Any] = Field(default_factory=dict)


class FutureGrowthMethodologyResponse(BaseModel):
    layer_name: str
    methodology_markdown: str
    source_config_path: str | None = None
    generated_at: dt.datetime


class FutureGrowthJobRequest(BaseModel):
    action: Literal["future-growth:ingest", "future-growth:score", "future-growth:vectors", "future-growth:all"]
    mode: str | None = None
    sources: list[str] | None = None
    local_authority_code: str | None = None
    calculation_version: str | None = None
    horizon_years: int | None = None
    limit: int | None = None
    parcel_ids: list[int] | None = None


class FutureGrowthJobResponse(BaseModel):
    action: str
    result: dict[str, Any] = Field(default_factory=dict)

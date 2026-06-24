from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.future_growth.constants import CALCULATION_VERSION_V1, DEFAULT_HORIZON_YEARS


class FutureGrowthTileService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()

    def get_layer_geojson(
        self,
        *,
        bbox: tuple[float, float, float, float] | None,
        zoom: float | None,
        local_authority_code: str | None,
        min_score: float | None,
        max_score: float | None,
        limit: int = 5000,
    ) -> dict[str, Any]:
        version = self.settings.future_growth_calculation_version or CALCULATION_VERSION_V1
        horizon = int(self.settings.future_growth_default_horizon_years or DEFAULT_HORIZON_YEARS)
        zoom_value = float(zoom) if zoom is not None else 12.0
        params: dict[str, Any] = {
            "version": version,
            "horizon": horizon,
            "zoom": zoom_value,
            "limit": int(max(1, min(limit, 20000))),
        }
        where_clauses = [
            "s.calculation_version = :version",
            "s.horizon_years = :horizon",
            """
            NOT EXISTS (
              SELECT 1
              FROM parcel_future_growth_evidence e
              JOIN future_growth_features f ON f.id = e.feature_id
              WHERE e.score_id = s.id
                AND upper(coalesce(e.relation_type, '')) = 'SAME_LOCAL_AUTHORITY'
                AND trim(coalesce(f.local_authority_code, '')) <> ''
                AND lower(trim(f.local_authority_code)) <> lower(trim(coalesce(p.local_authority, '')))
            )
            """,
        ]

        if min_score is not None:
            params["min_score"] = float(min_score)
            where_clauses.append("s.future_growth_percent >= :min_score")
        if max_score is not None:
            params["max_score"] = float(max_score)
            where_clauses.append("s.future_growth_percent <= :max_score")

        authority_value = str(local_authority_code).strip().lower() if local_authority_code else None
        if authority_value:
            params["authority"] = authority_value
            where_clauses.append("lower(coalesce(p.local_authority, '')) = :authority")

        if bbox is not None:
            params.update(
                {
                    "west": float(bbox[0]),
                    "south": float(bbox[1]),
                    "east": float(bbox[2]),
                    "north": float(bbox[3]),
                }
            )
            where_clauses.append(
                """
                ST_Intersects(
                  ST_Transform(p.geometry, 4326),
                  ST_MakeEnvelope(:west, :south, :east, :north, 4326)
                )
                """
            )

        where_sql = " AND ".join(clause.strip() for clause in where_clauses)
        layer_sql = text(
            f"""
            SELECT
              p.parcel_id,
              s.future_growth_percent,
              s.confidence_score,
              s.color_class,
              s.hex_color,
              ST_AsGeoJSON(
                CASE
                  WHEN :zoom < 9
                    THEN ST_Transform(ST_Centroid(p.geometry), 4326)
                  WHEN :zoom < 12
                    THEN ST_Transform(ST_SimplifyPreserveTopology(p.geometry, 15.0), 4326)
                  ELSE ST_Transform(p.geometry, 4326)
                END
              ) AS geometry_json
            FROM parcel_future_growth_scores s
            JOIN parcels_inspire p ON p.parcel_id = s.parcel_id
            WHERE {where_sql}
            ORDER BY s.future_growth_percent DESC, s.confidence_score DESC, p.parcel_id ASC
            LIMIT :limit
            """
        )

        rows = []
        for attempt in range(2):
            try:
                rows = self.session.execute(layer_sql, params).mappings().all()
                break
            except SQLAlchemyError:
                self.session.rollback()
                if attempt == 1:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="future growth layer temporarily unavailable",
                    )

        features = []
        for row in rows:
            try:
                geometry = json.loads(row["geometry_json"]) if row.get("geometry_json") else None
            except json.JSONDecodeError:
                continue
            features.append(
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "parcel_id": row["parcel_id"],
                        "future_growth_percent": float(row["future_growth_percent"] or 0.0),
                        "growth_probability_percent": None,
                        "probability_not_calibrated": True,
                        "confidence_score": float(row["confidence_score"] or 0.0),
                        "color_class": row["color_class"],
                        "hex_color": row["hex_color"],
                    },
                }
            )
        return {"type": "FeatureCollection", "features": features}

    def get_city_vector(self, *, city_id: str | None = None, local_authority_code: str | None = None) -> dict[str, Any]:
        if not city_id and not local_authority_code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="city id veya local authority code gerekli")
        params = {
            "city_id": str(city_id).strip().lower() if city_id else None,
            "authority": str(local_authority_code).strip().lower() if local_authority_code else None,
        }
        row = self.session.execute(
            text(
                """
                SELECT
                  id,
                  city_id,
                  local_authority_code,
                  city_name,
                  direction_label,
                  strength_score,
                  confidence_score,
                  horizon_years,
                  calculation_version,
                  calculated_at,
                  evidence_summary_json,
                  ST_AsGeoJSON(base_centroid) AS base_centroid_json,
                  ST_AsGeoJSON(weighted_future_centroid) AS weighted_future_centroid_json,
                  ST_AsGeoJSON(vector_geometry) AS vector_geometry_json
                FROM city_growth_vectors
                WHERE
                  (:city_id IS NOT NULL AND lower(city_id) = :city_id)
                  OR (:authority IS NOT NULL AND lower(coalesce(local_authority_code, '')) = :authority)
                ORDER BY calculated_at DESC, id DESC
                LIMIT 1
                """
            ),
            params,
        ).mappings().first()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="city growth vector bulunamadi")
        return {
            "city_id": row["city_id"],
            "local_authority_code": row.get("local_authority_code"),
            "city_name": row.get("city_name"),
            "base_centroid": json.loads(row["base_centroid_json"]) if row.get("base_centroid_json") else None,
            "weighted_future_centroid": json.loads(row["weighted_future_centroid_json"]) if row.get("weighted_future_centroid_json") else None,
            "vector_geometry": json.loads(row["vector_geometry_json"]) if row.get("vector_geometry_json") else None,
            "direction_label": row.get("direction_label"),
            "strength_score": float(row.get("strength_score") or 0.0),
            "confidence_score": float(row.get("confidence_score") or 0.0),
            "horizon_years": int(row.get("horizon_years") or 5),
            "calculation_version": row.get("calculation_version"),
            "calculated_at": row.get("calculated_at"),
            "evidence_summary": row.get("evidence_summary_json") if isinstance(row.get("evidence_summary_json"), dict) else {},
        }

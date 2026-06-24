from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.future_growth.constants import PARCEL_GEOGRAPHY_WARNING


RELATION_TYPE_LABELS = {
    "INTERSECTS_PARCEL": "Parsel ile kesisiyor",
    "WITHIN_250M": "250m icinde",
    "WITHIN_500M": "500m icinde",
    "WITHIN_1000M": "1000m icinde",
    "WITHIN_2000M": "2000m icinde",
    "SAME_LSOA": "Ayni LSOA",
    "SAME_MSOA": "Ayni MSOA",
    "SAME_LOCAL_AUTHORITY": "Ayni local authority",
    "CITY_LEVEL_ONLY": "Sehir duzeyi sinyal",
}


class FutureGrowthEvidenceService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()

    def get_latest_score(self, parcel_id: int) -> dict[str, Any]:
        row = self.session.execute(
            text(
                """
                SELECT
                  s.id,
                  s.parcel_id,
                  p.local_authority AS local_authority_code,
                  s.score_total,
                  s.score_planning,
                  s.score_transport,
                  s.score_market,
                  s.score_demographic,
                  s.score_social,
                  s.score_policy,
                  s.risk_penalty,
                  s.future_growth_percent,
                  s.confidence_score,
                  s.color_class,
                  s.hex_color,
                  s.city_growth_direction_label,
                  s.calculation_version,
                  s.horizon_years,
                  s.calculated_at
                FROM parcel_future_growth_scores s
                JOIN parcels_inspire p ON p.parcel_id = s.parcel_id
                WHERE s.parcel_id = :parcel_id
                  AND NOT EXISTS (
                    SELECT 1
                    FROM parcel_future_growth_evidence e
                    JOIN future_growth_features f ON f.id = e.feature_id
                    WHERE e.score_id = s.id
                      AND upper(coalesce(e.relation_type, '')) = 'SAME_LOCAL_AUTHORITY'
                      AND trim(coalesce(f.local_authority_code, '')) <> ''
                      AND lower(trim(f.local_authority_code)) <> lower(trim(coalesce(p.local_authority, '')))
                  )
                ORDER BY s.calculated_at DESC, s.id DESC
                LIMIT 1
                """
            ),
            {"parcel_id": int(parcel_id)},
        ).mappings().first()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"parcel {parcel_id} icin future growth skoru bulunamadi",
            )
        return dict(row)

    def get_parcel_evidence(self, parcel_id: int, *, score_id: int | None = None) -> list[dict[str, Any]]:
        resolved_score_id = int(score_id) if score_id is not None else int(self.get_latest_score(parcel_id)["id"])
        rows = self.session.execute(
            text(
                """
                SELECT
                  e.id,
                  e.parcel_id,
                  e.score_id,
                  e.factor_type,
                  e.evidence_title,
                  e.source_title,
                  e.source_url,
                  e.source_publisher,
                  e.publication_date,
                  e.data_date,
                  e.geography_level,
                  e.relation_type,
                  e.distance_m,
                  e.impact_weight,
                  e.extracted_claim,
                  e.confidence,
                  e.raw_json
                FROM parcel_future_growth_evidence e
                WHERE e.parcel_id = :parcel_id AND e.score_id = :score_id
                ORDER BY abs(coalesce(e.impact_weight, 0)) DESC, e.id ASC
                """
            ),
            {"parcel_id": int(parcel_id), "score_id": resolved_score_id},
        ).mappings().all()
        evidence_list: list[dict[str, Any]] = []
        for row in rows:
            data = dict(row)
            relation_type = str(data.get("relation_type") or "")
            geography_level = str(data.get("geography_level") or "")
            display_warning = None
            if relation_type == "SAME_LOCAL_AUTHORITY" or geography_level.upper() == "LOCAL_AUTHORITY":
                display_warning = PARCEL_GEOGRAPHY_WARNING
            data["relation_label"] = RELATION_TYPE_LABELS.get(relation_type, relation_type)
            data["display_warning"] = display_warning
            evidence_list.append(data)
        return evidence_list

    def get_parcel_detail(self, parcel_id: int) -> dict[str, Any]:
        score = self.get_latest_score(parcel_id)
        evidence_rows = self.get_parcel_evidence(parcel_id, score_id=int(score["id"]))
        top_reasons = self._build_top_reasons(evidence_rows)
        warnings: list[str] = []
        if any(row.get("display_warning") for row in evidence_rows):
            warnings.append(PARCEL_GEOGRAPHY_WARNING)
        if not evidence_rows:
            warnings.append("No parcel-specific evidence available.")
        missing_factors = self._missing_factor_warnings(evidence_rows)
        warnings.extend(missing_factors)
        deduped_warnings = list(dict.fromkeys(warnings))
        return {
            "parcel_id": int(score["parcel_id"]),
            "local_authority_code": score.get("local_authority_code"),
            "score_total": float(score["score_total"] or 0.0),
            "future_growth_percent": float(score["future_growth_percent"] or 0.0),
            "growth_probability_percent": None,
            "probability_not_calibrated": True,
            "score_breakdown": {
                "planning_growth_score": float(score["score_planning"] or 0.0),
                "transport_infra_score": float(score["score_transport"] or 0.0),
                "market_momentum_score": float(score["score_market"] or 0.0),
                "demographic_demand_score": float(score["score_demographic"] or 0.0),
                "social_amenity_score": float(score["score_social"] or 0.0),
                "land_supply_and_policy_score": float(score["score_policy"] or 0.0),
                "risk_penalty": float(score["risk_penalty"] or 0.0),
            },
            "confidence_score": float(score["confidence_score"] or 0.0),
            "color_class": score["color_class"],
            "hex_color": score["hex_color"],
            "color_explanation": self._color_explanation(score["color_class"]),
            "city_growth_direction_label": score.get("city_growth_direction_label") or "insufficient evidence",
            "top_reasons": top_reasons,
            "warnings": deduped_warnings,
            "evidence": evidence_rows,
            "calculation_version": score["calculation_version"],
            "horizon_years": int(score["horizon_years"] or self.settings.future_growth_default_horizon_years),
            "calculated_at": score["calculated_at"],
        }

    @staticmethod
    def _build_top_reasons(evidence_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, float] = defaultdict(float)
        sample_by_factor: dict[str, dict[str, Any]] = {}
        for row in evidence_rows:
            factor = str(row.get("factor_type") or "unknown")
            impact = float(row.get("impact_weight") or 0.0)
            grouped[factor] += impact
            sample_by_factor.setdefault(factor, row)
        ranked = sorted(grouped.items(), key=lambda item: abs(item[1]), reverse=True)[:6]
        output: list[dict[str, Any]] = []
        for factor, total_impact in ranked:
            sample = sample_by_factor.get(factor, {})
            output.append(
                {
                    "factor_type": factor,
                    "impact_weight_total": round(total_impact, 4),
                    "sample_evidence_title": sample.get("evidence_title"),
                    "sample_source_title": sample.get("source_title"),
                    "sample_relation_type": sample.get("relation_type"),
                }
            )
        return output

    @staticmethod
    def _missing_factor_warnings(evidence_rows: list[dict[str, Any]]) -> list[str]:
        present = {str(row.get("factor_type") or "") for row in evidence_rows}
        missing = []
        for factor in ("planning", "transport", "market", "demographic", "social", "policy"):
            if factor not in present:
                missing.append(f"{factor}: no parcel-specific evidence available.")
        return missing

    @staticmethod
    def _color_explanation(color_class: str) -> str:
        mapping = {
            "decline_very_high": "Dusus ya da zayiflama sinyali baskin.",
            "decline_risk": "Riskli/zayif gelisim sinyali.",
            "stagnant": "Duragan sinyal profili.",
            "limited_growth": "Sinirli yukselis potansiyeli.",
            "strong_growth": "Guclu yukselis sinyali.",
            "breakout_growth": "Cok yuksek gelisim/sicrama potansiyeli.",
        }
        return mapping.get(str(color_class), "Sinyal siniflandirmasi mevcut.")

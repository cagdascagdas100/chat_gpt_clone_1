from __future__ import annotations
import csv
import json
import os
import re
import datetime as dt
import time
from functools import lru_cache
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import and_, bindparam, case, desc, func, or_, select, text
from sqlalchemy.orm import Session

from app.db.geo import geometry_to_geojson
from app.db.models import (
    ParcelContextSummary,
    ListingParcelLink,
    ListingsGovernmentPropertyFinder,
    ListingsLandHub,
    ListingsMarketAdapter,
    ParcelInspire,
    ParcelSignalSummary,
    SitesBrownfieldLocalAuthority,
    SitesBrownfieldPlanningData,
    TransactionsPricePaid,
)
from app.schemas.common import LinkItem, WarningItem
from app.schemas.parcel import ParcelDetail, ParcelHistoryItem, ParcelListItem, ParcelSignalItem
from app.services.facility_service import get_parcel_context, get_parcel_scores, load_context_and_scores_map
from app.services.listing_area import extract_listing_area
from app.services.parcel_use_classifier import classify_parcel_use
from app.services.listing_truth import build_listing_truth_payload, has_price, sale_record_actionability_key
from app.services.planned_asset_service import get_parcel_future_intelligence_summary
from app.services.sale_link_utils import resolve_homes_england_external_link, resolve_market_external_link
from app.services.warnings import DEFAULT_WARNING_ITEMS

SOURCE_LINK_LABELS = {
    "homes_england_landhub": "Homes England Land Hub",
    "government_property_finder": "Government Property Finder",
    "planning_data_brownfield": "Planning Data Brownfield",
    "local_authority_brownfield": "Local Authority Brownfield Register",
    "hmlr_price_paid": "HM Land Registry Price Paid Data",
    "market_listing_adapter": "Licensed Market Listing",
}

SOURCE_DETAIL_MODELS = {
    "homes_england_landhub": ListingsLandHub,
    "government_property_finder": ListingsGovernmentPropertyFinder,
    "planning_data_brownfield": SitesBrownfieldPlanningData,
    "local_authority_brownfield": SitesBrownfieldLocalAuthority,
    "hmlr_price_paid": TransactionsPricePaid,
    "market_listing_adapter": ListingsMarketAdapter,
}


SALES_MATCH_MASTER_ROOT = Path(
    os.getenv("AAYS_SALES_MATCH_OUTPUT_ROOT", r"F:\AAYS_DATA\sales_match_program")
) / "master"
PARCEL_USE6_LOOKUP_JSON_CANDIDATES = [
    Path(__file__).resolve().parents[2] / "data" / "exports" / "parcel_use6" / "parcel_use6_lookup.json",
    Path(__file__).resolve().parents[2] / "docs" / "handoff_imports" / "20260523_parcel_label" / "zip_3_2" / "parcel_use6_lookup.json",
]
USE6_CODE_TO_NATIVE_LABEL = {
    "industrial": "industrial",
    "detached_residential": "residential",
    "apartment_residential": "residential",
    "retail": "retail",
    "office": "office",
    "mixed_use_vertical": "mixed_use",
    "unknown": "unknown",
}
USE6_ACCURACY_TO_CONFIDENCE = {
    "A_CERTAIN": 95.0,
    "B_HIGH": 85.0,
    "C_PARTIAL": 65.0,
    "D_UNKNOWN": 35.0,
}


def _safe_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed


@lru_cache(maxsize=1)
def _load_parcel_use6_lookup_map() -> dict[int, dict[str, Any]]:
    for candidate in PARCEL_USE6_LOOKUP_JSON_CANDIDATES:
        if not candidate.exists():
            continue
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        rows = payload.get("rows") if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            continue
        lookup: dict[int, dict[str, Any]] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            parcel_id = _safe_int(row.get("parcel_id"))
            if parcel_id is None:
                continue
            lookup[parcel_id] = row
        if lookup:
            return lookup
    return {}


def _parse_use6_triplet(text_value: Any) -> tuple[str | None, str | None, str | None]:
    text = str(text_value or "").strip()
    if not text:
        return None, None, None
    parts = [part.strip() for part in text.split("|")]
    if len(parts) >= 3:
        return parts[0] or None, parts[1] or None, parts[2] or None
    if len(parts) == 2:
        return parts[0] or None, parts[1] or None, None
    return parts[0] or None, None, None


def _parcel_use_from_lookup_row(row: dict[str, Any]) -> dict[str, Any]:
    label_tr, parsed_use6_code, parsed_color = _parse_use6_triplet(row.get("yapi_turu_ve_6_renk"))
    use6_code = str(row.get("use6_code") or parsed_use6_code or "unknown").strip().lower()
    native_label = str(row.get("native_label") or USE6_CODE_TO_NATIVE_LABEL.get(use6_code, "unknown")).strip().lower()
    accuracy_band = str(row.get("dogruluk_skalasi") or row.get("accuracy_band") or "D_UNKNOWN").strip().upper()
    confidence = _coerce_float(row.get("confidence")) or USE6_ACCURACY_TO_CONFIDENCE.get(accuracy_band, 35.0)
    evidence = {
        "source_kind": "parcel_use6_excel_lookup",
        "source_path": "data/exports/parcel_use6/parcel_use6_lookup.json",
        "use6_code": use6_code,
        "use6_label_tr": row.get("use6_label_tr") or label_tr,
        "use6_color_hex": row.get("use6_color_hex") or parsed_color,
        "accuracy_band": accuracy_band,
        "method_text": row.get("kaynak_ve_belirleme_yontemi"),
    }
    return {
        "label": native_label or "unknown",
        "confidence": confidence,
        "evidence": evidence,
    }


def _prefer_lookup_parcel_use(parcel_use: dict[str, Any] | None, parcel_id: int | None) -> dict[str, Any]:
    if parcel_id is None:
        return parcel_use or {}
    lookup_row = _load_parcel_use6_lookup_map().get(int(parcel_id))
    if lookup_row is None:
        return parcel_use or {}
    lookup_use = _parcel_use_from_lookup_row(lookup_row)
    current_label = str((parcel_use or {}).get("label") or "").strip().lower()
    lookup_label = str(lookup_use.get("label") or "").strip().lower()
    if current_label and current_label != "unknown":
        return parcel_use or {}
    if lookup_label and lookup_label != "unknown":
        return lookup_use
    if parcel_use:
        return parcel_use
    return lookup_use


def _load_parcel_use_cache_map(session: Session, parcel_ids: list[int]) -> dict[int, dict[str, Any]]:
    if not parcel_ids:
        return {}
    exists = session.scalar(text("select to_regclass('public.parcel_use_inference')"))
    if not exists:
        return {}
    stmt = text(
        """
        SELECT parcel_id, parcel_use_label, parcel_use_confidence, parcel_use_evidence
        FROM parcel_use_inference
        WHERE parcel_id IN :parcel_ids
        """
    ).bindparams(bindparam("parcel_ids", expanding=True))
    rows = session.execute(stmt, {"parcel_ids": [int(parcel_id) for parcel_id in parcel_ids]}).mappings().all()
    return {
        int(row["parcel_id"]): {
            "label": row["parcel_use_label"],
            "confidence": _coerce_float(row["parcel_use_confidence"]) or 0.0,
            "evidence": row["parcel_use_evidence"] if isinstance(row["parcel_use_evidence"], dict) else {},
        }
        for row in rows
    }


def _prefer_cached_parcel_use(cached_use: dict[str, Any] | None, computed_use: dict[str, Any]) -> dict[str, Any]:
    cached_label = str((cached_use or {}).get("label") or "").strip().lower()
    if cached_label and cached_label != "unknown":
        return cached_use or computed_use
    return computed_use


def _build_source_record_lookup(session: Session, links: list[ListingParcelLink]) -> dict[tuple[str, str], Any]:
    grouped_ids: dict[str, set[str]] = {}
    for link in links:
        grouped_ids.setdefault(link.source_name, set()).add(link.source_record_id)

    lookup: dict[tuple[str, str], Any] = {}
    for source_name, ids in grouped_ids.items():
        model = SOURCE_DETAIL_MODELS.get(source_name)
        if not model or not ids:
            continue
        key_attr = "listing_id" if hasattr(model, "listing_id") else "site_id" if hasattr(model, "site_id") else "transaction_id"
        rows = session.execute(select(model).where(getattr(model, key_attr).in_(ids))).scalars().all()
        for row in rows:
            lookup[(source_name, getattr(row, key_attr))] = row
    return lookup


def _build_truth_payload_for_source(link: ListingParcelLink, record: Any) -> dict[str, Any]:
    if link.source_name == "homes_england_landhub":
        external_url, _ = resolve_homes_england_external_link(record)
        return build_listing_truth_payload(
            source_name=link.source_name,
            ask_price=None,
            url=external_url or getattr(record, "source_url", None),
            provider_name="Homes England",
            provider_kind="official_export",
            license_scope="official_public",
            provider_listing_id=getattr(record, "site_reference", None),
            truth_tier="official",
            is_demo=False,
        )
    if link.source_name == "government_property_finder":
        return build_listing_truth_payload(
            source_name=link.source_name,
            ask_price=getattr(record, "ask_price", None),
            url=getattr(record, "listing_url", None) or getattr(record, "source_url", None),
            provider_name=getattr(record, "provider_name", None) or "Government Property Finder",
            provider_kind=getattr(record, "provider_kind", None) or "official_export",
            license_scope=getattr(record, "license_scope", None) or "government_export",
            provider_listing_id=getattr(record, "provider_listing_id", None),
            truth_tier=getattr(record, "truth_tier", None) or "official",
            is_demo=getattr(record, "is_demo", None),
        )
    if link.source_name == "market_listing_adapter":
        external_url, _ = resolve_market_external_link(record)
        return build_listing_truth_payload(
            source_name=link.source_name,
            ask_price=getattr(record, "ask_price", None),
            url=external_url or getattr(record, "listing_url", None) or getattr(record, "source_url", None),
            provider_name=getattr(record, "provider_name", None),
            provider_kind=getattr(record, "provider_kind", None),
            license_scope=getattr(record, "license_scope", None),
            provider_listing_id=getattr(record, "provider_listing_id", None),
            truth_tier=getattr(record, "truth_tier", None),
            is_demo=getattr(record, "is_demo", None),
        )
    return build_listing_truth_payload(
        source_name=link.source_name,
        ask_price=getattr(record, "ask_price", None),
        url=getattr(record, "source_url", None),
        provider_name=getattr(record, "provider_name", None),
        provider_kind=getattr(record, "provider_kind", None),
        license_scope=getattr(record, "license_scope", None),
        provider_listing_id=getattr(record, "provider_listing_id", None),
        truth_tier=getattr(record, "truth_tier", None),
        is_demo=getattr(record, "is_demo", None),
    )


def _serialize_source_record(link: ListingParcelLink, record: Any) -> dict[str, Any]:
    external_url = None
    external_label = None
    if record is not None and link.source_name == "homes_england_landhub":
        external_url, external_label = resolve_homes_england_external_link(record)
    elif record is not None and link.source_name == "market_listing_adapter":
        external_url, external_label = resolve_market_external_link(record)
    elif record is not None and link.source_name == "government_property_finder":
        external_url = getattr(record, "listing_url", None) or getattr(record, "source_url", None)
        external_label = "Government Property ilanina git" if external_url else None
    truth = _build_truth_payload_for_source(link, record)
    payload = {
        "source_name": link.source_name,
        "source_record_id": link.source_record_id,
        "match_method": link.match_method,
        "match_score": link.match_score,
        "confidence_score": link.confidence_score,
        "requires_review": link.requires_review,
        "source_url": getattr(record, "source_url", None) if record is not None else None,
        "external_url": external_url,
        "external_label": external_label,
        "source_updated_at": getattr(record, "source_updated_at", None) if record is not None else None,
        **truth,
    }
    if link.source_name == "homes_england_landhub":
        payload.update(
            {
                "record_type": "official_sale",
                "label": getattr(record, "parcel_name", None),
                "status": getattr(record, "marketing_status", None),
                "planning_status": getattr(record, "planning_status", None),
                "marketing_date": getattr(record, "marketing_date", None),
                "disposal_route": getattr(record, "disposal_route", None),
                "postcode": getattr(record, "postcode", None),
                "local_authority": getattr(record, "local_authority", None),
                "is_official": True,
            }
        )
    elif link.source_name == "government_property_finder":
        payload.update(
            {
                "record_type": "official_sale",
                "label": getattr(record, "title", None),
                "status": getattr(record, "listing_status", None),
                "ask_price": getattr(record, "ask_price", None),
                "listing_url": getattr(record, "listing_url", None),
                "provider_name": getattr(record, "provider_name", None) or "Government Property Finder",
                "postcode": getattr(record, "postcode", None),
                "local_authority": getattr(record, "local_authority", None),
                "is_official": True,
            }
        )
    elif link.source_name == "market_listing_adapter":
        listing_area_m2, listing_area_acres, listing_area_source = extract_listing_area(getattr(record, "metadata_json", None))
        payload.update(
            {
                "record_type": "market_listing",
                "label": getattr(record, "parcel_name", None) or getattr(record, "title", None),
                "status": getattr(record, "listing_status", None),
                "ask_price": getattr(record, "ask_price", None),
                "listing_area_m2": listing_area_m2,
                "listing_area_acres": listing_area_acres,
                "listing_area_source": listing_area_source,
                "listing_url": getattr(record, "listing_url", None),
                "provider_name": getattr(record, "provider_name", None),
                "provider_kind": getattr(record, "provider_kind", None),
                "license_scope": getattr(record, "license_scope", None),
                "provider_listing_id": getattr(record, "provider_listing_id", None),
                "postcode": getattr(record, "postcode", None),
                "local_authority": getattr(record, "local_authority", None),
                "is_official": False,
            }
        )
    elif link.source_name in {"planning_data_brownfield", "local_authority_brownfield"}:
        payload.update(
            {
                "record_type": "brownfield",
                "label": getattr(record, "reference", None) or getattr(record, "site_reference", None) or getattr(record, "site_name_address", None),
                "status": getattr(record, "planning_permission_status", None) or getattr(record, "planning_status", None),
                "planning_status": getattr(record, "planning_permission_status", None) or getattr(record, "planning_status", None),
                "ownership_status": getattr(record, "ownership_status", None),
                "hectares": getattr(record, "hectares", None),
                "site_plan_url": getattr(record, "site_plan_url", None),
                "is_official": link.source_name == "local_authority_brownfield",
            }
        )
    elif link.source_name == "hmlr_price_paid":
        payload.update(
            {
                "record_type": "history",
                "label": getattr(record, "address_text", None),
                "status": getattr(record, "transaction_category", None),
                "price_paid": getattr(record, "price_paid", None),
                "sale_date": getattr(record, "sale_date", None),
                "is_official": True,
            }
        )
    else:
        payload["record_type"] = "source"
        payload["label"] = None
        payload["status"] = None
    return payload


def _source_detail_url(source_name: str, source_record_id: str, parcel_id: int) -> str:
    if source_name in {"planning_data_brownfield", "local_authority_brownfield"}:
        return f"/brownfield-sites/{source_record_id}"
    if source_name == "hmlr_price_paid":
        return f"/parcels/{parcel_id}/history"
    return f"/listings/{source_record_id}"


def _matches_sale_record_filters(
    record: dict[str, Any],
    *,
    exclude_demo: bool,
    real_price_only: bool,
    source_tier: str | None,
) -> bool:
    if not isinstance(record, dict):
        return False
    tier = str(record.get("source_tier") or record.get("truth_tier") or "").strip().lower()
    is_demo = bool(record.get("is_demo")) or tier == "demo"
    if exclude_demo and is_demo:
        return False
    if source_tier and tier != source_tier:
        return False
    if real_price_only:
        price_truth = record.get("price_truth") if isinstance(record.get("price_truth"), dict) else {}
        if price_truth.get("is_real") is not True or not has_price(record.get("ask_price")):
            return False
    return True


def _filter_active_sale_records(
    records: list[dict[str, Any]] | None,
    *,
    exclude_demo: bool,
    real_price_only: bool,
    source_tier: str | None,
) -> list[dict[str, Any]]:
    return [
        record
        for record in (records or [])
        if _matches_sale_record_filters(
            record,
            exclude_demo=exclude_demo,
            real_price_only=real_price_only,
            source_tier=source_tier,
        )
    ]


def _build_filtered_sale_summary(
    source_summary: dict[str, Any] | None,
    *,
    exclude_demo: bool,
    real_price_only: bool,
    source_tier: str | None,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    summary = deepcopy(source_summary or {})
    all_active_sale_records = summary.get("active_sale_records", []) if isinstance(summary.get("active_sale_records"), list) else []
    filtered_active_sale_records = _filter_active_sale_records(
        all_active_sale_records,
        exclude_demo=exclude_demo,
        real_price_only=real_price_only,
        source_tier=source_tier,
    )
    official_visible_count = sum(1 for record in filtered_active_sale_records if record.get("source_tier") == "official")
    market_visible_count = sum(1 for record in filtered_active_sale_records if record.get("source_name") == "market_listing_adapter")
    sale_summary = deepcopy(summary.get("sale_summary") or {})
    top_actionable_listing = max(filtered_active_sale_records, key=sale_record_actionability_key) if filtered_active_sale_records else None
    top_actionable_truth = top_actionable_listing.get("price_truth") if isinstance(top_actionable_listing, dict) else {}
    visible_sale_count = len(filtered_active_sale_records)
    real_price_count = sum(
        1
        for record in filtered_active_sale_records
        if isinstance(record.get("price_truth"), dict) and record["price_truth"].get("is_real") is True and has_price(record.get("ask_price"))
    )
    sale_summary.update(
        {
            "active_sale_count": visible_sale_count,
            "visible_sale_count": visible_sale_count,
            "real_price_count": real_price_count,
            "official_sale_count": official_visible_count,
            "market_listing_count": market_visible_count,
            "top_actionable_listing": top_actionable_listing,
            "top_actionable_truth": top_actionable_truth or {},
            "latest_asking_price_gbp": top_actionable_listing.get("ask_price") if top_actionable_listing else None,
        }
    )
    summary["active_sale_records"] = filtered_active_sale_records
    summary["sale_summary"] = sale_summary
    return summary, filtered_active_sale_records, top_actionable_truth or {}


def _coerce_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _coerce_decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _coerce_date(value: Any) -> dt.date | None:
    if value in (None, ""):
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except Exception:
        return None


def _coerce_datetime(value: Any) -> dt.datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, dt.datetime):
        return value
    if isinstance(value, dt.date):
        return dt.datetime.combine(value, dt.time.min)
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def _reliability_band(value: float | None) -> str | None:
    if value is None:
        return None
    if value >= 90:
        return "HIGH"
    if value >= 75:
        return "MEDIUM"
    if value >= 60:
        return "LOW"
    return "VERY_LOW"


def _history_accuracy_scale(value: float | None) -> str:
    if value is None:
        return "D_UNKNOWN"
    if value >= 90:
        return "A_CERTAIN"
    if value >= 75:
        return "B_HIGH"
    if value >= 60:
        return "C_PARTIAL"
    return "D_UNKNOWN"


def _apply_history_accuracy_fields(item: ParcelHistoryItem) -> ParcelHistoryItem:
    overall_accuracy = _history_accuracy_scale(getattr(item, "correctness_likelihood_pct", None))
    has_source_url = _history_source_url_is_valid(getattr(item, "source_url", None))
    has_evidence_hash = bool(str(getattr(item, "evidence_hash", None) or "").strip())
    is_official_hmlr = _history_source_is_official_hmlr(getattr(item, "source_name", None))

    item.accuracy_scale = overall_accuracy
    item.area_accuracy = overall_accuracy if getattr(item, "building_area_m2", None) is not None else "D_UNKNOWN"
    item.price_accuracy = "A_CERTAIN" if is_official_hmlr and getattr(item, "price_paid", None) is not None else overall_accuracy
    item.parcel_match_accuracy = overall_accuracy
    item.evidence_accuracy = (
        "A_CERTAIN"
        if is_official_hmlr and has_source_url and has_evidence_hash
        else ("B_HIGH" if has_source_url and has_evidence_hash else "D_UNKNOWN")
    )
    item.sale_year_accuracy = "A_CERTAIN" if is_official_hmlr and getattr(item, "sale_date", None) is not None else overall_accuracy
    return item



def _history_record_is_rejected_duplicate(raw: dict[str, Any]) -> bool:
    decision = str(raw.get("quality_decision") or raw.get("decision") or "").strip().upper()
    notes = str(raw.get("notes") or raw.get("candidate_notes") or raw.get("match_notes") or "").upper()
    return decision == "REJECT_DUPLICATE" or "REJECT_DUPLICATE" in notes


def _history_source_url_is_valid(value: Any) -> bool:
    raw = str(value or "").strip()
    if not raw:
        return False
    lowered = raw.lower()
    if lowered in {"none", "null", "unknown", "n/a", "na"}:
        return False
    if lowered.startswith("file:"):
        return False
    if re.match(r"^[a-zA-Z]:[\\/]", raw):
        return False
    return lowered.startswith("http://") or lowered.startswith("https://")


def _history_source_is_candidate(value: Any) -> bool:
    raw = str(value or "").strip().upper()
    return (
        "TRANSACTION_HISTORY_CANDIDATE" in raw
        or "CANDIDATE" in raw
        or "PREVIEW" in raw
        or "STAGING" in raw
    )


def _history_source_is_official_hmlr(value: Any) -> bool:
    raw = str(value or "").strip().lower()
    return raw in {"hmlr_price_paid", "hm land registry price paid data", "hmlr_ppd", "price_paid_data"}


def _cap_history_confidence(
    *,
    source_name: Any,
    source_url: Any,
    evidence_hash: Any,
    reliability_score: Any,
    correctness_likelihood_pct: Any,
    requires_review: Any = False,
) -> tuple[float | None, float | None, str | None]:
    score = _coerce_float(reliability_score)
    correctness = _coerce_float(correctness_likelihood_pct)
    base = correctness if correctness is not None else score
    if base is None:
        return score, correctness, _reliability_band(correctness)

    has_url = _history_source_url_is_valid(source_url)
    has_evidence = bool(str(evidence_hash or "").strip())
    is_candidate = _history_source_is_candidate(source_name)
    is_official = _history_source_is_official_hmlr(source_name)
    review = bool(requires_review)

    cap = 100.0
    if not has_url and not has_evidence:
        cap = min(cap, 40.0)
    elif not has_url:
        cap = min(cap, 60.0)
    if not has_evidence:
        cap = min(cap, 75.0)
    if is_candidate:
        cap = min(cap, 60.0)
    if review:
        cap = min(cap, 60.0)

    capped = min(float(base), cap)

    # HIGH is reserved for official HMLR-like rows with usable source URL and evidence, not candidates/review rows.
    high_allowed = has_url and has_evidence and is_official and not is_candidate and not review
    if capped >= 90.0 and not high_allowed:
        capped = 89.0

    capped_score = min(score, capped) if score is not None else capped
    capped_correctness = capped
    return capped_score, capped_correctness, _reliability_band(capped_correctness)


def _apply_history_guardrails_to_items(items: list[ParcelHistoryItem]) -> list[ParcelHistoryItem]:
    for item in items:
        source_name = getattr(item, "source_name", None)
        source_url = getattr(item, "source_url", None)
        evidence_hash = getattr(item, "evidence_hash", None)
        score = getattr(item, "reliability_score", None)
        correctness = getattr(item, "correctness_likelihood_pct", None)
        capped_score, capped_correctness, band = _cap_history_confidence(
            source_name=source_name,
            source_url=source_url,
            evidence_hash=evidence_hash,
            reliability_score=score,
            correctness_likelihood_pct=correctness,
            requires_review=False,
        )
        try:
            item.reliability_score = capped_score
            item.correctness_likelihood_pct = capped_correctness
            item.reliability_band = band
            _apply_history_accuracy_fields(item)
        except Exception:
            pass
    return items


def _format_history_property_type_label(value: Any) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    upper = raw.upper()
    if upper == "D":
        return "Detached house"
    if upper == "S":
        return "Semi-detached house"
    if upper == "T":
        return "Terraced house"
    if upper == "F":
        return "Flat / apartment"
    if upper == "O":
        return "Other property"
    return raw


def _classify_history_building_class(property_type: Any, land_use_label: str | None) -> str:
    normalized_type = str(property_type or "").strip().lower()
    normalized_land_use = str(land_use_label or "").strip().lower()

    if normalized_type in {"d", "s", "t", "f"}:
        return "Residential building"
    if normalized_type == "o":
        return "Other building type"
    if any(token in normalized_type for token in ("industrial", "factory", "warehouse", "logistics", "sanayi")):
        return "Industrial building"
    if any(token in normalized_type for token in ("retail", "shop", "store", "market", "perakende")):
        return "Retail building"
    if any(token in normalized_type for token in ("office", "ofis")):
        return "Office building"
    if any(token in normalized_type for token in ("flat", "apartment", "apartman")):
        return "Apartment building"
    if any(token in normalized_type for token in ("detached", "house", "villa", "mustakil", "residential", "konut")):
        return "Residential building"

    if any(token in normalized_land_use for token in ("sanayi", "industrial")):
        return "Industrial land/building context"
    if any(token in normalized_land_use for token in ("perakende", "retail")):
        return "Retail land/building context"
    if any(token in normalized_land_use for token in ("tar", "agri", "farm")):
        return "Agricultural land context"
    if any(token in normalized_land_use for token in ("konut", "residential")):
        return "Residential land/building context"
    if any(token in normalized_land_use for token in ("karma", "mixed")):
        return "Mixed-use context"

    return "Unclassified building type"


def _apply_parcel_filters(
    stmt,
    *,
    inspire_id: str | None = None,
    parcel_ref: str | None = None,
    local_authority: str | None = None,
    parcel_area_min: float | None = None,
    parcel_area_max: float | None = None,
    min_confidence: float | None = None,
    max_confidence: float | None = None,
    brownfield_signal: bool | None = None,
    on_market_signal: bool | None = None,
    portal_listing_signal: bool | None = None,
    sale_ready_signal: bool | None = None,
    history_signal: bool | None = None,
    exclude_demo: bool = True,
    real_price_only: bool = False,
    source_tier: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
):
    sale_ready_fallback_expr = text(
        "exists (select 1 from parcel_external_market_evidence_summary eme where eme.parcel_id = parcels_inspire.parcel_id)"
    )
    history_fallback_expr = text(
        """
        exists (
          select 1
          from parcel_verified_sales_history_summary sh
          cross join lateral jsonb_array_elements(coalesce(sh.sales_history_records, '[]'::jsonb)) record
          where sh.parcel_id = parcels_inspire.parcel_id
            and coalesce(sh.best_sales_history_confidence_score, 0) >= 75
            and nullif(record->>'source_url', '') is not null
            and nullif(record->>'evidence_hash', '') is not null
            and upper(coalesce(record->>'source_name', record->>'source_type', '')) not like '%CANDIDATE%'
        )
        """
    )
    if inspire_id:
        stmt = stmt.where(or_(ParcelInspire.inspire_id == inspire_id, ParcelInspire.parcel_ref == inspire_id))
    if parcel_ref:
        stmt = stmt.where(or_(ParcelInspire.parcel_ref == parcel_ref, ParcelInspire.inspire_id == parcel_ref))
    if local_authority:
        stmt = stmt.where(ParcelInspire.local_authority.ilike(f"%{local_authority}%"))
    if parcel_area_min is not None:
        stmt = stmt.where(ParcelInspire.area_m2 >= parcel_area_min)
    if parcel_area_max is not None:
        stmt = stmt.where(ParcelInspire.area_m2 <= parcel_area_max)
    if min_confidence is not None:
        stmt = stmt.where(ParcelSignalSummary.highest_confidence_score >= min_confidence)
    if max_confidence is not None:
        stmt = stmt.where(ParcelSignalSummary.highest_confidence_score <= max_confidence)
    if brownfield_signal is not None:
        stmt = stmt.where(ParcelSignalSummary.brownfield_signal.is_(brownfield_signal))
    if on_market_signal is not None:
        stmt = stmt.where(ParcelSignalSummary.official_sale_signal.is_(on_market_signal))
    if portal_listing_signal is not None:
        non_demo_portal_visible = (
            func.coalesce(ParcelSignalSummary.licensed_sale_visible_count, 0)
            + func.coalesce(ParcelSignalSummary.manual_sale_visible_count, 0)
        )
        if exclude_demo:
            stmt = stmt.where((non_demo_portal_visible > 0) if portal_listing_signal else (non_demo_portal_visible == 0))
        else:
            stmt = stmt.where(ParcelSignalSummary.portal_listing_signal.is_(portal_listing_signal))
    if source_tier == "official":
        stmt = stmt.where(ParcelSignalSummary.official_sale_visible_count > 0)
    elif source_tier == "licensed":
        stmt = stmt.where(ParcelSignalSummary.licensed_sale_visible_count > 0)
    elif source_tier == "manual":
        stmt = stmt.where(ParcelSignalSummary.manual_sale_visible_count > 0)
    elif source_tier == "demo" and not exclude_demo:
        stmt = stmt.where(ParcelSignalSummary.demo_sale_count > 0)
    if real_price_only:
        stmt = stmt.where(ParcelSignalSummary.real_price_count > 0)
    if sale_ready_signal is not None:
        if exclude_demo or real_price_only or source_tier:
            if sale_ready_signal:
                stmt = stmt.where(or_(func.coalesce(ParcelSignalSummary.visible_sale_count, 0) > 0, sale_ready_fallback_expr))
            else:
                stmt = stmt.where(and_(func.coalesce(ParcelSignalSummary.visible_sale_count, 0) == 0, ~sale_ready_fallback_expr))
        else:
            if sale_ready_signal:
                stmt = stmt.where(
                    or_(
                        ParcelSignalSummary.official_sale_signal.is_(True),
                        ParcelSignalSummary.portal_listing_signal.is_(True),
                        sale_ready_fallback_expr,
                    )
                )
            else:
                stmt = stmt.where(
                    and_(
                        ParcelSignalSummary.official_sale_signal.is_(False),
                        ParcelSignalSummary.portal_listing_signal.is_(False),
                        ~sale_ready_fallback_expr,
                    )
                )
    if history_signal is not None:
        if history_signal:
            stmt = stmt.where(history_fallback_expr)
        else:
            stmt = stmt.where(~history_fallback_expr)
    if bbox:
        west, south, east, north = bbox
        envelope_27700 = func.ST_Transform(func.ST_MakeEnvelope(west, south, east, north, 4326), 27700)
        stmt = stmt.where(func.ST_Intersects(ParcelInspire.geometry, envelope_27700))
    return stmt



_DISTRICT_SALES_STOP_WORD_RE = re.compile(r"\b(COUNCIL|BOROUGH|DISTRICT|CITY|COUNTY|METROPOLITAN|OF|THE)\b", re.IGNORECASE)
_DISTRICT_SALES_NON_ALNUM_RE = re.compile(r"[^A-Z0-9]+")
_DISTRICT_SALES_CONTEXT_CACHE: dict[str, dict] | None = None


def _district_sales_key(value: str | None) -> str:
    raw = (value or "").upper()
    raw = _DISTRICT_SALES_STOP_WORD_RE.sub("", raw)
    raw = _DISTRICT_SALES_NON_ALNUM_RE.sub("", raw)
    return raw.strip()


def _district_context_confidence(row: dict) -> float:
    district_count = int(row.get("source_district_count") or 0)
    county_count = int(row.get("source_county_count") or 0)
    if district_count == 1 and county_count == 1:
        return 0.62
    if district_count == 1:
        return 0.55
    return 0.45


def _safe_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _safe_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _load_district_sales_context_lookup(session: Session) -> dict[str, dict]:
    global _DISTRICT_SALES_CONTEXT_CACHE
    if _DISTRICT_SALES_CONTEXT_CACHE is not None:
        return _DISTRICT_SALES_CONTEXT_CACHE

    sql = """
        select
          district_key,
          matched_district_label,
          county,
          tx_count,
          avg_price_gbp,
          min_sale_date,
          max_sale_date,
          tx_count_recent_5y,
          avg_price_recent_5y_gbp,
          source_district_count,
          source_county_count
        from district_sales_context
    """

    try:
        rows = session.connection().exec_driver_sql(sql).mappings().all()
    except Exception:
        _DISTRICT_SALES_CONTEXT_CACHE = {}
        return _DISTRICT_SALES_CONTEXT_CACHE

    lookup: dict[str, dict] = {}
    for row in rows:
        item = dict(row)
        key = str(item.get("district_key") or "").strip()
        if key:
            lookup[key] = item

    _DISTRICT_SALES_CONTEXT_CACHE = lookup
    return lookup


def _district_sales_context_for_local_authority(session: Session, local_authority: str | None) -> dict:
    key = _district_sales_key(local_authority)
    row = _load_district_sales_context_lookup(session).get(key)

    if not row:
        return {
            "district_sales_context_available": False,
            "district_sales_context_level": None,
            "district_sales_context_match_method": None,
            "district_sales_context_confidence": None,
            "district_sales_matched_district": None,
            "district_sales_county": None,
            "district_sales_tx_count": None,
            "district_sales_avg_price_gbp": None,
            "district_sales_recent_5y_count": None,
            "district_sales_recent_5y_avg_price_gbp": None,
            "district_sales_min_sale_date": None,
            "district_sales_max_sale_date": None,
        }

    return {
        "district_sales_context_available": True,
        "district_sales_context_level": "district",
        "district_sales_context_match_method": "local_authority_to_ppd_district",
        "district_sales_context_confidence": _district_context_confidence(row),
        "district_sales_matched_district": row.get("matched_district_label"),
        "district_sales_county": row.get("county"),
        "district_sales_tx_count": _safe_int(row.get("tx_count")),
        "district_sales_avg_price_gbp": _safe_float(row.get("avg_price_gbp")),
        "district_sales_recent_5y_count": _safe_int(row.get("tx_count_recent_5y")),
        "district_sales_recent_5y_avg_price_gbp": _safe_float(row.get("avg_price_recent_5y_gbp")),
        "district_sales_min_sale_date": str(row.get("min_sale_date")) if row.get("min_sale_date") is not None else None,
        "district_sales_max_sale_date": str(row.get("max_sale_date")) if row.get("max_sale_date") is not None else None,
    }


_EXTERNAL_MARKET_EVIDENCE_CACHE: dict[int, dict] | None = None


def _safe_float_or_none(value):
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _safe_int_or_none(value):
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _load_external_market_evidence_lookup(session: Session) -> dict[int, dict]:
    global _EXTERNAL_MARKET_EVIDENCE_CACHE
    if session is None:
        return {}
    if _EXTERNAL_MARKET_EVIDENCE_CACHE is not None:
        return _EXTERNAL_MARKET_EVIDENCE_CACHE

    sql = """
        select
          parcel_id,
          external_market_evidence_count,
          external_market_l2_count,
          external_market_l3_count,
          external_market_polygon_match_count,
          external_market_best_overlap_ratio,
          external_market_avg_overlap_ratio,
          external_market_best_confidence_score,
          coalesce(external_market_evidence_samples, '[]'::jsonb)::text as samples_json
        from parcel_external_market_evidence_summary
    """

    try:
        rows = session.connection().exec_driver_sql(sql).mappings().all()
    except Exception:
        _EXTERNAL_MARKET_EVIDENCE_CACHE = {}
        return _EXTERNAL_MARKET_EVIDENCE_CACHE

    lookup: dict[int, dict] = {}
    for row in rows:
        item = dict(row)
        parcel_id = item.get("parcel_id")
        if parcel_id is None:
            continue

        try:
            samples = json.loads(item.get("samples_json") or "[]")
        except Exception:
            samples = []

        lookup[int(parcel_id)] = {
            "external_market_evidence_available": True,
            "external_market_evidence_count": _safe_int_or_none(item.get("external_market_evidence_count")),
            "external_market_polygon_match_count": _safe_int_or_none(item.get("external_market_polygon_match_count")),
            "external_market_l2_count": _safe_int_or_none(item.get("external_market_l2_count")),
            "external_market_l3_count": _safe_int_or_none(item.get("external_market_l3_count")),
            "external_market_best_overlap_ratio": _safe_float_or_none(item.get("external_market_best_overlap_ratio")),
            "external_market_avg_overlap_ratio": _safe_float_or_none(item.get("external_market_avg_overlap_ratio")),
            "external_market_best_confidence_score": _safe_float_or_none(item.get("external_market_best_confidence_score")),
            "external_market_evidence_samples": samples,
        }

    _EXTERNAL_MARKET_EVIDENCE_CACHE = lookup
    return lookup


def _external_market_evidence_for_parcel(session: Session, parcel_id: int | None) -> dict:
    if parcel_id is None:
        return {
            "external_market_evidence_available": False,
            "external_market_evidence_count": None,
            "external_market_polygon_match_count": None,
            "external_market_l2_count": None,
            "external_market_l3_count": None,
            "external_market_best_overlap_ratio": None,
            "external_market_avg_overlap_ratio": None,
            "external_market_best_confidence_score": None,
            "external_market_evidence_samples": None,
        }

    return _load_external_market_evidence_lookup(session).get(int(parcel_id), {
        "external_market_evidence_available": False,
        "external_market_evidence_count": None,
        "external_market_polygon_match_count": None,
        "external_market_l2_count": None,
        "external_market_l3_count": None,
        "external_market_best_overlap_ratio": None,
        "external_market_avg_overlap_ratio": None,
        "external_market_best_confidence_score": None,
        "external_market_evidence_samples": None,
    })


_VERIFIED_SALES_HISTORY_CACHE: dict[int, dict] | None = None
_VERIFIED_SALES_HISTORY_CACHE_LOADED_AT: float | None = None
_VERIFIED_SALES_HISTORY_CACHE_TTL_SECONDS = 30.0


def invalidate_verified_sales_history_cache() -> None:
    global _VERIFIED_SALES_HISTORY_CACHE, _VERIFIED_SALES_HISTORY_CACHE_LOADED_AT
    _VERIFIED_SALES_HISTORY_CACHE = None
    _VERIFIED_SALES_HISTORY_CACHE_LOADED_AT = None


def _load_verified_sales_history_lookup(session: Session) -> dict[int, dict]:
    global _VERIFIED_SALES_HISTORY_CACHE, _VERIFIED_SALES_HISTORY_CACHE_LOADED_AT
    if session is None:
        return {}
    if (
        _VERIFIED_SALES_HISTORY_CACHE is not None
        and _VERIFIED_SALES_HISTORY_CACHE_LOADED_AT is not None
        and (time.monotonic() - _VERIFIED_SALES_HISTORY_CACHE_LOADED_AT) < _VERIFIED_SALES_HISTORY_CACHE_TTL_SECONDS
    ):
        return _VERIFIED_SALES_HISTORY_CACHE

    candidate_sql_list = [
        """
        select
          parcel_id,
          sales_history_count,
          latest_sale_year,
          latest_sale_date::text as latest_sale_date,
          latest_sale_price_gbp,
          latest_sale_area_m2,
          latest_sale_price_per_m2_gbp,
          latest_sale_property_type,
          best_sales_history_confidence_score,
          coalesce(sales_history_records, '[]'::jsonb)::text as records_json
        from parcel_verified_sales_history_summary
        """,
    ]
    rows = None
    for candidate_sql in candidate_sql_list:
        try:
            rows = session.connection().exec_driver_sql(candidate_sql).mappings().all()
            break
        except Exception:
            rows = None
    if rows is None:
        _VERIFIED_SALES_HISTORY_CACHE = {}
        _VERIFIED_SALES_HISTORY_CACHE_LOADED_AT = time.monotonic()
        return _VERIFIED_SALES_HISTORY_CACHE

    lookup: dict[int, dict] = {}
    for row in rows:
        item = dict(row)
        parcel_id = item.get("parcel_id")
        if parcel_id is None:
            continue

        try:
            records = json.loads(item.get("records_json") or "[]")
        except Exception:
            records = []

        guarded_records = []
        guarded_scores = []
        for raw in records:
            if not isinstance(raw, dict) or _history_record_is_rejected_duplicate(raw):
                continue
            source_name = raw.get("source_name") or raw.get("source_type")
            score, correctness, band = _cap_history_confidence(
                source_name=source_name,
                source_url=raw.get("source_url"),
                evidence_hash=raw.get("evidence_hash"),
                reliability_score=raw.get("reliability_score") or raw.get("source_confidence_score"),
                correctness_likelihood_pct=raw.get("correctness_likelihood_pct"),
                requires_review=raw.get("requires_review") or raw.get("review_required"),
            )
            accuracy_scale = _history_accuracy_scale(correctness)
            if accuracy_scale not in {"A_CERTAIN", "B_HIGH"}:
                continue
            guarded = dict(raw)
            guarded["reliability_score"] = score
            guarded["correctness_likelihood_pct"] = correctness
            guarded["reliability_band"] = band
            guarded["accuracy_scale"] = accuracy_scale
            guarded_records.append(guarded)
            if correctness is not None:
                guarded_scores.append(float(correctness))

        # Summary rows are publishable only when at least one evidence-backed A/B record survives.
        if not guarded_records:
            continue

        score = max(guarded_scores) if guarded_scores else item.get("best_sales_history_confidence_score")
        level = None
        if score is not None:
            try:
                s = float(score)
                level = "L4" if s >= 0.85 else ("L3" if s >= 0.65 else ("L2" if s >= 0.40 else "L1"))
            except Exception:
                level = None

        lookup[int(parcel_id)] = {
            "sales_history_available": True,
            "sales_history_count": int(item["sales_history_count"]) if item.get("sales_history_count") is not None else None,
            "latest_sale_year": int(item["latest_sale_year"]) if item.get("latest_sale_year") is not None else None,
            "latest_sale_date": item.get("latest_sale_date"),
            "latest_sale_price_gbp": float(item["latest_sale_price_gbp"]) if item.get("latest_sale_price_gbp") is not None else None,
            "latest_sale_area_m2": float(item["latest_sale_area_m2"]) if item.get("latest_sale_area_m2") is not None else None,
            "latest_sale_price_per_m2_gbp": float(item["latest_sale_price_per_m2_gbp"]) if item.get("latest_sale_price_per_m2_gbp") is not None else None,
            "latest_sale_property_type": item.get("latest_sale_property_type"),
            "sales_history_confidence_level": level,
            "sales_history_confidence_score": float(score) if score is not None else None,
            "sales_history_records": guarded_records,
        }

    _VERIFIED_SALES_HISTORY_CACHE = lookup
    _VERIFIED_SALES_HISTORY_CACHE_LOADED_AT = time.monotonic()
    return lookup


def _verified_sales_history_for_parcel(session: Session, parcel_id: int | None) -> dict:
    empty = {
        "sales_history_available": False,
        "sales_history_count": None,
        "latest_sale_year": None,
        "latest_sale_date": None,
        "latest_sale_price_gbp": None,
        "latest_sale_area_m2": None,
        "latest_sale_price_per_m2_gbp": None,
        "latest_sale_property_type": None,
        "sales_history_confidence_level": None,
        "sales_history_confidence_score": None,
        "sales_history_records": None,
    }
    if parcel_id is None:
        return empty
    return _load_verified_sales_history_lookup(session).get(int(parcel_id), empty)

def list_parcels(
    session: Session,
    external_market_signal: bool = False,
    sales_history_signal: bool = False,
    *,
    inspire_id: str | None = None,
    parcel_ref: str | None = None,
    local_authority: str | None = None,
    parcel_area_min: float | None = None,
    parcel_area_max: float | None = None,
    min_confidence: float | None = None,
    max_confidence: float | None = None,
    brownfield_signal: bool | None = None,
    on_market_signal: bool | None = None,
    portal_listing_signal: bool | None = None,
    sale_ready_signal: bool | None = None,
    history_signal: bool | None = None,
    exclude_demo: bool = True,
    real_price_only: bool = False,
    source_tier: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    limit: int = 100,
    offset: int = 0,
    include_total: bool = True,
    fast_mode: bool = False,
) -> tuple[list[ParcelListItem], int]:
    geometry_expr = func.ST_AsGeoJSON(
        case(
            (func.ST_SRID(ParcelInspire.geometry) == 4326, ParcelInspire.geometry),
            (func.ST_SRID(ParcelInspire.geometry) == 0, func.ST_SetSRID(ParcelInspire.geometry, 4326)),
            else_=func.ST_Transform(ParcelInspire.geometry, 4326),
        )
    ).label("geometry_geojson")
    stmt = (
        select(ParcelInspire, ParcelSignalSummary, geometry_expr)
        .outerjoin(ParcelSignalSummary, ParcelSignalSummary.parcel_id == ParcelInspire.parcel_id)
        .order_by(ParcelInspire.parcel_id.asc())
    )
    if external_market_signal:
        external_market_session = locals().get("session") or locals().get("db")
        external_market_ids = list(_load_external_market_evidence_lookup(external_market_session).keys()) if external_market_session is not None else []
        if external_market_ids:
            stmt = stmt.where(ParcelInspire.parcel_id.in_(external_market_ids))
        else:
            stmt = stmt.where(ParcelInspire.parcel_id == -1)

    if sales_history_signal:
        sales_history_session = locals().get("session") or locals().get("db")
        sales_history_ids = list(_load_verified_sales_history_lookup(sales_history_session).keys()) if sales_history_session is not None else []
        if sales_history_ids:
            stmt = stmt.where(ParcelInspire.parcel_id.in_(sales_history_ids))
        else:
            stmt = stmt.where(ParcelInspire.parcel_id == -1)



    stmt = _apply_parcel_filters(
        stmt,
        inspire_id=inspire_id,
        parcel_ref=parcel_ref,
        local_authority=local_authority,
        parcel_area_min=parcel_area_min,
        parcel_area_max=parcel_area_max,
        min_confidence=min_confidence,
        max_confidence=max_confidence,
        brownfield_signal=brownfield_signal,
        on_market_signal=on_market_signal,
        portal_listing_signal=portal_listing_signal,
        sale_ready_signal=sale_ready_signal,
        history_signal=history_signal,
        exclude_demo=exclude_demo,
        real_price_only=real_price_only,
        source_tier=source_tier,
        bbox=bbox,
    )
    total = (session.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0) if include_total else 0




    rows = session.execute(stmt.offset(offset).limit(limit)).all()
    parcel_ids = [parcel.parcel_id for parcel, _, _ in rows]
    parcel_use_cache_map = _load_parcel_use_cache_map(session, parcel_ids) if not fast_mode else {}
    uncached_parcel_ids = [
        parcel_id
        for parcel_id in parcel_ids
        if str((parcel_use_cache_map.get(parcel_id) or {}).get("label") or "").strip().lower() in {"", "unknown"}
    ] if not fast_mode else []
    context_map, score_map = (
        load_context_and_scores_map(session, uncached_parcel_ids, refresh_missing=False)
        if (not fast_mode and uncached_parcel_ids)
        else ({}, {})
    )
    items = []
    for parcel, summary, geometry_json in rows:
        cached_parcel_use = parcel_use_cache_map.get(parcel.parcel_id) if not fast_mode else None
        context_summary = context_map.get(parcel.parcel_id) if not fast_mode else None
        scenario_scores = (
            {item.profile_code: item.score_total for item in score_map.get(parcel.parcel_id, [])}
            if not fast_mode
            else {}
        )
        if fast_mode:
            parcel_use: dict[str, Any] = {}
        elif str((cached_parcel_use or {}).get("label") or "").strip().lower() not in {"", "unknown"}:
            parcel_use = cached_parcel_use or {}
        else:
            computed_parcel_use = classify_parcel_use(context_summary, scenario_scores)
            parcel_use = _prefer_cached_parcel_use(cached_parcel_use, computed_parcel_use)
        if not fast_mode:
            parcel_use = _prefer_lookup_parcel_use(parcel_use, parcel.parcel_id)
        filtered_source_summary, filtered_sale_records, top_actionable_truth = _build_filtered_sale_summary(
            summary.source_summary if summary and summary.source_summary else {},
            exclude_demo=exclude_demo,
            real_price_only=real_price_only,
            source_tier=source_tier,
        )
        history_summary = filtered_source_summary.get("history_summary", {}) if isinstance(filtered_source_summary, dict) else {}
        external_market_evidence = _external_market_evidence_for_parcel((locals().get("session") or locals().get("db")), parcel.parcel_id)
        sales_history = _verified_sales_history_for_parcel((locals().get("session") or locals().get("db")), parcel.parcel_id)
        history_count = summary.history_transaction_count if summary else 0
        history_count_fallback = sales_history.get("sales_history_count")
        if (history_count or 0) <= 0 and history_count_fallback is not None:
            history_count = int(history_count_fallback)
        latest_history_sale_date = history_summary.get("latest_sale_date") or _coerce_date(sales_history.get("latest_sale_date"))
        latest_history_price_paid = _coerce_decimal(history_summary.get("latest_price_paid"))
        if latest_history_price_paid is None:
            latest_history_price_paid = _coerce_decimal(sales_history.get("latest_sale_price_gbp"))
        latest_history_property_type = history_summary.get("latest_property_type") or sales_history.get("latest_sale_property_type")
        parcel_use_label = parcel_use.get("label")
        latest_history_property_type_label = _format_history_property_type_label(latest_history_property_type)
        latest_history_building_class_label = _classify_history_building_class(latest_history_property_type, parcel_use_label)
        latest_history_tenure = history_summary.get("latest_tenure")
        latest_history_location = history_summary.get("latest_location")
        latest_history_area_m2 = _coerce_float(history_summary.get("latest_area_m2"))
        if latest_history_area_m2 is None:
            latest_history_area_m2 = _coerce_float(sales_history.get("latest_sale_area_m2"))
        latest_history_price_per_m2 = _coerce_float(history_summary.get("latest_price_per_m2"))
        if latest_history_price_per_m2 is None:
            latest_history_price_per_m2 = _coerce_float(sales_history.get("latest_sale_price_per_m2_gbp"))
        district_sales_context = _district_sales_context_for_local_authority(session, parcel.local_authority)
        effective_visible_sale_count = len(filtered_sale_records)
        if effective_visible_sale_count == 0 and external_market_evidence.get("external_market_evidence_available"):
            effective_visible_sale_count = int(external_market_evidence.get("external_market_evidence_count") or 1)
        effective_sale_summary = deepcopy(filtered_source_summary.get("sale_summary", {}) if isinstance(filtered_source_summary, dict) else {})
        if effective_sale_summary.get("visible_sale_count") in (None, 0) and effective_visible_sale_count > 0:
            effective_sale_summary["visible_sale_count"] = effective_visible_sale_count
            effective_sale_summary["active_sale_count"] = effective_visible_sale_count
        effective_highest_confidence = summary.highest_confidence_score if summary else None
        if effective_highest_confidence is None:
            effective_highest_confidence = external_market_evidence.get("external_market_best_confidence_score") or sales_history.get("sales_history_confidence_score")
        items.append(
            ParcelListItem(
                parcel_id=parcel.parcel_id,
                inspire_id=parcel.inspire_id or f"parcel:{parcel.parcel_id}",
                parcel_ref=parcel.parcel_ref or parcel.inspire_id or f"parcel:{parcel.parcel_id}",
                local_authority=parcel.local_authority,
                area_m2=parcel.area_m2,
                perimeter_m=parcel.perimeter_m,
                sale_ready_signal=bool(filtered_sale_records) or bool(external_market_evidence.get("external_market_evidence_available")),
                official_sale_signal=bool(summary.official_sale_signal) if summary else False,
                brownfield_signal=bool(summary.brownfield_signal) if summary else False,
                portal_listing_signal=(bool(filtered_source_summary.get("sale_summary", {}).get("market_listing_count")) if summary else False)
                or bool(external_market_evidence.get("external_market_evidence_available")),
                highest_confidence_score=effective_highest_confidence,
                last_updated=summary.latest_source_updated_at if summary else None,
                requires_review=bool(summary.requires_review) if summary else False,
                visible_sale_count=effective_visible_sale_count,
                real_price_count=effective_sale_summary.get("real_price_count", 0),
                history_transaction_count=history_count or 0,
                latest_history_sale_date=latest_history_sale_date,
                latest_history_price_paid=latest_history_price_paid,
                latest_history_property_type=latest_history_property_type,
                latest_history_property_type_label=latest_history_property_type_label,
                latest_history_building_class_label=latest_history_building_class_label,
                latest_history_land_use_label=parcel_use_label,
                latest_history_tenure=latest_history_tenure,
                latest_history_location=latest_history_location,
                latest_history_area_m2=latest_history_area_m2,
                latest_history_price_per_m2=latest_history_price_per_m2,
                top_actionable_truth=top_actionable_truth,
                sale_summary=effective_sale_summary,
                dominant_context=context_summary.dominant_context_code if context_summary else None,
                nuisance_score=context_summary.nuisance_score if context_summary else None,
                accessibility_score=context_summary.accessibility_score if context_summary else None,
                scenario_scores=scenario_scores,
                parcel_use_label=parcel_use_label,
                parcel_use_confidence=parcel_use.get("confidence"),
                parcel_use_evidence=dict(parcel_use.get("evidence") or {}),
                district_sales_context_available=district_sales_context.get("district_sales_context_available", False),
                district_sales_context_level=district_sales_context.get("district_sales_context_level"),
                district_sales_context_match_method=district_sales_context.get("district_sales_context_match_method"),
                district_sales_context_confidence=district_sales_context.get("district_sales_context_confidence"),
                district_sales_matched_district=district_sales_context.get("district_sales_matched_district"),
                district_sales_county=district_sales_context.get("district_sales_county"),
                district_sales_tx_count=district_sales_context.get("district_sales_tx_count"),
                district_sales_avg_price_gbp=district_sales_context.get("district_sales_avg_price_gbp"),
                district_sales_recent_5y_count=district_sales_context.get("district_sales_recent_5y_count"),
                district_sales_recent_5y_avg_price_gbp=district_sales_context.get("district_sales_recent_5y_avg_price_gbp"),
                district_sales_min_sale_date=district_sales_context.get("district_sales_min_sale_date"),
                district_sales_max_sale_date=district_sales_context.get("district_sales_max_sale_date"),
                                        sales_history_available=sales_history.get("sales_history_available", False),
                sales_history_count=sales_history.get("sales_history_count"),
                latest_sale_year=sales_history.get("latest_sale_year"),
                latest_sale_date=sales_history.get("latest_sale_date"),
                latest_sale_price_gbp=sales_history.get("latest_sale_price_gbp"),
                latest_sale_area_m2=sales_history.get("latest_sale_area_m2"),
                latest_sale_price_per_m2_gbp=sales_history.get("latest_sale_price_per_m2_gbp"),
                latest_sale_property_type=sales_history.get("latest_sale_property_type"),
                sales_history_confidence_level=sales_history.get("sales_history_confidence_level"),
                sales_history_confidence_score=sales_history.get("sales_history_confidence_score"),
                sales_history_records=sales_history.get("sales_history_records"),
external_market_evidence_available=external_market_evidence.get("external_market_evidence_available", False),
                external_market_evidence_count=external_market_evidence.get("external_market_evidence_count"),
                external_market_polygon_match_count=external_market_evidence.get("external_market_polygon_match_count"),
                external_market_l2_count=external_market_evidence.get("external_market_l2_count"),
                external_market_l3_count=external_market_evidence.get("external_market_l3_count"),
                external_market_best_overlap_ratio=external_market_evidence.get("external_market_best_overlap_ratio"),
                external_market_avg_overlap_ratio=external_market_evidence.get("external_market_avg_overlap_ratio"),
                external_market_best_confidence_score=external_market_evidence.get("external_market_best_confidence_score"),
                external_market_evidence_samples=external_market_evidence.get("external_market_evidence_samples"),
geometry=geometry_to_geojson(geometry_json),
            )
        )
    return items, total


def get_parcel_detail(session: Session, parcel_id: int) -> ParcelDetail:
    geometry_expr = func.ST_AsGeoJSON(
        case(
            (func.ST_SRID(ParcelInspire.geometry) == 4326, ParcelInspire.geometry),
            (func.ST_SRID(ParcelInspire.geometry) == 0, func.ST_SetSRID(ParcelInspire.geometry, 4326)),
            else_=func.ST_Transform(ParcelInspire.geometry, 4326),
        )
    ).label("geometry_geojson")
    centroid_expr = func.ST_AsGeoJSON(
        case(
            (ParcelInspire.centroid.is_(None), None),
            (func.ST_SRID(ParcelInspire.centroid) == 4326, ParcelInspire.centroid),
            (func.ST_SRID(ParcelInspire.centroid) == 0, func.ST_SetSRID(ParcelInspire.centroid, 4326)),
            else_=func.ST_Transform(ParcelInspire.centroid, 4326),
        )
    ).label("centroid_geojson")
    row = session.execute(
        select(ParcelInspire, ParcelSignalSummary, geometry_expr, centroid_expr)
        .outerjoin(ParcelSignalSummary, ParcelSignalSummary.parcel_id == ParcelInspire.parcel_id)
        .where(ParcelInspire.parcel_id == parcel_id)
    ).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found")
    parcel, summary, geometry_json, centroid_json = row
    warnings = [WarningItem(**item) for item in DEFAULT_WARNING_ITEMS]
    if summary and summary.warnings:
        warnings.extend(WarningItem(code="source_summary", message=str(msg)) for msg in summary.warnings)
    filtered_source_summary, _, _ = _build_filtered_sale_summary(
        summary.source_summary if summary and summary.source_summary else {},
        exclude_demo=True,
        real_price_only=False,
        source_tier=None,
    )
    context_summary = get_parcel_context(session, parcel_id)
    scenario_scores = get_parcel_scores(session, parcel_id)
    computed_parcel_use = classify_parcel_use(context_summary, scenario_scores)
    parcel_use = _prefer_cached_parcel_use(_load_parcel_use_cache_map(session, [parcel_id]).get(parcel_id), computed_parcel_use)
    parcel_use = _prefer_lookup_parcel_use(parcel_use, parcel_id)
    district_sales_context = _district_sales_context_for_local_authority(session, parcel.local_authority)
    external_market_evidence = _external_market_evidence_for_parcel((locals().get("session") or locals().get("db")), parcel.parcel_id)
    sales_history = _verified_sales_history_for_parcel((locals().get("session") or locals().get("db")), parcel.parcel_id)
    future_summary = get_parcel_future_intelligence_summary(session, parcel.parcel_id)
    return ParcelDetail(
        parcel_id=parcel.parcel_id,
        inspire_id=parcel.inspire_id,
        parcel_ref=parcel.parcel_ref,
        local_authority=parcel.local_authority,
        postcode=parcel.postcode,
        address_text=parcel.address_text,
        area_m2=parcel.area_m2,
        perimeter_m=parcel.perimeter_m,
        district_sales_context_available=district_sales_context.get("district_sales_context_available", False),
        district_sales_context_level=district_sales_context.get("district_sales_context_level"),
        district_sales_context_match_method=district_sales_context.get("district_sales_context_match_method"),
        district_sales_context_confidence=district_sales_context.get("district_sales_context_confidence"),
        district_sales_matched_district=district_sales_context.get("district_sales_matched_district"),
        district_sales_county=district_sales_context.get("district_sales_county"),
        district_sales_tx_count=district_sales_context.get("district_sales_tx_count"),
        district_sales_avg_price_gbp=district_sales_context.get("district_sales_avg_price_gbp"),
        district_sales_recent_5y_count=district_sales_context.get("district_sales_recent_5y_count"),
        district_sales_recent_5y_avg_price_gbp=district_sales_context.get("district_sales_recent_5y_avg_price_gbp"),
        district_sales_min_sale_date=district_sales_context.get("district_sales_min_sale_date"),
        district_sales_max_sale_date=district_sales_context.get("district_sales_max_sale_date"),
                        sales_history_available=sales_history.get("sales_history_available", False),
        sales_history_count=sales_history.get("sales_history_count"),
        latest_sale_year=sales_history.get("latest_sale_year"),
        latest_sale_date=sales_history.get("latest_sale_date"),
        latest_sale_price_gbp=sales_history.get("latest_sale_price_gbp"),
        latest_sale_area_m2=sales_history.get("latest_sale_area_m2"),
        latest_sale_price_per_m2_gbp=sales_history.get("latest_sale_price_per_m2_gbp"),
        latest_sale_property_type=sales_history.get("latest_sale_property_type"),
        sales_history_confidence_level=sales_history.get("sales_history_confidence_level"),
        sales_history_confidence_score=sales_history.get("sales_history_confidence_score"),
        sales_history_records=sales_history.get("sales_history_records"),
external_market_evidence_available=external_market_evidence.get("external_market_evidence_available", False),
        external_market_evidence_count=external_market_evidence.get("external_market_evidence_count"),
        external_market_polygon_match_count=external_market_evidence.get("external_market_polygon_match_count"),
        external_market_l2_count=external_market_evidence.get("external_market_l2_count"),
        external_market_l3_count=external_market_evidence.get("external_market_l3_count"),
        external_market_best_overlap_ratio=external_market_evidence.get("external_market_best_overlap_ratio"),
        external_market_avg_overlap_ratio=external_market_evidence.get("external_market_avg_overlap_ratio"),
        external_market_best_confidence_score=external_market_evidence.get("external_market_best_confidence_score"),
        external_market_evidence_samples=external_market_evidence.get("external_market_evidence_samples"),
geometry=geometry_to_geojson(geometry_json),
        centroid=geometry_to_geojson(centroid_json),
        source_summary=filtered_source_summary,
        warnings=warnings,
        last_updated=summary.latest_source_updated_at if summary else None,
        confidence_score=summary.highest_confidence_score if summary else None,
        requires_review=bool(summary.requires_review) if summary else False,
        dominant_context=context_summary.dominant_context_code if context_summary else None,
        nuisance_score=context_summary.nuisance_score if context_summary else None,
        accessibility_score=context_summary.accessibility_score if context_summary else None,
        context_summary=context_summary,
        scenario_scores=scenario_scores,
        parcel_use_label=parcel_use.get("label"),
        parcel_use_confidence=parcel_use.get("confidence"),
        parcel_use_evidence=dict(parcel_use.get("evidence") or {}),
        future_intelligence_summary=future_summary,
    )


def get_parcel_signals(session: Session, parcel_id: int) -> ParcelSignalItem:
    parcel = session.get(ParcelInspire, parcel_id)
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found")
    summary = session.get(ParcelSignalSummary, parcel_id)
    links = session.execute(
        select(ListingParcelLink)
        .where(ListingParcelLink.parcel_id == parcel_id)
        .order_by(desc(ListingParcelLink.confidence_score), ListingParcelLink.source_name.asc())
    ).scalars().all()
    record_lookup = _build_source_record_lookup(session, links)

    source_links: list[LinkItem] = []
    sources: list[dict[str, Any]] = []
    freshness: dict[str, Any] = {}
    for link in links:
        source_links.append(LinkItem(label=SOURCE_LINK_LABELS.get(link.source_name, link.source_name), url=_source_detail_url(link.source_name, link.source_record_id, parcel_id)))
        record_summary = _serialize_source_record(link, record_lookup.get((link.source_name, link.source_record_id)))
        freshness[link.source_name] = {
            "match_method": link.match_method,
            "match_score": link.match_score,
            "confidence_score": link.confidence_score,
            "requires_review": link.requires_review,
        }
        sources.append(
            {
                "source_name": link.source_name,
                "source_record_id": link.source_record_id,
                "match_method": link.match_method,
                "match_score": link.match_score,
                "confidence_score": link.confidence_score,
                "requires_review": link.requires_review,
                "record_summary": record_summary,
                "source_url": record_summary.get("source_url"),
            }
        )

    warnings = [WarningItem(**item) for item in DEFAULT_WARNING_ITEMS]
    if summary and summary.requires_review:
        warnings.append(WarningItem(code="requires_review", message="Some parcel-to-source matches are inferred and require review."))

    filtered_source_summary, filtered_sale_records, top_actionable_truth = _build_filtered_sale_summary(
        summary.source_summary if summary and summary.source_summary else {},
        exclude_demo=True,
        real_price_only=False,
        source_tier=None,
    )
    return ParcelSignalItem(
        parcel_id=parcel.parcel_id,
        inspire_id=parcel.inspire_id,
        parcel_ref=parcel.parcel_ref,
        official_sale_signal=bool(summary.official_sale_signal) if summary else False,
        official_sale_status=summary.official_sale_status if summary else None,
        brownfield_signal=bool(summary.brownfield_signal) if summary else False,
        portal_listing_signal=bool(filtered_source_summary.get("sale_summary", {}).get("market_listing_count")) if summary else False,
        confidence_score=summary.highest_confidence_score if summary else None,
        latest_source_updated_at=summary.latest_source_updated_at if summary else None,
        visible_sale_count=len(filtered_sale_records),
        real_price_count=filtered_source_summary.get("sale_summary", {}).get("real_price_count", 0),
        top_actionable_truth=top_actionable_truth,
        source_summary=filtered_source_summary,
        sale_records=filtered_sale_records,
        brownfield_records=((summary.source_summary or {}).get("brownfield_records", []) if summary and summary.source_summary else []),
        source_links=source_links,
        warnings=warnings,
        sources=sources,
        freshness=freshness,
    )


def get_parcel_history(session: Session, parcel_id: int) -> list[ParcelHistoryItem]:
    parcel = session.get(ParcelInspire, parcel_id)
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found")
    context_summary = get_parcel_context(session, parcel_id)
    scenario_scores = get_parcel_scores(session, parcel_id)
    computed_parcel_use = classify_parcel_use(context_summary, scenario_scores)
    parcel_use = _prefer_cached_parcel_use(
        _load_parcel_use_cache_map(session, [parcel_id]).get(parcel_id),
        computed_parcel_use,
    )
    parcel_use = _prefer_lookup_parcel_use(parcel_use, parcel_id)
    parcel_use_label = str(parcel_use.get("label") or "").strip() or None
    stmt = (
        select(TransactionsPricePaid)
        .join(
            ListingParcelLink,
            (ListingParcelLink.source_name == "hmlr_price_paid")
            & (ListingParcelLink.source_record_id == TransactionsPricePaid.transaction_id),
        )
        .where(ListingParcelLink.parcel_id == parcel_id)
        .order_by(desc(TransactionsPricePaid.sale_date))
    )
    rows = session.execute(stmt).scalars().all()
    items: list[ParcelHistoryItem] = []
    for row in rows:
        metadata = row.metadata_json if isinstance(row.metadata_json, dict) else {}
        building_area_m2 = _coerce_float(
            metadata.get("building_area_m2")
            or metadata.get("site_area_m2")
            or metadata.get("listing_area_m2")
        )
        parcel_area_m2 = _coerce_float(parcel.area_m2)
        denominator_area = building_area_m2 if (building_area_m2 and building_area_m2 > 0) else parcel_area_m2
        computed_price_per_m2 = (
            (_coerce_float(row.price_paid) / denominator_area)
            if denominator_area and denominator_area > 0 and _coerce_float(row.price_paid) not in (None, 0)
            else None
        )
        location_label = (
            metadata.get("location_label")
            or row.town_city
            or row.district
            or row.county
            or parcel.local_authority
        )
        sale_year_meta = _coerce_float(metadata.get("sale_year"))
        reliability_score = _coerce_float(metadata.get("reliability_score") or metadata.get("confidence_score"))
        correctness_likelihood = _coerce_float(metadata.get("correctness_likelihood_pct")) or reliability_score
        items.append(
            ParcelHistoryItem(
                transaction_id=row.transaction_id,
                sale_date=row.sale_date,
                sale_year=row.sale_date.year if row.sale_date else (int(sale_year_meta) if sale_year_meta is not None else None),
                price_paid=row.price_paid,
                price_per_m2_gbp=_coerce_float(metadata.get("price_per_m2_gbp")) or computed_price_per_m2,
                postcode=row.postcode,
                property_type=metadata.get("building_type") or row.property_type,
                property_type_label=_format_history_property_type_label(metadata.get("building_type") or row.property_type),
                building_class_label=_classify_history_building_class(metadata.get("building_type") or row.property_type, parcel_use_label),
                land_use_label=parcel_use_label,
                tenure=row.tenure,
                address_text=row.address_text,
                location_label=location_label,
                building_area_m2=building_area_m2,
                parcel_area_m2=parcel_area_m2,
                source_name=str(metadata.get("source_name") or "hmlr_price_paid"),
                source_url=str(metadata.get("source_url") or "https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads"),
                source_file=str(metadata.get("source_file") or "").strip() or None,
                source_row_number=_safe_int(metadata.get("source_row_number") or metadata.get("row_number")),
                license_name=str(metadata.get("license_name") or "Open Government Licence"),
                evidence_hash=str(metadata.get("evidence_hash") or "").strip() or None,
                retrieved_at=_coerce_datetime(metadata.get("retrieved_at") or metadata.get("source_updated_at") or row.sale_date),
                reliability_score=reliability_score,
                correctness_likelihood_pct=correctness_likelihood,
                reliability_band=_reliability_band(correctness_likelihood),
            )
        )
    if items:
        return _apply_history_guardrails_to_items(items)

    verified_sales = _verified_sales_history_for_parcel(session, parcel_id)
    verified_records = verified_sales.get("sales_history_records") if isinstance(verified_sales, dict) else None
    if isinstance(verified_records, list) and verified_records:
        verified_items: list[ParcelHistoryItem] = []
        for index, raw in enumerate(verified_records, start=1):
            if not isinstance(raw, dict):
                continue
            if _history_record_is_rejected_duplicate(raw):
                continue

            sale_date = _coerce_date(raw.get("sale_date") or verified_sales.get("latest_sale_date"))
            sale_year = sale_date.year if sale_date else None
            if sale_year is None:
                raw_sale_year = _coerce_float(raw.get("sale_year") or verified_sales.get("latest_sale_year"))
                sale_year = int(raw_sale_year) if raw_sale_year is not None else None

            price_paid = _coerce_decimal(raw.get("sale_price_gbp") or verified_sales.get("latest_sale_price_gbp"))
            building_area_m2 = _coerce_float(raw.get("sale_area_m2") or verified_sales.get("latest_sale_area_m2"))
            parcel_area_m2 = _coerce_float(parcel.area_m2)
            denominator_area = building_area_m2 if (building_area_m2 and building_area_m2 > 0) else parcel_area_m2
            fallback_price_per_m2 = (
                (float(price_paid) / denominator_area)
                if denominator_area and denominator_area > 0 and price_paid is not None
                else None
            )
            price_per_m2 = _coerce_float(raw.get("sale_price_per_m2_gbp") or verified_sales.get("latest_sale_price_per_m2_gbp")) or fallback_price_per_m2

            property_type = str(raw.get("property_type") or verified_sales.get("latest_sale_property_type") or "").strip() or None
            reliability_score = _coerce_float(raw.get("source_confidence_score") or verified_sales.get("sales_history_confidence_score"))
            correctness_likelihood = _coerce_float(raw.get("correctness_likelihood_pct")) or reliability_score

            transaction_id = str(
                raw.get("transaction_id")
                or raw.get("source_record_id")
                or raw.get("matched_parcel_ref")
                or f"verified-history:{parcel_id}:{index}"
            ).strip()

            verified_items.append(
                ParcelHistoryItem(
                    transaction_id=transaction_id,
                    sale_date=sale_date,
                    sale_year=sale_year,
                    price_paid=price_paid,
                    price_per_m2_gbp=price_per_m2,
                    postcode=str(raw.get("postcode") or "").strip() or parcel.postcode,
                    property_type=property_type,
                    property_type_label=_format_history_property_type_label(property_type),
                    building_class_label=_classify_history_building_class(property_type, parcel_use_label),
                    land_use_label=parcel_use_label,
                    tenure=str(raw.get("tenure") or "").strip() or None,
                    address_text=str(raw.get("address") or raw.get("address_text") or "").strip() or None,
                    location_label=parcel.local_authority,
                    building_area_m2=building_area_m2,
                    parcel_area_m2=parcel_area_m2,
                    source_name=str(raw.get("source_type") or "hmlr_price_paid"),
                    source_url=str(raw.get("source_url") or "").strip() or None,
                    source_file=str(raw.get("source_file") or "").strip() or None,
                    source_row_number=_safe_int(raw.get("source_row_number") or raw.get("row_number")),
                    license_name=str(raw.get("license_name") or "Unknown").strip() or None,
                    evidence_hash=str(raw.get("evidence_hash") or "").strip() or None,
                    retrieved_at=_coerce_datetime(raw.get("retrieved_at") or raw.get("sale_date")),
                    reliability_score=reliability_score,
                    correctness_likelihood_pct=correctness_likelihood,
                    reliability_band=_reliability_band(correctness_likelihood),
                )
            )

        verified_items.sort(
            key=lambda item: (
                item.sale_date or dt.date.min,
                item.sale_year or 0,
            ),
            reverse=True,
        )
        if verified_items:
            return _apply_history_guardrails_to_items(verified_items)

    summary = session.get(ParcelSignalSummary, parcel_id)
    source_summary = summary.source_summary if summary and isinstance(summary.source_summary, dict) else {}
    history_records = source_summary.get("history_records", []) if isinstance(source_summary, dict) else []
    if not isinstance(history_records, list):
        return []

    fallback_items: list[ParcelHistoryItem] = []
    for index, raw in enumerate(history_records, start=1):
        if not isinstance(raw, dict):
            continue
        if _history_record_is_rejected_duplicate(raw):
            continue
        sale_date = _coerce_date(raw.get("sale_date") or raw.get("latest_sale_date"))
        sale_year = sale_date.year if sale_date else None
        if sale_year is None:
            raw_sale_year = _coerce_float(raw.get("sale_year"))
            sale_year = int(raw_sale_year) if raw_sale_year is not None else None

        price_paid = _coerce_decimal(raw.get("price_paid") or raw.get("latest_price_paid"))
        building_area_m2 = _coerce_float(raw.get("building_area_m2") or raw.get("area_m2") or raw.get("latest_area_m2"))
        parcel_area_m2 = _coerce_float(parcel.area_m2)
        denominator_area = building_area_m2 if (building_area_m2 and building_area_m2 > 0) else parcel_area_m2
        fallback_price_per_m2 = (
            (float(price_paid) / denominator_area)
            if denominator_area and denominator_area > 0 and price_paid is not None
            else None
        )
        price_per_m2 = _coerce_float(raw.get("price_per_m2_gbp") or raw.get("latest_price_per_m2")) or fallback_price_per_m2
        reliability_score = _coerce_float(raw.get("reliability_score") or raw.get("confidence_score"))
        correctness_likelihood = _coerce_float(raw.get("correctness_likelihood_pct")) or reliability_score

        transaction_id = str(
            raw.get("transaction_id")
            or raw.get("source_record_id")
            or raw.get("record_id")
            or f"history:{parcel_id}:{index}"
        ).strip()

        fallback_items.append(
            ParcelHistoryItem(
                transaction_id=transaction_id,
                sale_date=sale_date,
                sale_year=sale_year,
                price_paid=price_paid,
                price_per_m2_gbp=price_per_m2,
                postcode=str(raw.get("postcode") or "").strip() or parcel.postcode,
                property_type=str(raw.get("property_type") or raw.get("latest_property_type") or "").strip() or None,
                property_type_label=_format_history_property_type_label(raw.get("property_type") or raw.get("latest_property_type")),
                building_class_label=_classify_history_building_class(raw.get("property_type") or raw.get("latest_property_type"), parcel_use_label),
                land_use_label=parcel_use_label,
                tenure=str(raw.get("tenure") or raw.get("latest_tenure") or "").strip() or None,
                address_text=str(raw.get("address_text") or raw.get("label") or "").strip() or None,
                location_label=str(raw.get("location_label") or raw.get("latest_location") or "").strip() or parcel.local_authority,
                building_area_m2=building_area_m2,
                parcel_area_m2=parcel_area_m2,
                source_name=str(raw.get("source_name") or raw.get("source_type") or "hmlr_price_paid"),
                source_url=str(raw.get("source_url") or "").strip() or None,
                source_file=str(raw.get("source_file") or "").strip() or None,
                source_row_number=_safe_int(raw.get("source_row_number") or raw.get("row_number")),
                license_name=str(raw.get("license_name") or "Unknown").strip() or None,
                evidence_hash=str(raw.get("evidence_hash") or "").strip() or None,
                retrieved_at=_coerce_datetime(raw.get("retrieved_at") or raw.get("source_updated_at") or raw.get("sale_date")),
                reliability_score=reliability_score,
                correctness_likelihood_pct=correctness_likelihood,
                reliability_band=_reliability_band(correctness_likelihood),
            )
        )

    fallback_items.sort(
        key=lambda item: (
            item.sale_date or dt.date.min,
            item.sale_year or 0,
        ),
        reverse=True,
    )
    return _apply_history_guardrails_to_items(fallback_items)




def get_parcel_sales_latest(session: Session, parcel_id: int) -> dict[str, Any]:
    history_rows = get_parcel_history(session, parcel_id)
    if not history_rows:
        return {
            "status": "ok",
            "parcel_id": parcel_id,
            "has_sales": False,
            "latest": None,
        }
    latest = history_rows[0]
    return {
        "status": "ok",
        "parcel_id": parcel_id,
        "has_sales": True,
        "latest": latest.model_dump(mode="json"),
    }


def get_parcel_rental_reference(session: Session, parcel_id: int) -> dict[str, Any]:
    parcel = session.get(ParcelInspire, parcel_id)
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found")

    local_authority = str(parcel.local_authority or "").strip()
    csv_candidates = [
        SALES_MATCH_MASTER_ROOT / "rental_reference_official.csv",
        Path(__file__).resolve().parents[2] / "data" / "exports" / "historical_sales_parcel_matched" / "rental_reference_official.csv",
    ]
    csv_path = next((item for item in csv_candidates if item.exists() and item.is_file()), None)
    if csv_path is None:
        return {
            "status": "ok",
            "parcel_id": parcel_id,
            "local_authority": local_authority,
            "dataset_status": "not_available",
            "source_file": None,
            "records": [],
        }

    records: list[dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if not isinstance(row, dict):
                continue
            area_name = str(row.get("area_name") or "").strip()
            if local_authority and area_name and area_name.lower() != local_authority.lower():
                continue
            records.append(
                {
                    "area_code": row.get("area_code"),
                    "area_name": area_name or None,
                    "year_or_period": row.get("year_or_period"),
                    "bedroom_category": row.get("bedroom_category"),
                    "monthly_rent_statistic": row.get("monthly_rent_statistic"),
                    "statistic_type": row.get("statistic_type"),
                    "source_url": row.get("source_url"),
                    "accuracy": row.get("accuracy") if str(row.get("accuracy") or "") in {"A_CERTAIN", "B_HIGH", "C_PARTIAL", "D_UNKNOWN"} else "D_UNKNOWN",
                }
            )

    return {
        "status": "ok",
        "parcel_id": parcel_id,
        "local_authority": local_authority,
        "dataset_status": "available",
        "source_file": str(csv_path),
        "records": records,
    }


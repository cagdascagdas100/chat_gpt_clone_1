from __future__ import annotations

SOURCE_CATALOG: dict[str, dict[str, object]] = {
    "homes_england_landhub": {
        "name": "homes_england_landhub",
        "label": "Homes England Land Hub",
        "description": "Official Homes England land source.",
    },
    "government_property_finder": {
        "name": "government_property_finder",
        "label": "Government Property Finder",
        "description": "Government property source.",
    },
    "hmlr_inspire": {
        "name": "hmlr_inspire",
        "label": "HM Land Registry INSPIRE",
        "description": "Parcel boundary source.",
    },
    "local_authority_brownfield": {
        "name": "local_authority_brownfield",
        "label": "Local Authority Brownfield",
        "description": "Local authority brownfield land registers.",
    },
    "planning_data_brownfield": {
        "name": "planning_data_brownfield",
        "label": "Planning Data Brownfield",
        "description": "Planning data brownfield source.",
    },
    "hmlr_price_paid": {
        "name": "hmlr_price_paid",
        "label": "HMLR Price Paid",
        "description": "Historic transaction source.",
    },
    "market_listing_adapter": {
        "name": "market_listing_adapter",
        "label": "Market Listing Adapter",
        "description": "Market listing feed adapter.",
    },
}

STALE_THRESHOLDS: dict[str, int] = {
    "homes_england_landhub": 90,
    "government_property_finder": 90,
    "hmlr_inspire": 365,
    "local_authority_brownfield": 180,
    "planning_data_brownfield": 180,
    "hmlr_price_paid": 90,
    "market_listing_adapter": 30,
}


def get_stale_threshold_days(source_name: str) -> int:
    return STALE_THRESHOLDS.get(source_name, 30)

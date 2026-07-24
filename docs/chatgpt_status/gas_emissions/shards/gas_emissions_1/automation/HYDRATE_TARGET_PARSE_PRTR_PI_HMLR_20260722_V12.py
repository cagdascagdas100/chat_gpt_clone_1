#!/usr/bin/env python3
"""Parser V12: add Britvic/RMS identities and isolate HMLR from binary parsing.

The base binary parser historically searched all configured tokens inside HMLR
INSPIRE GML, including leasehold title TGL419520. HMLR INSPIRE polygons cover
registered freehold property and expose INSPIRE identifiers, so title-text
matching is not a valid leasehold binding method. V12 disables HMLR work in this
binary task and leaves geometry discovery solely to the dedicated corrected
HMLR proximity task. PRTR and Pollution Inventory extraction remains enabled.
"""
from __future__ import annotations

import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V11 as v11

base = v11.v10.v9.v8.v7.v6.v5.v4.v3.v2.base

base.TARGET_TOKENS = tuple(dict.fromkeys(base.TARGET_TOKENS + (
    "britvic soft drinks limited",
    "britvic soft drinks",
    "beckton soft drinks factory",
    "beckton soft drinks",
    "epr/bn2832ik",
    "epr/bn2832ik/v006",
    "e6 6lf",
    "00517211",
    "britvic corona limited",
    "canada dry rawlings limited",
    "canada dry (u.k) limited",
    "britannia soft drinks limited",
    "recycled material supplies limited",
    "recycled material supplies",
    "perry road recycling facility",
    "perry road recycling",
    "epr/db3502tz",
    "epr/db3502tz/v005",
    "perry road",
    "rm9 6qd",
    "06221599",
    "rms group limited",
)))


def resolve_hmlr_gml_disabled() -> dict[str, object]:
    """Prevent invalid title-token searching in freehold-only INSPIRE GML."""
    return {
        "index_url": base.HMLR_INDEX_URL,
        "gml_url": None,
        "error": "HMLR_DISABLED_IN_BINARY_PARSER_USE_DEDICATED_INSPIRE_PROXIMITY_TASK",
        "dataset_scope": "REGISTERED_FREEHOLD_PROPERTY_ONLY",
        "target_title_tenure_context": "LEASEHOLD",
        "exact_title_occurrence_required": False,
        "parcel_binding_permitted": False,
    }


base.resolve_hmlr_gml = resolve_hmlr_gml_disabled

if __name__ == "__main__":
    raise SystemExit(base.main())

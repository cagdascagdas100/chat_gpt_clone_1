#!/usr/bin/env python3
"""Semantic gate V9: reject beverage, recycling and permit-document context.

V8 already rejects application, capacity, production, resource, corporate,
no-point-source and no-limit wording. V9 adds explicit Britvic/RMS context so
soft-drink production, aggregate recycling, hazardous treatment thresholds,
EWC codes, variation notices and decision documents cannot be mistaken for an
official annual PRTR/PI pollutant release to air.
"""
from __future__ import annotations

import VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V8 as v8

terms = v8.v7.v6.v5.v4.CONTEXT_REJECT_TERMS
v8.v7.v6.v5.v4.CONTEXT_REJECT_TERMS = tuple(dict.fromkeys(terms + (
    "soft drink production",
    "manufacture of soft drinks",
    "mineral waters",
    "beverage wholesale",
    "aggregate recycling facility",
    "construction demolition and excavation waste",
    "physico-chemical treatment",
    "hazardous treatment threshold",
    "hazardous storage threshold",
    "ewc codes",
    "variation notice",
    "decision document",
    "industrial emissions directive permit",
    "permit identity",
    "withdrawn consultation notice",
)))

if __name__ == "__main__":
    v8.v7.v6.v5.v4.v3.review = v8.v7.v6.v5.v4.review
    raise SystemExit(v8.v7.v6.v5.v4.v3.main())

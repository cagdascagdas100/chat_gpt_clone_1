#!/usr/bin/env python3
"""Semantic gate V5: reject production, treatment and waste-performance contexts.

V4 rejects permit limits, capacity, storage, fuel/reagent usage and operating
records. V5 additionally rejects production/treatment outputs, digestate,
resource-use, waste-throughput and transfer records even when a field contains an
annual mass unit. Official PRTR/PI pollutant releases to air remain eligible.
"""
from __future__ import annotations

import VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V4 as v4

v4.CONTEXT_REJECT_TERMS = tuple(dict.fromkeys(v4.CONTEXT_REJECT_TERMS + (
    "annual production/treatment",
    "electricity generated",
    "electricity exported",
    "biomethane exported",
    "whole digestate",
    "liquid digestate",
    "solid digestate",
    "digestate output",
    "digestate stability",
    "recovered outputs",
    "water usage",
    "energy usage",
    "raw material usage",
    "waste throughput",
    "waste transfer",
    "waste accepted",
    "waste processed",
    "contamination removal efficiency",
    "bioaerosols monitoring",
    "pressure relief report",
    "mass-balance release",
    "methane slip assessment",
)))

if __name__ == "__main__":
    v4.v3.review = v4.review
    raise SystemExit(v4.v3.main())

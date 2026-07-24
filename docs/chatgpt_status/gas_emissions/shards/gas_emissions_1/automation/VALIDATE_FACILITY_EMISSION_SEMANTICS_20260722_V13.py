#!/usr/bin/env python3
"""Semantic gate V13: reject hazardous-storage and cooling-water contexts.

V12 already includes V11 annual-air-mass quality gates and surrender/history
exclusions. V13 explicitly rejects S Norton hazardous-storage variation context
and B&D Energy cooling-water, receiving-water and flow-volume context. Official
PRTR/PI annual releases to air remain eligible only with explicit year,
pollutant, air medium, numeric annual mass, recognised unit and valid method.
"""
from __future__ import annotations

import VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V12 as v12

terms = v12.v11.v10.v9.v8.v7.v6.v5.v4.CONTEXT_REJECT_TERMS
v12.v11.v10.v9.v8.v7.v6.v5.v4.CONTEXT_REJECT_TERMS = tuple(dict.fromkeys(terms + (
    "section 5.6",
    "temporary or underground storage of hazardous waste",
    "temporary storage of hazardous waste",
    "underground storage of hazardous waste",
    "hazardous-waste storage",
    "foreseeable emissions application narrative",
    "water source heating / cooling system",
    "water source heating and cooling system",
    "cooling waters",
    "river roding",
    "receiving environment",
    "6650 cubic metres per day",
    "cubic metres per day",
    "withdrawn variation application",
)))

if __name__ == "__main__":
    v12.v11.v10.v9.v8.v7.v6.v5.v4.v3.review = v12.v11.v10.v9.v8.v7.v6.v5.v4.review
    raise SystemExit(v12.v11.v10.v9.v8.v7.v6.v5.v4.v3.main())

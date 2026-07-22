#!/usr/bin/env python3
"""Semantic gate V10: reject water-discharge and dissolved-company contexts.

V9 already rejects permit, application, production, corporate, beverage and
aggregate-recycling records. V10 explicitly rejects sewage treatment, effluent,
receiving-water, discharge-point and flow-volume records, plus physical-treatment
and dissolved-company status. Official PRTR/PI annual pollutant releases to air
remain eligible only with year, pollutant, air medium, numeric mass and unit.
"""
from __future__ import annotations

import VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V9 as v9

terms = v9.v8.v7.v6.v5.v4.CONTEXT_REJECT_TERMS
v9.v8.v7.v6.v5.v4.CONTEXT_REJECT_TERMS = tuple(dict.fromkeys(terms + (
    "sewage treatment plant",
    "secondary treated sewage effluent",
    "surface water runoff",
    "receiving environment",
    "river thames via perched water table",
    "discharge point",
    "cubic metres/day",
    "m3/day",
    "water flow volume",
    "physical treatment facility",
    "dissolved company",
    "company dissolved",
    "corporate dissolution",
    "register viewing location",
)))

if __name__ == "__main__":
    v9.v8.v7.v6.v5.v4.v3.review = v9.v8.v7.v6.v5.v4.review
    raise SystemExit(v9.v8.v7.v6.v5.v4.v3.main())

#!/usr/bin/env python3
"""Semantic gate V15: reject partial-surrender and support-site contexts.

V14 already includes annual-air-mass quality gates, surrender/history,
hazardous-storage, cooling-water, transfer-station and permit-boundary
exclusions. V15 adds partial-surrender, clinical-waste support-site application,
50-tonne-per-day proposed capacity, permit-document availability and corporate
name-change certificate contexts. Official PRTR/PI annual releases to air still
require explicit year, pollutant, air medium, numeric annual mass, recognised
unit and valid determination method.
"""
from __future__ import annotations

import VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V14 as v14

terms = v14.v13.v12.v11.v10.v9.v8.v7.v6.v5.v4.CONTEXT_REJECT_TERMS
v14.v13.v12.v11.v10.v9.v8.v7.v6.v5.v4.CONTEXT_REJECT_TERMS = tuple(dict.fromkeys(terms + (
    "partial surrender issued",
    "partial surrender permit",
    "surrender notice",
    "clinical waste transfer station support site",
    "support site to the applicant",
    "hazardous waste repackaging",
    "maximum throughput of 50 tpd",
    "50 tonnes per day",
    "variation notice published",
    "decision document published",
    "permit document availability",
    "company name changed",
    "name change certificate",
    "certificate issued on 06/12/24",
)))

if __name__ == "__main__":
    v14.v13.v12.v11.v10.v9.v8.v7.v6.v5.v4.v3.review = v14.v13.v12.v11.v10.v9.v8.v7.v6.v5.v4.review
    raise SystemExit(v14.v13.v12.v11.v10.v9.v8.v7.v6.v5.v4.v3.main())

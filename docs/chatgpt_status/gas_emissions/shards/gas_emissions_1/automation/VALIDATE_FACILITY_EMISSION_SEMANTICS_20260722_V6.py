#!/usr/bin/env python3
"""Semantic gate V6: reject corporate, governance, filing and venue contexts.

V5 already rejects permit, performance, production, resource, throughput and
transfer contexts. V6 additionally rejects company accounts, officers, PSC,
charges, filings, registered offices and venue/service-management records even
when an annual mass-like value appears. Official PRTR/PI pollutant releases to
air remain eligible.
"""
from __future__ import annotations

import VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V5 as v5

v5.v4.CONTEXT_REJECT_TERMS = tuple(dict.fromkeys(v5.v4.CONTEXT_REJECT_TERMS + (
    "company accounts",
    "annual accounts",
    "confirmation statement",
    "company filing",
    "filing history",
    "officer appointment",
    "director appointed",
    "secretary appointed",
    "person with significant control",
    "psc notified",
    "share control",
    "voting control",
    "right to appoint or remove directors",
    "registered office",
    "company status",
    "company type",
    "sic code",
    "nature of business",
    "registered charges",
    "outstanding charges",
    "satisfied charges",
    "venue manager",
    "facility manager",
    "leisure centre management",
    "council service",
)))

if __name__ == "__main__":
    v5.v4.v3.review = v5.v4.review
    raise SystemExit(v5.v4.v3.main())

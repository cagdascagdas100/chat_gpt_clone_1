#!/usr/bin/env python3
"""Semantic gate V8: reject absence, no-limit and permit-reporting contexts.

V7 already rejects application, permit, capacity, production, resource,
corporate and consultation records. V8 explicitly prevents statements such as
"no point source emissions" or "no emission limits" from being interpreted as
zero annual releases and rejects permit reporting/configuration context even
when it contains annual or mass-like terms. Official PRTR/PI annual pollutant
releases to air remain eligible.
"""
from __future__ import annotations

import VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V7 as v7

v7.v6.v5.v4.CONTEXT_REJECT_TERMS = tuple(dict.fromkeys(v7.v6.v5.v4.CONTEXT_REJECT_TERMS + (
    "no point source emissions",
    "no emission limits",
    "no associated monitoring requirements",
    "annual production/treatment",
    "hazardous aggregate processed",
    "quarterly waste report",
    "waste accepted and removed",
    "treatment capacity",
    "storage capacity",
    "site configuration",
    "screening fractions",
    "dust emissions management plan",
    "receptor distance",
    "aqma context",
    "permit reporting deadline",
)))

if __name__ == "__main__":
    v7.v6.v5.v4.v3.review = v7.v6.v5.v4.review
    raise SystemExit(v7.v6.v5.v4.v3.main())

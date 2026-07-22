#!/usr/bin/env python3
"""Semantic gate V12: reject surrender and historic permit-lifecycle contexts.

V11 already rejects permit/application, production, corporate, water-discharge,
refining, concentration, recovery-tonnage and remediation records. V12 adds
permit surrender, surrender-letter, site-condition evaluation, historic permit
version and installation-name continuity contexts. Official PRTR/PI annual air
releases remain eligible only with explicit year, pollutant, air medium, numeric
annual mass, recognised unit and valid determination method.
"""
from __future__ import annotations

import VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V11 as v11

terms = v11.v10.v9.v8.v7.v6.v5.v4.CONTEXT_REJECT_TERMS
v11.v10.v9.v8.v7.v6.v5.v4.CONTEXT_REJECT_TERMS = tuple(dict.fromkeys(terms + (
    "permit surrender",
    "surrender issued",
    "surrender letter",
    "site condition report evaluation template",
    "scret",
    "historic issued permit",
    "historic permit version",
    "permit version continuity",
    "permit lifecycle event",
    "installation name continuity",
    "historic installation name",
    "superseded permit publication",
)))

if __name__ == "__main__":
    v11.v10.v9.v8.v7.v6.v5.v4.v3.review = v11.v10.v9.v8.v7.v6.v5.v4.review
    raise SystemExit(v11.v10.v9.v8.v7.v6.v5.v4.v3.main())

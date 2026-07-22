#!/usr/bin/env python3
"""Semantic gate V11: reject refining, concentration and remediation contexts.

V10 already rejects permit, application, production, corporate, water-discharge
and dissolved-company records. V11 additionally rejects precious-metal refining
processes, permit concentration limits, recovery/import tonnage, groundwater
remediation and trade-effluent context. Official PRTR/PI annual pollutant
releases to air remain eligible only with year, pollutant, air medium, numeric
annual mass and recognised unit.
"""
from __future__ import annotations

import VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V10 as v10

terms = v10.v9.v8.v7.v6.v5.v4.CONTEXT_REJECT_TERMS
v10.v9.v8.v7.v6.v5.v4.CONTEXT_REJECT_TERMS = tuple(dict.fromkeys(terms + (
    "miller process",
    "aqua regia process",
    "electrolytic refining",
    "precious metal refining",
    "batch capacity",
    "equipment capacity",
    "permit concentration limit",
    "mg/m3",
    "monitoring frequency",
    "trade effluent consent",
    "foul sewer",
    "deposit for recovery",
    "import tonnage",
    "suitable wastes for construction",
    "ground remediation",
    "groundwater via injection borehole",
    "abstracted groundwater",
    "cubic metres per day",
    "operator name change",
)))

if __name__ == "__main__":
    v10.v9.v8.v7.v6.v5.v4.v3.review = v10.v9.v8.v7.v6.v5.v4.review
    raise SystemExit(v10.v9.v8.v7.v6.v5.v4.v3.main())

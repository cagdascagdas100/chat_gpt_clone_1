#!/usr/bin/env python3
"""Semantic gate V7: reject application and consultation contexts.

V6 already rejects permit, production, resource, corporate and venue records.
V7 additionally rejects application notices, proposed capacities, consultation
fields and withdrawn applications even when they contain annual mass-like units.
Official PRTR/PI annual pollutant releases to air remain eligible.
"""
from __future__ import annotations

import VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V6 as v6

v6.v5.v4.CONTEXT_REJECT_TERMS = tuple(dict.fromkeys(v6.v5.v4.CONTEXT_REJECT_TERMS + (
    "application notice",
    "application advertisement",
    "application number",
    "consultation deadline",
    "comment deadline",
    "substantial change application",
    "new bespoke application",
    "proposed annual tonnage",
    "proposed throughput",
    "proposed storage",
    "storage capacity increase",
    "additional waste codes proposed",
    "mixing and blending proposed",
    "withdrawn application",
    "application withdrawn",
    "no final permit decision",
)))

if __name__ == "__main__":
    v6.v5.v4.v3.review = v6.v5.v4.review
    raise SystemExit(v6.v5.v4.v3.main())

#!/usr/bin/env python3
"""Expand official target identity aliases, then run the read-only binary parser."""
from __future__ import annotations

import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722 as base

# Official Companies House identity aliases. These improve candidate recall only;
# they never merge sites or promote a candidate to a parcel emission value.
base.TARGET_TOKENS = tuple(dict.fromkeys(base.TARGET_TOKENS + (
    "07933078",
    "0793 3078",
    "01600851",
    "0160 0851",
    "mcgrath brothers",
    "mcgrath brothers (waste disposal) services",
    "production of electricity",
    "treatment and disposal of non-hazardous waste",
    "treatment and disposal of hazardous waste",
    "collection of non-hazardous waste",
    "remediation activities and other waste management services",
)))

if __name__ == "__main__":
    raise SystemExit(base.main())

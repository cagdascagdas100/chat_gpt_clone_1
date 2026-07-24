#!/usr/bin/env python3
"""Expand official corporate aliases for regional gas_emissions_1 targets, then run V4."""
from __future__ import annotations

import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V4 as v4

# Official Companies House identities and former names. These improve candidate
# recall only; they never merge separate sites or create measured release rows.
v4.v3.v2.base.TARGET_TOKENS = tuple(dict.fromkeys(v4.v3.v2.base.TARGET_TOKENS + (
    "07625177",
    "teg biogas (london) limited",
    "plot 7a london sustainable industries park",
    "06561170",
    "refood limited",
    "saria limited",
    "04239332",
    "gyron internet limited",
    "willoughby (342) limited",
    "ntt limited",
    "10088491",
    "london borough of barking and dagenham",
)))

if __name__ == "__main__":
    raise SystemExit(v4.v3.v2.base.main())

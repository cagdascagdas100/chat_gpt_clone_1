#!/usr/bin/env python3
"""Add Barking Power, Van Dalen and permit-revision aliases, then run V6.

Tokens improve official PRTR/PI candidate recall only. Historical permit pages,
dissolved companies and shared postcodes never create a current permit claim,
annual release row or parcel binding.
"""
from __future__ import annotations

import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V6 as v6

v6.v5.v4.v3.v2.base.TARGET_TOKENS = tuple(dict.fromkeys(v6.v5.v4.v3.v2.base.TARGET_TOKENS + (
    "thames power services limited",
    "barking power station",
    "epr/rp3133bh",
    "epr/rp3133bh/v005",
    "rm9 6pf",
    "02624730",
    "van dalen uk limited",
    "van dalen dagenham",
    "epr/vp3597np",
    "epr/vp3597np/v003",
    "rm8 6qy",
    "04031206",
    "easimet limited",
    "shandene limited",
    "hunts wharf",
    "perry road",
    "chequers lane",
    "dagenham combustion plant",
    "epr/vp3736sb",
    "epr/vp3736sb/v003",
    "epr/cp3902lv/v003",
    "epr/ep3494vg/v003",
    "epr/wp3433by/v004",
    "epr/qp3735dl/v003",
    "epr/zp3833bk/v003",
)))

if __name__ == "__main__":
    raise SystemExit(v6.v5.v4.v3.v2.base.main())

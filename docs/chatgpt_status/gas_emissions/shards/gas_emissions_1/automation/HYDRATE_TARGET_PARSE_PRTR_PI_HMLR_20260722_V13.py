#!/usr/bin/env python3
"""Parser V13: add Plasterzone and VolkerFitzpatrick withdrawn identities.

V12 already isolates HMLR INSPIRE from binary parsing. V13 expands official
PRTR/PI recall only. Withdrawn applications, water-discharge records, flow
volumes, dissolved-company records, officers and charges never create a current
permit, annual air-release row, site merge or parcel binding.
"""
from __future__ import annotations

import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V12 as v12

base = v12.base
base.TARGET_TOKENS = tuple(dict.fromkeys(base.TARGET_TOKENS + (
    "plasterzone limited",
    "plasterzone ltd",
    "plasterzone",
    "epr/eb3403xa",
    "epr/eb3403xa/a001",
    "11 atcost road",
    "ig11 0eg",
    "10185968",
    "physical treatment facility",
    "volkerfitzpatrick limited",
    "volkerfitzpatrick",
    "epr/pb3397eb",
    "epr/pb3397eb/a001",
    "msvf compound a",
    "barking riverside",
    "ig11 0td",
    "tq 46897 81933",
    "02387700",
    "volkerwessels limited",
    "fitzpatrick contractors limited",
    "caxtonhurst limited",
)))

if __name__ == "__main__":
    raise SystemExit(base.main())

#!/usr/bin/env python3
"""Parser V15: add S Norton V003 and B&D Energy A001 identities.

V14 keeps HMLR INSPIRE title-token matching disabled. These additional tokens
improve official PRTR/PI candidate recall only. Withdrawn applications,
hazardous-waste storage scope, cooling-water discharge, flow volume, corporate
records and consultation data never create an annual air-release row, current
permit, site merge or parcel binding.
"""
from __future__ import annotations

import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V14 as v14

base = v14.base
base.TARGET_TOKENS = tuple(dict.fromkeys(base.TARGET_TOKENS + (
    "s norton & co limited",
    "s norton & co ltd",
    "epr/cb3807hv",
    "epr/cb3807hv/v003",
    "river road barking",
    "01859428",
    "section 5.6 hazardous waste storage",
    "b&d energy dis 1",
    "epr/ab3845kw",
    "epr/ab3845kw/a001",
    "east ham water treatment works",
    "tq 43615 84286",
    "cooling waters",
    "ig11 8lh",
)))

if __name__ == "__main__":
    raise SystemExit(base.main())

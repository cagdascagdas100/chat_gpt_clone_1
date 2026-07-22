#!/usr/bin/env python3
"""Add G&S Tyre V003 and Neptune Recycling A001 aliases, then run V10.

Tokens improve official PRTR/PI candidate recall only. Application notices,
permit capacity, no-limit statements, production/resource reporting, company
control and officers never create an annual release row, site merge or parcel
binding.
"""
from __future__ import annotations

import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V10 as v10

v10.v9.v8.v7.v6.v5.v4.v3.v2.base.TARGET_TOKENS = tuple(dict.fromkeys(
    v10.v9.v8.v7.v6.v5.v4.v3.v2.base.TARGET_TOKENS + (
        "g & s tyre services limited",
        "g & s tyre services",
        "epr/vp3299vx",
        "epr/vp3299vx/v003",
        "kingsbridge road",
        "ig11 0bd",
        "02531072",
        "g h s tyre group limited",
        "neptune contract services limited",
        "neptune recycling",
        "epr/jp3838qw",
        "epr/jp3838qw/a001",
        "thunderer road",
        "rm9 6qd",
        "03347634",
        "tq 48350 82141",
    )
))

if __name__ == "__main__":
    raise SystemExit(v10.v9.v8.v7.v6.v5.v4.v3.v2.base.main())

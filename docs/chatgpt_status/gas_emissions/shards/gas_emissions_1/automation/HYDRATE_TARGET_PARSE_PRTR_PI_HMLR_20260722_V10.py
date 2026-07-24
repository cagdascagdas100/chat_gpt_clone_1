#!/usr/bin/env python3
"""Add Stolthaven and withdrawn Olleco Dagenham application aliases, then run V9.

Tokens improve official PRTR/PI candidate recall only. Application notices,
proposed throughput, withdrawn applications, company control and officers never
create a current permit claim, annual release row, site merge or parcel binding.
"""
from __future__ import annotations

import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V9 as v9

v9.v8.v7.v6.v5.v4.v3.v2.base.TARGET_TOKENS = tuple(dict.fromkeys(
    v9.v8.v7.v6.v5.v4.v3.v2.base.TARGET_TOKENS + (
        "stolthaven dagenham limited",
        "stolthaven dagenham",
        "epr/we4467ac",
        "epr/we4467ac/a001",
        "epr/we4467ac/v002",
        "rm9 6pu",
        "hindmans way",
        "08119909",
        "stolt-nielsen m. s. ltd",
        "olleco dagenham",
        "epr/wp3825sb/a001",
        "rm9 6ln",
        "05878742",
        "agri energy",
        "anglo beef processors holdings",
    )
))

if __name__ == "__main__":
    raise SystemExit(v9.v8.v7.v6.v5.v4.v3.v2.base.main())

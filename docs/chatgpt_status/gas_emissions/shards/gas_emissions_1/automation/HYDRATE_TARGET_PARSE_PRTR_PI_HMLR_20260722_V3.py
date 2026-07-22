#!/usr/bin/env python3
"""Expand official permit/site aliases, then run the read-only gas_emissions_1 parser."""
from __future__ import annotations

import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V2 as v2

# Current Environment Agency permit records. Tokens improve candidate recall only;
# they never merge sites or promote a record to a parcel emission value.
v2.base.TARGET_TOKENS = tuple(dict.fromkeys(v2.base.TARGET_TOKENS + (
    "80745",
    "80535",
    "80105",
    "403490",
    "406738",
    "104126",
    "ig11 0ds",
    "rm10 7hx",
    "ig11 0eg",
    "ig11 0sb",
    "rm9 6rj",
    "frizlands lane reuse & recycling centre",
    "renwick road rail hub",
    "k&j skip hire",
    "s u c exc",
    "54 - 60 river road",
    "62 river road",
)))

if __name__ == "__main__":
    raise SystemExit(v2.base.main())

#!/usr/bin/env python3
"""Parser V17: add Riverside, Veolia Rainham, Sharpsmart and ITM identities.

V16 keeps HMLR INSPIRE title-token matching disabled. These official permit,
application, company-number and former-name aliases improve PRTR/PI candidate
recall only. Partial surrender, support-site application, throughput, company
name-change and corporate records never create annual air-release rows, site
merges or parcel bindings.
"""
from __future__ import annotations

import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V16 as v16

base = v16.base
base.TARGET_TOKENS = tuple(dict.fromkeys(base.TARGET_TOKENS + (
    "riverside sludge treatment centre",
    "epr/gb3739dy",
    "epr/gb3739dy/v004",
    "rm13 8qs",
    "veolia es landfill limited",
    "rainham landfill",
    "epr/ep3136gk",
    "epr/ep3136gk/s012",
    "rm13 9bj",
    "00997695",
    "onyx landfill limited",
    "progressive waste disposal limited",
    "veolia environmental services group (uk) limited",
    "sharpsmart limited",
    "rainham clinical treatment centre",
    "epr/pp3707bb",
    "epr/pp3707bb/v004",
    "epr/rp3621lb",
    "epr/rp3621lb/a001",
    "rm13 8bt",
    "04261387",
    "white rose sharpsmart limited",
    "broomco (2648) limited",
    "itm power uk limited",
    "itm power (trading) limited",
    "hydrogen refuelling station",
    "epr/xp3536dk",
    "rm13 8ua",
    "06156553",
    "quayshelfco 1214 limited",
)))

if __name__ == "__main__":
    raise SystemExit(base.main())

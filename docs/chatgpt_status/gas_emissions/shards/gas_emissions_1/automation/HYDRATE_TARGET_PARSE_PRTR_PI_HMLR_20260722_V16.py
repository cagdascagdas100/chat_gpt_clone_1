#!/usr/bin/env python3
"""Parser V16: add H. Sivyer A001 and DB Cargo V003/V004 identities.

V15 keeps HMLR INSPIRE title-token matching disabled. These official application,
site, company and control aliases improve PRTR/PI candidate recall only.
Withdrawn applications, hazardous-waste capacity, transfer-station class, EWC
codes, permit-boundary changes and corporate records never create annual air
release rows, current permits, site merges or parcel bindings.
"""
from __future__ import annotations

import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V15 as v15

base = v15.base
base.TARGET_TOKENS = tuple(dict.fromkeys(base.TARGET_TOKENS + (
    "h sivyer transport limited",
    "h. sivyer transport limited",
    "sivyer wharf",
    "epr/lp3537dj",
    "epr/lp3537dj/a001",
    "24-28 river road",
    "ig11 0dg",
    "01360909",
    "sivyer logistics limited",
    "06844424",
    "physical treatment facility",
    "db cargo (uk) limited",
    "d b cargo (uk) limited",
    "barking eurohub",
    "epr/gb3003gr",
    "epr/gb3003gr/v003",
    "epr/gb3003gr/v004",
    "box lane",
    "renwick road",
    "ig11 0sq",
    "02938988",
    "db cargo (uk) holdings limited",
)))

if __name__ == "__main__":
    raise SystemExit(base.main())

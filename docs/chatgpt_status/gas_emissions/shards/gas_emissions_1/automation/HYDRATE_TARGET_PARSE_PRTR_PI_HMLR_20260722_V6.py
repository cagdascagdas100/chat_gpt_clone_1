#!/usr/bin/env python3
"""Expand remaining official corporate and Jenkins Lane aliases, then run V5.

Tokens improve recall only. They never merge permit sites, create an annual
release, or bind a title/parcel without explicit geometry evidence.
"""
from __future__ import annotations

import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V5 as v5

v5.v4.v3.v2.base.TARGET_TOKENS = tuple(dict.fromkeys(v5.v4.v3.v2.base.TARGET_TOKENS + (
    "00235446",
    "ford technologies limited",
    "01631444",
    "silver lining industries limited",
    "nufix limited",
    "austenbury limited",
    "wastecare group limited",
    "02366970",
    "powergen uk plc",
    "powergen plc",
    "the power generation company plc",
    "e.on uk holding company limited",
    "02393309",
    "renewi uk services limited",
    "shanks waste management limited",
    "vale collections and recycling limited",
    "asm waste services limited",
    "asm skip hire limited",
    "biffa treatment services holdings limited",
    "gb3003zn",
    "80679",
    "rp3297nn",
    "80661",
    "jenkins lane ecco decco",
)))

if __name__ == "__main__":
    raise SystemExit(v5.v4.v3.v2.base.main())

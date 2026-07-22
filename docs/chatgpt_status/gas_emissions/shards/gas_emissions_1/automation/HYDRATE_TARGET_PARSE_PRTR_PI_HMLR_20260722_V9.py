#!/usr/bin/env python3
"""Add Academy Central and B&D Energy official identity aliases, then run V8.

Tokens improve official PRTR/PI candidate recall only. Corporate status, PSC,
officers, filings, venue management and registered-office data never create an
annual release row, permit transfer, site merge or parcel binding.
"""
from __future__ import annotations

import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V8 as v8

v8.v7.v6.v5.v4.v3.v2.base.TARGET_TOKENS = tuple(dict.fromkeys(
    v8.v7.v6.v5.v4.v3.v2.base.TARGET_TOKENS + (
        "academy way",
        "academy central epr/yp3803pa",
        "e.on uk plc",
        "westwood business park",
        "becontree heath leisure centre epr/jb3990yz",
        "althorne way",
        "david lewis barking town hall",
        "b&d energy limited",
    )
))

if __name__ == "__main__":
    raise SystemExit(v8.v7.v6.v5.v4.v3.v2.base.main())

#!/usr/bin/env python3
"""Add East London historic permit and Beckton STC aliases, then run V7.

Tokens improve official PRTR/PI candidate recall only. Permit history, same-site
waste transfers and shared operators never merge separate regulated facilities,
create an annual release row or establish parcel geometry.
"""
from __future__ import annotations

import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V7 as v7

v7.v6.v5.v4.v3.v2.base.TARGET_TOKENS = tuple(dict.fromkeys(
    v7.v6.v5.v4.v3.v2.base.TARGET_TOKENS + (
        "epr/zp3235zp",
        "teg environmental limited",
        "epr/pp3437wr",
        "epr/pp3437wr/v002",
        "epr/pp3437wr/v003",
        "epr/wp3606me/v002",
        "epr/wp3606me/v003",
        "beckton sludge treatment centre",
        "beckton sewage treatment works",
        "epr/pb3238rk",
        "epr/pb3238rk/a001",
        "epr/pb3238rk/v002",
        "epr/pb3238rk/v003",
        "epr/pb3238rk/v004",
        "02366661",
        "eawml 400177",
    )
))

if __name__ == "__main__":
    raise SystemExit(v7.v6.v5.v4.v3.v2.base.main())

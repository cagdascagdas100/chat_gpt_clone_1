#!/usr/bin/env python3
"""Expand regional official installation aliases, then run the read-only V3 parser."""
from __future__ import annotations

import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V3 as v3

# Environment Agency and GOV.UK installation identities. These tokens improve
# candidate recall only; they never create a measured release or parcel binding.
v3.v2.base.TARGET_TOKENS = tuple(dict.fromkeys(v3.v2.base.TARGET_TOKENS + (
    "ford motor company limited",
    "dagenham engine plant",
    "epr/yp3024st",
    "rm9 6sa",
    "thames water utilities limited",
    "beckton sludge powered generator",
    "epr/zp3833bk",
    "epr/zp3833bk/v003",
    "ig11 0ad",
    "east london biogas limited",
    "organic waste treatment facility",
    "epr/wp3606me",
    "halyard street",
    "dagenham dock",
    "refood uk limited",
    "hitch street ad plant",
    "refood ad facility",
    "epr/qp3735dl",
    "epr/qp3735dl/a001",
    "epr/qp3735dl/v003",
    "rm9 6fa",
    "wastecare limited",
    "wastecare london",
    "epr/ep3494vg",
    "ig11 0eq",
    "ntt global data centers emea uk ltd",
    "epr/cp3902lv",
    "rm10 7fz",
    "e.on uk limited",
    "academy central",
    "epr/yp3803pa",
    "rm8 2fd",
    "b & d energy limited",
    "becontree heath leisure centre",
    "epr/jb3990yz",
    "rm10 7fh",
    "jenkins lane waste management facility",
    "epr/wp3433by",
)))

if __name__ == "__main__":
    raise SystemExit(v3.v2.base.main())

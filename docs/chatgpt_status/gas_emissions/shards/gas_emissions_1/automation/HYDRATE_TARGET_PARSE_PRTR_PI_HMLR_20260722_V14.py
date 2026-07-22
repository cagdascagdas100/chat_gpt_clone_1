#!/usr/bin/env python3
"""Parser V14: add Baird, Renewi, Thames Materials and C.A. Blackwell identities.

V13 already isolates HMLR INSPIRE from binary parsing. V14 expands official
PRTR/PI recall only. Permit limits, process capacities, recovery tonnage,
withdrawn applications, groundwater discharge, corporate records and charges
never create annual air-release rows, site merges or parcel bindings.
"""
from __future__ import annotations

import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V13 as v13

base = v13.base
base.TARGET_TOKENS = tuple(dict.fromkeys(base.TARGET_TOKENS + (
    "baird & co. limited",
    "baird & co limited",
    "gemini business park precious metal refinery",
    "epr/cp3633kn",
    "epr/cp3633kn/v003",
    "e6 7ff",
    "02269558",
    "miller process",
    "aqua regia process",
    "renewi uk services limited",
    "shanks waste management limited",
    "jenkins lane waste management facility",
    "epr/wp3433by",
    "epr/wp3433by/v008",
    "ig11 0ad",
    "02393309",
    "thames materials limited",
    "central park dagenham",
    "epr/gb3808cw",
    "epr/gb3808cw/a001",
    "rm10 7ej",
    "03045533",
    "thames materials holdings limited",
    "c. a. blackwell (contracts) limited",
    "c a blackwell contracts limited",
    "sanofi rpa 1",
    "epr/fb3094aq",
    "epr/fb3094aq/a001",
    "rm10 7xs",
    "tq 50536 85192",
    "00570590",
    "ca blackwell group limited",
)))

if __name__ == "__main__":
    raise SystemExit(base.main())

#!/usr/bin/env python3
"""Classifier V3: bind classification to the exact Parser V15 aliases.

All original classifier quality requirements remain unchanged: official UK PRTR
or Environment Agency Pollution Inventory source, explicit reporting year,
pollutant, numeric value and unit, permit-limit exclusion and no parcel binding.
"""
from __future__ import annotations

import CLASSIFY_PRTR_PI_TARGET_RECORDS_20260722 as classifier
import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V15 as parser_v15

classifier.TARGETS = tuple(dict.fromkeys(parser_v15.base.TARGET_TOKENS))

if __name__ == "__main__":
    raise SystemExit(classifier.main())

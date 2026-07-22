#!/usr/bin/env python3
"""Classifier V2: keep PRTR/PI classification aligned with Parser V14 aliases.

The original classifier carried a small historic target list while the binary
parser had expanded to hundreds of official facility, operator, permit and
company aliases. V2 reuses the exact deduplicated parser token set. It does not
relax any source, year, pollutant, numeric value, unit, permit-limit or parcel
binding gate in the base classifier.
"""
from __future__ import annotations

import CLASSIFY_PRTR_PI_TARGET_RECORDS_20260722 as classifier
import HYDRATE_TARGET_PARSE_PRTR_PI_HMLR_20260722_V14 as parser_v14

classifier.TARGETS = tuple(dict.fromkeys(parser_v14.base.TARGET_TOKENS))

if __name__ == "__main__":
    raise SystemExit(classifier.main())

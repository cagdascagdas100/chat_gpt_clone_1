#!/usr/bin/env python3
"""Fail-closed guard for experimental brownfield-site geometry.

Any geometry from dataset=brownfield-site or quality other than authoritative
must remain diagnostic-only. It cannot create a canonical parcel match or score.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    site = doc.get("brownfield_site") or {}
    experimental = site.get("quality") != "authoritative" or site.get("dataset", "brownfield-site") == "brownfield-site"
    if not experimental:
        errors.append("EXPECTED_EXPERIMENTAL_OR_NON_AUTHORITATIVE_GEOMETRY")
    if doc.get("diagnostic_only") is not True:
        errors.append("DIAGNOSTIC_ONLY_REQUIRED")
    if doc.get("score_allowed") is not False:
        errors.append("SCORE_MUST_BE_FORBIDDEN")
    if doc.get("parcel_match_allowed") is not False:
        errors.append("PARCEL_MATCH_MUST_BE_FORBIDDEN")
    if doc.get("canonical_row_no") is not None or doc.get("canonical_parcel_id") is not None:
        errors.append("CANONICAL_IDENTITY_MUST_REMAIN_NULL")
    if doc.get("future_growth_score") is not None or doc.get("future_growth_confidence") != 0:
        errors.append("SCORE_AND_CONFIDENCE_MUST_REMAIN_NULL_ZERO")
    cap = doc.get("confidence_cap")
    if not isinstance(cap, (int, float)) or cap > 45:
        errors.append("DIAGNOSTIC_CONFIDENCE_CAP_MAX_45")
    return errors

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_json")
    ap.add_argument("--output")
    args = ap.parse_args()
    doc = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    errors = validate(doc)
    result = {"passed": not errors, "errors": errors, "diagnostic_only": doc.get("diagnostic_only")}
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0 if not errors else 2

if __name__ == "__main__":
    raise SystemExit(main())

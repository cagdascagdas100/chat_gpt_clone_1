#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

MIN_LARGE_SITE_HECTARES = 5.0
MAX_SUSPICIOUS_DWELLINGS = 5.0

def _number(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid numeric value {value!r}") from exc

def is_large_site_low_capacity_anomaly(candidate: dict) -> bool:
    hectares = _number(candidate.get("hectares"))
    maximum = _number(candidate.get("maximum_net_dwellings"))
    minimum = _number(candidate.get("minimum_net_dwellings"))
    return (
        hectares is not None and hectares >= MIN_LARGE_SITE_HECTARES
        and maximum is not None and maximum <= MAX_SUSPICIOUS_DWELLINGS
        and (minimum is None or minimum <= MAX_SUSPICIOUS_DWELLINGS)
    )

def validate_candidate(candidate: dict) -> bool:
    flagged = is_large_site_low_capacity_anomaly(candidate)
    if not flagged:
        return False
    cid = str(candidate.get("candidate_id") or "")
    eligibility = str(candidate.get("eligibility") or "")
    if not (eligibility.startswith("held") or eligibility.startswith("excluded")):
        raise ValueError(f"{cid}: large-site low-capacity anomaly must be held or excluded")
    if not str(candidate.get("capacity_anomaly_evidence") or "").strip():
        raise ValueError(f"{cid}: capacity anomaly evidence missing")
    if float(candidate.get("parcel_match_confidence_cap") or 0) != 0:
        raise ValueError(f"{cid}: anomalous record must have zero parcel confidence cap")
    if candidate.get("canonical_row_no") is not None or candidate.get("canonical_parcel_id") is not None:
        raise ValueError(f"{cid}: parcel promotion forbidden for capacity anomaly")
    if candidate.get("future_growth_score") is not None or candidate.get("future_growth_confidence") not in (0, None):
        raise ValueError(f"{cid}: score promotion forbidden for capacity anomaly")
    return True

def validate(payload: dict) -> dict:
    if payload.get("slot_id") != "future_growth_2":
        raise ValueError("wrong slot_id")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidate array missing")
    flagged = [str(c.get("candidate_id") or "") for c in candidates if validate_candidate(c)]
    return {
        "schema_version": 1,
        "slot_id": "future_growth_2",
        "executed": True,
        "flagged_candidates": flagged,
        "flagged_count": len(flagged),
        "threshold_hectares": MIN_LARGE_SITE_HECTARES,
        "threshold_maximum_dwellings": MAX_SUSPICIOUS_DWELLINGS,
        "canonical_parcel_matches": 0,
        "future_growth_scores_produced": 0,
        "actual_business_data_rows_written": 0,
        "all_passed": True,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--wave",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    out=validate(json.loads(a.wave.read_text(encoding="utf-8")))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out))
    return 0

if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def validate_provider(p: dict) -> None:
    errors=int(p.get("url_access_errors") or 0)
    brownfield=str(p.get("brownfield_status") or "")
    decision=str(p.get("decision") or "")
    uplift=p.get("parcel_or_score_confidence_uplift")
    if errors > 0 or "error" in brownfield.lower() or "404" in brownfield:
        if "not_promoted" not in decision and "warning" not in decision:
            raise ValueError("provider endpoint error cannot be promoted")
        if uplift is not False:
            raise ValueError("provider endpoint error cannot uplift parcel or score confidence")

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--wave",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    payload=json.loads(a.wave.read_text(encoding="utf-8")); provider=payload.get("provider_quality") or {}
    validate_provider(provider)
    out={"schema_version":1,"slot_id":"future_growth_2","executed":True,"provider_checked":True,"url_access_errors":int(provider.get("url_access_errors") or 0),"brownfield_status":provider.get("brownfield_status"),"confidence_uplift_applied":False,"all_passed":True,"canonical_parcel_matches":0,"future_growth_scores_produced":0,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    a.output.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8"); return 0
if __name__=="__main__": raise SystemExit(main())

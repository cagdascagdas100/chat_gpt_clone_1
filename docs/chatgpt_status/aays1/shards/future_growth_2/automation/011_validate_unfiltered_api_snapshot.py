#!/usr/bin/env python3
"""Validate a direct unfiltered Planning Data API snapshot fail-closed.

This is supplementary evidence only. It MUST NOT be labelled period=current,
and it MUST NOT create parcel matches or Future Growth scores.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from urllib.parse import urlparse

OFFICIAL_HOST = "www.planning.data.gov.uk"

def validate_snapshot(payload: dict) -> dict:
    if payload.get("slot_id") != "future_growth_2": raise ValueError("wrong slot")
    if urlparse(str(payload.get("source_url") or "")).hostname != OFFICIAL_HOST: raise ValueError("non-official host")
    if payload.get("api_period") != "unfiltered": raise ValueError("snapshot must be explicitly unfiltered")
    if payload.get("period_current_equivalent") is not False: raise ValueError("unfiltered snapshot cannot be period=current equivalent")
    if payload.get("parcel_promotion_allowed") is not False or payload.get("score_allowed") is not False: raise ValueError("promotion forbidden")
    rows=payload.get("selected_records")
    if not isinstance(rows,list) or not rows: raise ValueError("empty records")
    ids=[int(r["entity"]) for r in rows]
    if len(ids)!=len(set(ids)): raise ValueError("duplicate entity")
    results=[]
    for r in rows:
        if r.get("dataset")!="brownfield-land": raise ValueError("wrong dataset")
        if r.get("quality")!="authoritative": raise ValueError("non-authoritative row")
        if not str(r.get("point") or "").startswith("POINT"): raise ValueError("point missing")
        current=not bool(str(r.get("end-date") or "").strip())
        results.append({"entity":int(r["entity"]),"reference":str(r["reference"]),"state":"CLIENT_SIDE_CURRENT" if current else "HISTORICAL_HELD","parcel_promoted":False,"score_written":False})
    return {"source_contract":"DIRECT_UNFILTERED_API_SUPPLEMENTARY_ONLY","record_count":len(rows),"current_count":sum(x["state"]=="CLIENT_SIDE_CURRENT" for x in results),"historical_held":sum(x["state"]=="HISTORICAL_HELD" for x in results),"period_current_equivalent":False,"results":results,"actual_parcel_matches":0,"future_growth_scores_produced":0,"final_ready":False}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--snapshot',type=Path,required=True); ap.add_argument('--output-json',type=Path,required=True); a=ap.parse_args()
    out=validate_snapshot(json.loads(a.snapshot.read_text(encoding='utf-8')))
    a.output_json.parent.mkdir(parents=True,exist_ok=True); a.output_json.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({"ok":True,"current":out["current_count"],"historical_held":out["historical_held"]}))
if __name__=='__main__': main()

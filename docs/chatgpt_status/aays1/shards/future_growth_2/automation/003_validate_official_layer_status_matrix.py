#!/usr/bin/env python3
"""Validate compact future_growth_2 Batch 008 without network calls."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from urllib.parse import urlparse
ALLOWED_HOSTS={"github.com","www.enfield.gov.uk","www.havering.gov.uk","www.lambeth.gov.uk","services.arcgis.com","gis.lambeth.gov.uk"}
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("json_path",type=Path); a=ap.parse_args()
    d=json.loads(a.json_path.read_text(encoding="utf-8"))
    g=d["operation_generation"]
    total=sum(v for k,v in g.items() if k!="expected_total")
    urls=[]
    for r in d["rows"]:
        urls.append(r["service"])
        for s in r["sources"]: urls.append(s["url"])
        for z in r["layers"]:
            if "@" in z["token"]: urls.append(z["token"].split("@",1)[1])
    checks={
      "operation_count":total==g["expected_total"]==d["batch_operations_total"]==143,
      "row_count":len(d["rows"])==3,
      "layer_inventory":sum(len(r["layers"]) for r in d["rows"])==31,
      "local_sources":sum(len(r["sources"]) for r in d["rows"])==21,
      "freshness_rows":sum(len(r["freshness"]) for r in d["rows"])==15,
      "system_rows":len(d["system_validations"])==8,
      "host_allowlist":all(urlparse(u).hostname in ALLOWED_HOSTS for u in urls),
      "score_guard":d["exact_parcel_bound_rows"]==0 and d["scored_business_rows"]==0,
      "future_dates_labelled":all(f["result"]=="FUTURE_TIMETABLE" for r in d["rows"] for f in r["freshness"] if f["code"] in {"SCOPING_START","TARGET_ADOPTION"}),
    }
    print(json.dumps({"checks":checks,"pass":all(checks.values()),"operations":total},indent=2))
    return 0 if all(checks.values()) else 1
if __name__=="__main__": raise SystemExit(main())

#!/usr/bin/env python3
"""Validate future_growth_2 Batch 009 without network calls."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from urllib.parse import urlparse
ALLOWED_HOSTS={"github.com","www.enfield.gov.uk","www.havering.gov.uk","www.lambeth.gov.uk","services.arcgis.com","gis.lambeth.gov.uk","gis.london.gov.uk","gis2.london.gov.uk"}
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("json_path",type=Path); a=ap.parse_args()
    d=json.loads(a.json_path.read_text(encoding="utf-8")); g=d["operation_generation"]
    total=sum(v for k,v in g.items() if k!="expected_total")
    urls=[]
    for r in d["rows"]:
        urls.append(r["service"]); urls.extend(s[2] for s in r["current_sources"])
    urls += [d["lambeth_brownfield_layer"]["source"],d["gla_opportunity_areas"]["source"],d["gla_opportunity_areas"]["exact_layer_source"]]
    checks={
      "operation_count":total==g["expected_total"]==d["batch_operations_total"]==124,
      "row_count":len(d["rows"])==3,
      "layer_inventory":sum(len(r["layers"]) for r in d["rows"])==30,
      "local_sources":sum(len(r["current_sources"]) for r in d["rows"])==18,
      "crosschecks":sum(len(r["crosschecks"]) for r in d["rows"])==12,
      "brownfield_polygon":d["lambeth_brownfield_layer"]["geometry_type"]=="esriGeometryPolygon",
      "opportunity_polygon":d["gla_opportunity_areas"]["geometry_type"]=="esriGeometryPolygon",
      "host_allowlist":all(urlparse(u).hostname in ALLOWED_HOSTS for u in urls),
      "score_guard":d["exact_parcel_bound_rows"]==0 and d["scored_business_rows"]==0,
      "system_rows":len(d["system_validations"])==8,
      "business_zero":d["business_coverage_pct"]==0.0}
    out={"checks":checks,"pass":all(checks.values()),"operations":total}; print(json.dumps(out,indent=2)); return 0 if out["pass"] else 1
if __name__=="__main__": raise SystemExit(main())

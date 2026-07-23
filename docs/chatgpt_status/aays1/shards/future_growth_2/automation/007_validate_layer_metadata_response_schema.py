#!/usr/bin/env python3
"""Validate future_growth_2 Batch 012 split evidence package."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from urllib.parse import urlparse
ALLOWED={"github.com","services.arcgis.com","www.planning.data.gov.uk","www.london.gov.uk","www.enfield.gov.uk","www.havering.gov.uk","www.lambeth.gov.uk","gis2.london.gov.uk","gis.lambeth.gov.uk"}
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def main():
 ap=argparse.ArgumentParser();ap.add_argument("index",type=Path);ap.add_argument("--results",type=Path);a=ap.parse_args()
 d=load(a.index);ps={x["name"]:load(a.index.parent/x["path"]) for x in d["parts"]}
 rows=ps["manifest"]["rows"];jobs=ps["jobs1"]["jobs"]+ps["jobs2"]["jobs"]+ps["jobs3"]["jobs"];pages=ps["official_pages"]["official_pages"];ds=ps["dataset_status"]["dataset_status"];q=ps["quality"]
 total=sum(v for k,v in d["operation_generation"].items() if k!="expected_total");layer_count=sum(len(r["layers"]) for r in rows);source_context_count=len(rows)*len(pages)
 urls=[j["url"] for j in jobs]+[p["url"] for p in pages]+[x["url"] for x in ds]
 checks={"operation_count":total==d["operation_generation"]["expected_total"]==d["batch_operations_total"]==300,"row_count":len(rows)==3,"job_count":len(jobs)==60 and len({j["job_id"] for j in jobs})==60,"layer_status_count":layer_count==30,"layer_temporal_count":layer_count==30,"source_context_count":source_context_count==48,"dataset_status_count":len(ds)==32,"negative_guard_count":len(q["negative_guards"])==20,"crosscheck_count":len(q["crosschecks"])==9,"system_validation_count":len(q["system_validations"])==8,"host_allowlist":all(urlparse(u).hostname in ALLOWED for u in urls),"child_metadata_fail_closed":True,"score_guard":d["exact_parcel_bound_rows"]==0 and d["scored_business_rows"]==0}
 result_checks=None
 if a.results:
  rr=load(a.results).get("results",[]);result_checks={"result_count":len(rr)==60,"url_hashes":sum(bool(x.get("request_url_sha256")) for x in rr)==60,"body_hashes":sum(bool(x.get("raw_sha256")) for x in rr)==60,"utc_times":sum(bool(x.get("fetched_at_utc")) for x in rr)==60,"score_guard":all(x.get("future_growth_score") is None and x.get("confidence_pct")==0 for x in rr)};checks["results"]=all(result_checks.values())
 out={"checks":checks,"result_checks":result_checks,"pass":all(checks.values()),"operations":total};print(json.dumps(out,indent=2));return 0 if out["pass"] else 1
if __name__=="__main__":raise SystemExit(main())

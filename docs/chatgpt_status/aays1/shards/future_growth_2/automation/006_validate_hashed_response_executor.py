#!/usr/bin/env python3
"""Validate future_growth_2 Batch 011 manifest and optional hashed live result export."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from urllib.parse import urlparse, parse_qs
ALLOWED_HOSTS={"services.arcgis.com","www.planning.data.gov.uk","gis2.london.gov.uk","gis.lambeth.gov.uk",
"www.london.gov.uk","www.enfield.gov.uk","www.havering.gov.uk","www.lambeth.gov.uk",
"democracy.havering.gov.uk","consult.london.gov.uk"}
HEX64=re.compile(r"^[0-9a-f]{64}$")
def load_parts(index_path:Path):
    d=json.loads(index_path.read_text(encoding="utf-8"))
    parts={}
    for p in d["parts"]:
        parts[p["name"]]=json.loads((index_path.parent/p["path"]).read_text(encoding="utf-8"))
    parts["manifest"]["jobs"]=sum((parts[k]["jobs"] for k in ("jobs1","jobs2","jobs3")),[])
    return d,parts
def validate_manifest(index_path:Path):
    d,p=load_parts(index_path); m=p["manifest"]; s=p["sources"]; q=p["quality"]
    g=d["operation_generation"]; total=sum(v for k,v in g.items() if k!="expected_total")
    jobs=m["jobs"]; coords={(r["row_no"],str(r["lon"]),str(r["lat"])) for r in m["rows"]}
    checks={
      "operation_count":total==g["expected_total"]==d["batch_operations_total"]==240,
      "job_count":len(jobs)==60,
      "unique_jobs":len({x["job_id"] for x in jobs})==60,
      "job_numbers":sorted(x["job_no"] for x in jobs)==list(range(1,61)),
      "official_job_hosts":all(urlparse(x["url"]).hostname in ALLOWED_HOSTS for x in jobs),
      "official_source_hosts":all(urlparse(x["url"]).hostname in ALLOWED_HOSTS for x in s["current_sources"]+s["dataset_rows"]),
      "canonical_coordinates":all((x["row_no"],str(x["canonical_lon"]),str(x["canonical_lat"])) in coords for x in jobs),
      "source_count":len(s["current_sources"])==32,
      "dataset_status_count":len(s["dataset_rows"])==32,
      "temporal_count":len(q["temporal_rows"])==20,
      "score_gate_count":len(q["score_gates"])==20,
      "runtime_controls":len(q["runtime_controls"])==5,
      "system_count":len(q["system_validations"])==8,
      "score_guard":d["exact_parcel_bound_rows"]==0 and d["scored_business_rows"]==0,
    }
    return d,m,checks
def validate_results(m,results_path:Path):
    r=json.loads(results_path.read_text(encoding="utf-8")); rows=r.get("results",[])
    by={x["job_id"]:x for x in rows}
    checks={"result_count":len(rows)==60,"unique_result_jobs":len(by)==60,
      "all_manifest_jobs":set(by)=={x["job_id"] for x in m["jobs"]}}
    if checks["all_manifest_jobs"]:
        checks.update({
          "raw_hashes":all(HEX64.fullmatch(x.get("raw_sha256","")) and hashlib.sha256(x.get("raw_body","").encode()).hexdigest()==x["raw_sha256"] for x in rows),
          "url_hashes":all(HEX64.fullmatch(x.get("request_url_sha256","")) and hashlib.sha256(x.get("request_url","").encode()).hexdigest()==x["request_url_sha256"] for x in rows),
          "timestamps":all(isinstance(x.get("fetched_at_utc"),str) and x["fetched_at_utc"].endswith("Z") for x in rows),
          "score_guard":all(x.get("future_growth_score") is None and x.get("confidence_pct")==0 and x.get("data_status")=="NO_DATA" for x in rows),
        })
    return checks
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("index_path",type=Path); ap.add_argument("--results",type=Path)
    a=ap.parse_args(); d,m,c=validate_manifest(a.index_path)
    result={"manifest_checks":c,"manifest_pass":all(c.values()),"operations":d["batch_operations_total"]}
    if a.results:
        rc=validate_results(m,a.results); result["result_checks"]=rc; result["results_pass"]=all(rc.values())
    print(json.dumps(result,indent=2)); return 0 if all(v for k,v in result.items() if k.endswith("_pass")) else 1
if __name__=="__main__": raise SystemExit(main())

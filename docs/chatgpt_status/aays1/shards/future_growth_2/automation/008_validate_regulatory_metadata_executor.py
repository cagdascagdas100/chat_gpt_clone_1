#!/usr/bin/env python3
"""Validate future_growth_2 Batch 013 and optional live hashed export."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_HOSTS={
    "services.arcgis.com","www.planning.data.gov.uk","gis2.london.gov.uk",
    "gis.lambeth.gov.uk","www.enfield.gov.uk","www.havering.gov.uk",
    "www.lambeth.gov.uk","www.gov.uk","consult.london.gov.uk","www.london.gov.uk",
    "github.com"
}
def load(p:Path): return json.loads(p.read_text(encoding="utf-8"))
def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("index",type=Path)
    ap.add_argument("--results",type=Path)
    a=ap.parse_args()
    d=load(a.index)
    docs={p["name"]:load(a.index.parent/p["path"]) for p in d["parts"]}
    jobs=docs["jobs1"]["jobs"]+docs["jobs2"]["jobs"]+docs["jobs3"]["jobs"]
    metas=docs["metadata"].get("metadata_jobs") or [{"job_id":f"META_{r['row_no']}_{lid}","row_no":r["row_no"],"parcel_id":r["parcel_id"],"lpa":r["lpa"],"url":f"{r['service']}/{lid}?f=pjson"} for r in docs["manifest"]["rows"] for lid,_ in r["layers"]]
    sources=docs["sources"]["official_sources"]
    standards=docs["sources"]["standards"]
    quality=docs["quality"]
    total=sum(v for k,v in d["operation_generation"].items() if k!="expected_total")
    urls=[j["url"] for j in jobs]+[j["url"] for j in metas]+[s["url"] for s in sources]+[s["source"] for s in standards]
    checks={
      "operation_count": total==d["operation_generation"]["expected_total"]==d["batch_operations_total"]==360,
      "exact_query_count": len(jobs)==60 and len({j["job_id"] for j in jobs})==60,
      "metadata_query_count": len(metas)==30 and len({j["job_id"] for j in metas})==30,
      "source_count": len(sources)==20 and sum(bool(x["new"]) for x in sources)==10,
      "standard_rows": sum(len(x["fields"]) for x in standards)==40,
      "temporal_rows": len(quality["temporal_rules"])*3==24,
      "score_gate_rows": len(quality["score_gates"])*3==24,
      "crosschecks": len(quality["crosschecks"])==19,
      "system_rows": len(quality["system_validations"])==10,
      "host_allowlist": all(urlparse(u).hostname in ALLOWED_HOSTS for u in urls),
      "https_only": all(urlparse(u).scheme=="https" for u in urls),
      "score_guard": d["exact_parcel_bound_rows"]==0 and d["scored_business_rows"]==0 and d["quality_policy"]["unbound_score_policy"].endswith("NO_DATA"),
    }
    result_checks=None
    if a.results:
        r=load(a.results); rr=r.get("results",[])
        by={x.get("job_id"):x for x in rr}
        expected={j["job_id"] for j in jobs+metas}
        def hex64(x): return isinstance(x,str) and len(x)==64 and all(c in "0123456789abcdef" for c in x.lower())
        result_checks={
          "result_count": r.get("result_count")==90 and len(rr)==90 and set(by)==expected,
          "url_hashes": all(hex64(x.get("request_url_sha256")) for x in rr),
          "body_hashes": all(hex64(x.get("raw_sha256")) for x in rr),
          "timestamps": all(isinstance(x.get("fetched_at_utc"),str) and x["fetched_at_utc"] for x in rr),
          "raw_preserved": all("raw_body" in x for x in rr),
          "score_guard": all(x.get("future_growth_score") is None and x.get("confidence_pct")==0 and x.get("data_status")=="NO_DATA" for x in rr),
          "hash_recompute": all(hashlib.sha256(x.get("request_url","").encode()).hexdigest()==x.get("request_url_sha256") and hashlib.sha256(x.get("raw_body","").encode()).hexdigest()==x.get("raw_sha256") for x in rr),
        }
    out={"checks":checks,"pass":all(checks.values()),"operations":total,"result_checks":result_checks,"results_pass":None if result_checks is None else all(result_checks.values())}
    print(json.dumps(out,indent=2))
    return 0 if out["pass"] and (result_checks is None or out["results_pass"]) else 1
if __name__=="__main__": raise SystemExit(main())

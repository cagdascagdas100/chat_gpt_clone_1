#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
def main():
    p=argparse.ArgumentParser();p.add_argument("--web-json",required=True,type=Path);p.add_argument("--index",required=True,type=Path);a=p.parse_args()
    x=json.loads(a.web_json.read_text(encoding="utf-8"));html=a.index.read_text(encoding="utf-8")
    checks=[
    ("slot",x.get("slot_id")=="internet_access_3"),
    ("waiting_status",x.get("status")=="WAITING_TWO_REAL_VALIDATED_RUNTIME_RECEIPTS"),
    ("receipts_zero",x.get("real_validated_receipts_available")==0),
    ("required_two",x.get("required_receipts")==2),
    ("exact_false",x.get("exact_reproducibility_pass") is False),
    ("automatic_false",x.get("automatic_acceptance") is False),
    ("six_gates",isinstance(x.get("gates"),list) and len(x["gates"])==6),
    ("gate_numbers",[g.get("gate_no") for g in x["gates"]]==list(range(1,7))),
    ("no_business",x.get("actual_business_data_rows_written")==0),
    ("no_scores",x.get("scores_written")==0),
    ("truth_flags",all(x.get(k) is False for k in ("fake_data","db_write","migration","production_deploy","final_ready"))),
    ("index_fetch","runtime_reproducibility_latest.json" in html),
    ("index_section",'id="reproducibility"' in html),
    ("index_summary",'id="reproducibilitySummary"' in html),
    ("index_render","rep.gates.forEach" in html),
    ("index_metric","Tekrar üretilebilirlik" in html)]
    for n,ok in checks:print("PASS" if ok else "FAIL",n)
    print(json.dumps({"passed":sum(ok for _,ok in checks),"total":len(checks)}))
    return 0 if all(ok for _,ok in checks) else 1
if __name__=="__main__":raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[6]
WEB=ROOT/"england_map_web/data/aays_18_slots/internet_access_2"
html=(WEB/"index.html").read_text(encoding="utf-8")
examples=json.loads((WEB/"candidate_integrity_examples_latest.json").read_text(encoding="utf-8"))
progress=json.loads((WEB/"progress_latest.json").read_text(encoding="utf-8"))
contract=json.loads((WEB/"provenance_contract_latest.json").read_text(encoding="utf-8"))
ops=[]
for name in ("operations_latest.json","scope_operations_latest.json","operations_provenance_latest.json"):
    ops.extend(json.loads((WEB/name).read_text(encoding="utf-8"))["operations"])
by_id={row["id"]:row for row in ops}
checks={
  "candidate_examples_fetch":"candidate_integrity_examples_latest.json" in html,
  "candidate_examples_table":"candidateIntegrityExamples" in html,
  "candidate_audit_table":"candidateAudit" in html,
  "candidate_audit_fetch":"candidate_jsonl_integrity_latest.json" in html,
  "six_examples":len(examples.get("examples",[]))==6,
  "examples_not_real":examples.get("real_parcel_rows")==0 and examples.get("actual_business_data_rows_written")==0,
  "no_data_methods":{x["required_method"] for x in examples["examples"] if x["candidate_class"]=="NO_DATA"}=={"NO_POSTCODE","POSTCODE_NOT_IN_CURRENT_R2"},
  "reject_examples":sum(x["decision"]=="REJECT_FAIL_CLOSED" for x in examples["examples"])==2,
  "validation_215":contract["combined_validation"]=={"passed":215,"total":215},
  "candidate_tests_25":contract["candidate_integrity_selftest"]=={"passed":25,"total":25},
  "operation_ids_unique":len(by_id)==len(ops),
  "review_only":progress.get("actual_business_data_rows_written")==0 and progress.get("final_ready") is False and contract.get("final_ready") is False,
}
failed=[name for name,ok in checks.items() if not ok]
if failed: raise AssertionError(f"failed: {failed}")
print(json.dumps({"status":"PASS","tests_passed":len(checks),"tests_total":len(checks),"test_names":list(checks),"actual_business_data_rows_written":0,"final_ready":False},sort_keys=True))

#!/usr/bin/env python3
from __future__ import annotations
import json
from collections import Counter
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
id_counts=Counter(row["id"] for row in ops)
duplicate_ids={operation_id for operation_id,count in id_counts.items() if count>1}
by_id={row["id"]:row for row in ops}
blocked=[row for row in by_id.values() if row["status"]!="DONE"]
checks={
  "candidate_examples_fetch":"candidate_integrity_examples_latest.json" in html,
  "candidate_examples_table":"candidateIntegrityExamples" in html,
  "candidate_audit_table":"candidateAudit" in html,
  "candidate_audit_fetch":"candidate_jsonl_integrity_latest.json" in html,
  "consistency_table":"reviewConsistency" in html,
  "consistency_audit_fetch":"review_contract_consistency_latest.json" in html,
  "six_examples":len(examples.get("examples",[]))==6,
  "examples_not_real":examples.get("real_parcel_rows")==0 and examples.get("actual_business_data_rows_written")==0,
  "no_data_methods":{x["required_method"] for x in examples["examples"] if x["candidate_class"]=="NO_DATA"}=={"NO_POSTCODE","POSTCODE_NOT_IN_CURRENT_R2"},
  "reject_examples":sum(x["decision"]=="REJECT_FAIL_CLOSED" for x in examples["examples"])==2,
  "validation_260":contract["combined_validation"]=={"passed":260,"total":260},
  "candidate_tests_25":contract["candidate_integrity_selftest"]=={"passed":25,"total":25},
  "consistency_tests_14":contract["review_contract_consistency_selftest"]=={"passed":14,"total":14},
  "wrapper_tests_36":contract["run_and_audit_wrapper_contract"]=={"passed":36,"total":36},
  "historical_override_ids_exact":duplicate_ids=={55,90} and by_id[55]["status"]=="DONE" and by_id[90]["status"]=="DONE",
  "operation_range_121":sorted(by_id)==list(range(1,122)),
  "single_current_blocker":len(blocked)==1 and blocked[0]["id"]==121,
  "review_only":progress.get("actual_business_data_rows_written")==0 and progress.get("final_ready") is False and contract.get("final_ready") is False,
}
failed=[name for name,ok in checks.items() if not ok]
if failed: raise AssertionError(f"failed: {failed}")
print(json.dumps({"status":"PASS","tests_passed":len(checks),"tests_total":len(checks),"test_names":list(checks),"actual_business_data_rows_written":0,"final_ready":False},sort_keys=True))

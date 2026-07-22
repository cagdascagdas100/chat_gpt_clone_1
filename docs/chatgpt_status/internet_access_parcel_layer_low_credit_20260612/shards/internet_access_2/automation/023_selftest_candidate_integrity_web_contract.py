#!/usr/bin/env python3
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[6]
WEB=ROOT/"england_map_web/data/aays_18_slots/internet_access_2"
html=(WEB/"index.html").read_text(encoding="utf-8")
examples=json.loads((WEB/"candidate_integrity_examples_latest.json").read_text(encoding="utf-8"))
prov_examples=json.loads((WEB/"provenance_examples_latest.json").read_text(encoding="utf-8"))
progress=json.loads((WEB/"progress_latest.json").read_text(encoding="utf-8"))
contract=json.loads((WEB/"provenance_contract_latest.json").read_text(encoding="utf-8"))
ops=[]
for name in ("operations_latest.json","scope_operations_latest.json","operations_provenance_latest.json"): ops.extend(json.loads((WEB/name).read_text(encoding="utf-8"))["operations"])
id_counts=Counter(row["id"] for row in ops);duplicate_ids={i for i,c in id_counts.items() if c>1};by_id={row["id"]:row for row in ops};blocked=[row for row in by_id.values() if row["status"]!="DONE"]
resolution_ids={x["id"] for x in examples["examples"] if x.get("postcode_resolution")}
code_examples={x["id"] for x in prov_examples["examples"] if x["id"] in {8,9,10} and x.get("accuracy_class") in {"RECOMPUTED_EXECUTION_CODE_SHA256","EXACT_SINGLE_SUBSTITUTION","EXACT_20_ARTIFACT_SHA256_CHAIN"}}
checks={
"candidate_examples_fetch":"candidate_integrity_examples_latest.json" in html,"candidate_examples_table":"candidateIntegrityExamples" in html,"candidate_audit_table_and_fetch":"candidateAudit" in html and "candidate_jsonl_integrity_latest.json" in html,"consistency_table":"reviewConsistency" in html,"consistency_audit_fetch":"review_contract_consistency_latest.json" in html,"twelve_candidate_examples":len(examples.get("examples",[]))==12,"examples_not_real":examples.get("real_parcel_rows")==0 and examples.get("actual_business_data_rows_written")==0,"no_data_methods":{x["required_method"] for x in examples["examples"] if x["candidate_class"]=="NO_DATA"}=={"NO_POSTCODE","POSTCODE_NOT_IN_CURRENT_R2"},"coverage_examples_and_rejects":{11,12}.issubset(resolution_ids) and sum(x["decision"]=="REJECT_FAIL_CLOSED" for x in examples["examples"])==3 and "Coverage fallback" in html,"ten_provenance_examples":len(prov_examples.get("examples",[]))==10,"execution_code_examples":code_examples=={8,9,10},"validation_415":contract["combined_validation"]=={"passed":415,"total":415},"candidate_tests_25":contract["candidate_integrity_selftest"]=={"passed":25,"total":25},"resolution_tests_24":contract["postcode_resolution_selftest"]=={"passed":24,"total":24},"consistency_tests_15":contract["review_contract_consistency_selftest"]=={"passed":15,"total":15},"wrapper_tests_54":contract["run_and_audit_wrapper_contract"]=={"passed":54,"total":54},"zip_container_tests_18":contract["zip_container_safety_selftest"]=={"passed":18,"total":18},"provenance_tests_24_chain_20":contract["provenance_selftest"]=={"passed":24,"total":24} and len(contract["required_chain"])==20 and "twenty-artifact" in html,"execution_code_hash_fields":all(x in html for x in ("base_runner_code_sha256","runtime_runner_code_sha256","coverage_aware_extractor_code_sha256","coverage_aware_carrier_code_sha256","runtime_exact_extractor_substitution_verified")),"historical_override_ids_exact":duplicate_ids=={55,90} and by_id[55]["status"]=="DONE" and by_id[90]["status"]=="DONE","operation_range_152_single_blocker":sorted(by_id)==list(range(1,153)) and len(blocked)==1 and blocked[0]["id"]==152,"review_only":progress.get("actual_business_data_rows_written")==0 and progress.get("final_ready") is False and contract.get("final_ready") is False}
failed=[name for name,ok in checks.items() if not ok]
if failed: raise AssertionError(f"failed: {failed}")
print(json.dumps({"status":"PASS","tests_passed":len(checks),"tests_total":len(checks),"test_names":list(checks),"actual_business_data_rows_written":0,"final_ready":False},sort_keys=True))

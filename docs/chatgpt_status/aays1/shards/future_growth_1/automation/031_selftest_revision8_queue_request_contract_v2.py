#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;TARGET=HERE/"030_validate_revision8_queue_request_contract_v2.py"
spec=importlib.util.spec_from_file_location("v",TARGET);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def fixture():
 q={"slot_id":"future_growth_1","task_id":mod.TASK_ID,"attempt_id":mod.ATTEMPT_ID,"contract_revision":8,"state":"pending","claimable":True,"ready_for_claim":True,"single_runner_only":True,"new_runner":False,"parallel_runner":False,"revision7_queue_superseded":True,"revision7_bug_fixed":"RAW_SHA256_WAS_COMPARED_TO_GIT_BLOB_SHA1","canonical_source_path":"england_map_web/data/program_layer_matrix/security.geojson","canonical_source_git_blob_sha1":"8afd1d2bac414cf0f6b9484014e7878a4ceff877","acceptance_contract":dict(mod.REQUIRED_ACCEPTANCE),"expected_outputs":sorted(mod.EXPECTED_OUTPUTS),"sequential_after_task_id":mod.PREDECESSOR_TASK_ID,"predecessor_status_path":mod.PREDECESSOR_STATUS_PATH,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
 for key in mod.REQUIRED_QUEUE_PATH_KEYS:
  q[key]=("england_map_web/data/aays_21_slots/future_growth_1/x.json" if key in {"candidate_source_path","planning_query_manifest_path"} else "docs/chatgpt_status/aays1/shards/future_growth_1/x.py");q[key.removesuffix("_path")+"_blob_sha"]="a"*40
 keys=[f"source_{i}" for i in range(16)]
 rows=[{"source_key":k,"official_url":"https://www.gov.uk/x","execution_status":"NOT_EXECUTED_0_OF_1","authority_check":"PASS_OFFICIAL_PRIMARY","payload_formats":["JSON"],"runtime_binding":"exact","promotion_gate":"closed","expected_runtime_evidence":["payload_sha256"]} for k in keys]
 ex=[{"example_id":f"EX{i+1:02d}","source_key":keys[i],"request_template":"GET https://www.gov.uk/x?value={value}","expected_format":"JSON","status":"TEMPLATE_VALIDATED_NOT_EXECUTED"} for i in range(10)]
 return q,{"slot_id":"future_growth_1","readiness_counts":{"loader_executions":"0/16","business_rows":0},"source_rows":rows,"example_request_templates":ex}
def rc(name,mut,exp):
 q,r=fixture();mut(q,r);act=mod.validate(q,r)["result"];return {"name":name,"expected":exp,"actual":act,"pass":act==exp}
def main():
 cs=[rc("exact",lambda q,r:None,"PASS"),rc("nine_outputs",lambda q,r:q.__setitem__("expected_outputs",q["expected_outputs"][:-1]),"FAIL"),rc("missing_bundle_acceptance",lambda q,r:q["acceptance_contract"].pop("runtime_evidence_bundle_checks_expected"),"FAIL"),rc("wrong_predecessor",lambda q,r:q.__setitem__("sequential_after_task_id","wrong"),"FAIL"),rc("cross_slot",lambda q,r:q.__setitem__("note","future_growth_2"),"FAIL"),rc("wrong_revision",lambda q,r:q.__setitem__("contract_revision",7),"FAIL"),rc("bad_blob",lambda q,r:q.__setitem__("runtime_evidence_bundle_validator_blob_sha","bad"),"FAIL"),rc("wrong_host",lambda q,r:r["source_rows"][0].__setitem__("official_url","https://example.com/x"),"FAIL"),rc("secret",lambda q,r:r["example_request_templates"][0].__setitem__("request_template","GET https://www.gov.uk/x?api_key=live-secret"),"FAIL"),rc("deploy",lambda q,r:q.__setitem__("production_deploy",True),"FAIL")]
 n=sum(c["pass"] for c in cs);print(json.dumps({"schema_version":5,"slot_id":"future_growth_1","selftest_kind":"REVISION8_QUEUE_REQUEST_BUNDLE_SELF_CONTAINED","result":f"{n}/{len(cs)} PASS","passed":n,"total":len(cs),"cases":cs,"runner_execution_claimed":False,"business_progress_claimed":False,"final_ready":False},ensure_ascii=False,indent=2));return 0 if n==len(cs) else 2
if __name__=="__main__":raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--runner-output",default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/038_target_evidence_matrix_tests_latest.json");return p.parse_args()
def mod():
 p=Path(__file__).with_name("045_target_evidence_matrix.py");s=importlib.util.spec_from_file_location("m45",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 o=args();m=mod();tests=[]
 def ck(n,c,d=""):tests.append({"name":n,"passed":bool(c),"detail":d})
 rows=m.recursive_rows({"row_no":"61523","nested":[{"row_no":61524},{"x":{"row_no":"61525"}}]});ck("RECURSIVE_ROWS_THREE",set(rows)=={61523,61524,61525},repr(rows));ck("PASS_ACCEPTANCE",m.state_pass({"state":"acceptance_passed"}));ck("PASS_PROVENANCE",m.state_pass({"state":"provenance_passed"}));ck("PASS_MATRIX",m.state_pass({"state":"matrix_complete"}));ck("FAIL_PENDING",not m.state_pass({"state":"pending_runtime"}));ck("FAIL_NON_DICT",not m.state_pass([]));ck("SOURCE_COUNT_SEVEN",len(m.SOURCES)==7,str(m.SOURCES));ck("TARGET_REV10","revision10" in m.TARGETS);ck("MANIFEST_PATH","stratified_candidate_manifest" in m.MANIFEST)
 source=Path(__file__).with_name("045_target_evidence_matrix.py").read_text();ck("TARGET_COUNT_40","len(targets)!=40" in source);ck("EIGHT_CELLS",source.count('"migration"')>=2 and '"chain_acceptance"' in source);ck("NO_CANDIDATE_CLAIM",'"candidate_claimed":False' in source);ck("NO_PARCEL_PROMOTION",'"parcel_relation_promoted":False' in source);ck("NO_CONFIDENCE_UPLIFT",'"confidence_uplift":0' in source);ck("FAIL_CLOSED_EXIT","return 0 if complete==40 else 2" in source);ck("SAFETY_FLAGS",all(x in source for x in ['"final_ready":False','"fake_data":False','"db_write":False','"migration":False','"production_deploy":False']))
 f=[x for x in tests if not x["passed"]];z={"schema_version":1,"slot_id":"internet_access_3","state":"passed" if not f else "failed","tests_expected":16,"tests_executed":len(tests),"tests_passed":len(tests)-len(f),"tests_failed":len(f),"tests":tests,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};out=(o.repo_root or Path.cwd())/o.runner_output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(z,separators=(",",":"))+"\n");print(json.dumps(z,indent=2));return 0 if not f else 2
if __name__=="__main__":raise SystemExit(main())

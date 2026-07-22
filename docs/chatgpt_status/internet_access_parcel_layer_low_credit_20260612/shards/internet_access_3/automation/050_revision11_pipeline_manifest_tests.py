#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--runner-output",default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/040_revision11_pipeline_manifest_tests_latest.json");return p.parse_args()
def main():
 o=args();p=Path(__file__).with_name("049_full_pipeline_revision11_entry.py");s=p.read_text();tests=[]
 def ck(n,c,d=""):tests.append({"name":n,"passed":bool(c),"detail":d})
 refs=["044_release_licence_attribution_bundle_tests.py","046_target_evidence_matrix_tests.py","048_web_acceptance_snapshot_tests.py","041_full_pipeline_revision10_entry.py","043_release_licence_attribution_bundle.py","045_target_evidence_matrix.py","047_web_acceptance_snapshot.py"];ck("ALL_REFERENCES",all(x in s for x in refs),repr(refs));ck("ALL_FILES",all((p.parent/x).exists() for x in refs),repr(refs));ck("STEPS_39",'effective_pipeline_steps":39' in s);ck("TESTS_212",'contract_tests_target":212' in s);ck("SOURCE_CHECKS_28",'official_source_checks_target":28' in s);ck("SAMPLE_384",'sample_size_target":384' in s);ck("TARGETS_40",'transparent_target_rows":40' in s and 'target_evidence_rows_required":40' in s);ck("BROWSER_ACCEPTANCE",'browser_acceptance_required":True' in s);ck("ATTRIBUTION_4",'attribution_sources_required":4' in s);ck("SAFETY",all(x in s for x in ['"final_ready":False','"fake_data":False','"db_write":False','"migration":False','"production_deploy":False']))
 f=[x for x in tests if not x["passed"]];z={"schema_version":1,"slot_id":"internet_access_3","state":"passed" if not f else "failed","tests_expected":10,"tests_executed":len(tests),"tests_passed":len(tests)-len(f),"tests_failed":len(f),"tests":tests,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};out=(o.repo_root or Path.cwd())/o.runner_output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(z,separators=(",",":"))+"\n");print(json.dumps(z,indent=2));return 0 if not f else 2
if __name__=="__main__":raise SystemExit(main())

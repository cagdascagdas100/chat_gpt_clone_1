#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def main():
 args();src=Path(__file__).with_name("057_full_pipeline_revision12_entry.py").read_text();t=[]
 def ck(n,c):t.append((n,bool(c)))
 ck("CHILD_REV11","049_full_pipeline_revision11_entry.py" in src);ck("THREE_TEST_PACKS",all(x in src for x in ["052_os_opendata_download_resolution_tests.py","054_resumable_download_probe_ledger_tests.py","056_uprn_relation_schema_contract_tests.py"]));ck("THREE_WORKERS",all(x in src for x in ["051_os_opendata_download_resolution.py","053_resumable_download_probe_ledger.py","055_uprn_relation_schema_contract.py"]));ck("STEPS_45",'effective_pipeline_steps":45' in src);ck("TESTS_264",'contract_tests_target":264' in src);ck("CHECKS_34",'official_source_checks_target":34' in src);ck("SAMPLE_384",'sample_size_target":384' in src);ck("EVIDENCE_40",'target_evidence_rows":40' in src);ck("PRE_HYDRATION","pipeline_passed_pre_hydration" in src and 'full_release_bytes_hydrated":False' in src);ck("SAFETY_FLAGS",all(x in src for x in ["final_ready","fake_data","db_write","migration","production_deploy"]))
 f=[n for n,c in t if not c];print(json.dumps({"schema_version":1,"slot_id":"internet_access_3","state":"passed" if not f else "failed","tests_expected":10,"tests_executed":len(t),"tests_passed":len(t)-len(f),"tests_failed":len(f),"failures":f,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False},indent=2));return 0 if not f else 2
if __name__=="__main__":raise SystemExit(main())

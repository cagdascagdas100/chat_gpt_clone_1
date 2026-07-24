#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def main():
 o=args();r=o.repo_root.resolve() if o.repo_root else next(p for p in [Path.cwd(),*Path(__file__).resolve().parents] if (p/"docs").exists() and (p/"england_map_web").exists());a=Path(__file__).parent;p=(a/"069_full_pipeline_revision14_entry.py").read_text();checks=[]
 def ck(n,x):checks.append({"name":n,"passed":bool(x)})
 for f in ["065_codepoint_open_exact_crosscheck.py","066_codepoint_open_exact_crosscheck_tests.py","067_official_postcode_source_consensus.py","068_official_postcode_source_consensus_tests.py","063_full_pipeline_revision13_entry.py"]:ck("PATH_"+f,(a/f).exists() and f in p)
 ck("STEP_55",'"effective_pipeline_steps":55' in p);ck("TEST_346",'"contract_tests_target":346' in p);ck("SOURCE_46",'"official_source_checks_target":46' in p);ck("SAMPLE_384",'"sample_size_target":384' in p);ck("SAFETY",all(x in p for x in ['"final_ready":False','"fake_data":False','"db_write":False','"migration":False','"production_deploy":False']))
 failed=[x for x in checks if not x["passed"]];out={"schema_version":1,"slot_id":"internet_access_3","tests_executed":len(checks),"tests_passed":len(checks)-len(failed),"tests_failed":len(failed),"checks":checks,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
 if o.repo_root:
  x=r/"docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/050_revision14_pipeline_manifest_tests_latest.json";x.parent.mkdir(parents=True,exist_ok=True);x.write_text(json.dumps(out,separators=(",",":"))+"\n")
 print(json.dumps(out,indent=2));return 0 if not failed else 2
if __name__=="__main__":raise SystemExit(main())

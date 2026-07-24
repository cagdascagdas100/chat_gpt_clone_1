#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--runner-output",default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/037_release_licence_attribution_bundle_tests_latest.json");return p.parse_args()
def module():
 p=Path(__file__).with_name("043_release_licence_attribution_bundle.py");s=importlib.util.spec_from_file_location("m43",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 o=args();m=module();tests=[]
 def ck(n,c,d=""):tests.append({"name":n,"passed":bool(c),"detail":d})
 ck("FOUR_REGISTRIES",len(m.REGISTRIES)==4,str(m.REGISTRIES));ck("FOUR_ATTRIBUTION_GROUPS",set(m.ATTRIBUTIONS)==set(m.REGISTRIES));ck("FOUR_REQUIRED_GROUPS",set(m.REQUIRED)==set(m.REGISTRIES))
 for key in sorted(m.REGISTRIES):
  text=" ".join(m.ATTRIBUTIONS[key]).lower();ck("TOKENS_"+key.upper(),all(t in text for t in m.REQUIRED[key]),text)
 ck("HMLR_OS_CONTRACT","ac0000851063" in " ".join(m.ATTRIBUTIONS["hmlr"]).lower());ck("UPRN_GEOPLACE","geoplace" in " ".join(m.ATTRIBUTIONS["uprn"]).lower());ck("ONSPD_ROYAL_MAIL","royal mail" in " ".join(m.ATTRIBUTIONS["onspd"]).lower())
 source=Path(__file__).with_name("043_release_licence_attribution_bundle.py").read_text();ck("NO_PROMOTION_GUARD",'"parcel_relations_promoted":0' in source and '"confidence_uplifts":0' in source);ck("SAFETY_FLAGS",all(x in source for x in ['"final_ready":False','"fake_data":False','"db_write":False','"migration":False','"production_deploy":False']))
 f=[x for x in tests if not x["passed"]];z={"schema_version":1,"slot_id":"internet_access_3","state":"passed" if not f else "failed","tests_expected":12,"tests_executed":len(tests),"tests_passed":len(tests)-len(f),"tests_failed":len(f),"tests":tests,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};out=(o.repo_root or Path.cwd())/o.runner_output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(z,separators=(",",":"))+"\n");print(json.dumps(z,indent=2));return 0 if not f else 2
if __name__=="__main__":raise SystemExit(main())

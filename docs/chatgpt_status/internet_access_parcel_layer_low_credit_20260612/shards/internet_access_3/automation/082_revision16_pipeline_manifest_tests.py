#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def main():
 o=args();r=o.repo_root.resolve() if o.repo_root else next(p for p in [Path.cwd(),*Path(__file__).resolve().parents] if (p/"docs").exists() and (p/"england_map_web").exists())
 a=Path(__file__).parent;text=(a/"081_full_pipeline_revision16_entry.py").read_text(encoding="utf-8");checks=[]
 def ck(n,v):checks.append({"name":n,"passed":bool(v)})
 ck("revision14_child","069_full_pipeline_revision14_entry.py" in text)
 ck("resource_preflight_worker","077_runtime_resource_download_preflight.py" in text)
 ck("hydration_worker","071_full_release_hydration_manifest.py" in text)
 ck("corrected_join_worker","079_exact_uprn_postcode_join_revision16.py" in text)
 ck("runtime_acceptance_worker","083_revision16_runtime_acceptance.py" in text)
 ck("effective_64","effective_pipeline_steps\":64" in text)
 ck("tests_422","contract_tests_target\":422" in text)
 ck("source_checks_62","official_source_checks_target\":62" in text)
 ck("ratios","common_exact_ratio_minimum\":0.95" in text and "uprn_join_ratio_minimum\":0.98" in text)
 ck("safety","parcel_relations_promoted\":0" in text and "final_ready\":False" in text)
 failed=[x for x in checks if not x["passed"]]
 print(json.dumps({"schema_version":1,"slot_id":"internet_access_3","test_suite":"revision16_pipeline_manifest","tests_total":len(checks),"tests_passed":len(checks)-len(failed),"tests_failed":len(failed),"checks":checks,"final_ready":False},indent=2))
 return 0 if not failed else 2
if __name__=="__main__":raise SystemExit(main())

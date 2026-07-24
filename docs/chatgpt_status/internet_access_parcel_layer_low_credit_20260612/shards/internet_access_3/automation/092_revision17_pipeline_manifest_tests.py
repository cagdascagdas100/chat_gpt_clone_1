#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path);return p.parse_args()
def main():
 p=Path(__file__).with_name('091_full_pipeline_revision17_entry.py');s=p.read_text();checks={'cache_worker':'085_release_cache_identity_ledger.py' in s,'checkpoint_worker':'087_exact_uprn_postcode_join_revision17.py' in s,'acceptance':'089_revision17_runtime_acceptance.py' in s,'cache_before_hydration':s.index('085_release_cache_identity_ledger.py')<s.index('071_full_release_hydration_manifest.py'),'hydration_before_join':s.index('071_full_release_hydration_manifest.py')<s.index('087_exact_uprn_postcode_join_revision17.py'),'join_before_acceptance':s.index('087_exact_uprn_postcode_join_revision17.py')<s.index('089_revision17_runtime_acceptance.py'),'steps69':"effective_pipeline_steps':69" in s,'tests488':"contract_tests_target':488" in s,'checks70':"official_source_checks_target':70" in s,'safety':"production_deploy':False" in s};tests=[{'name':k,'passed':v} for k,v in checks.items()];passed=sum(x['passed'] for x in tests);print(json.dumps({'tests':tests,'passed':passed,'failed':len(tests)-passed},indent=2));return 0 if passed==len(tests) else 1
if __name__=='__main__':raise SystemExit(main())

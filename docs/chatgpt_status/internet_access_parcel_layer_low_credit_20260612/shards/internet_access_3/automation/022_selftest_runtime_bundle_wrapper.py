#!/usr/bin/env python3
"""Static network-free tests for runtime bundle wrapper 021."""
from __future__ import annotations
import argparse, importlib.util, json, tempfile
from pathlib import Path
ROOT=Path(__file__).parent
def load():
    s=importlib.util.spec_from_file_location("w021",ROOT/"021_run_pipeline_and_validate_runtime_bundle.py"); assert s and s.loader
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def main():
    m=load(); results=[]
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); args=argparse.Namespace(git_ref="HEAD",download_retries=4,download_timeout_seconds=600,ofcom_zip=None,ofcom_url=None)
        p=m.build_pipeline_command(args,root,root/"work"); assert any(x.endswith("015_materialize_exact_blobs_and_run_targeted_slot3.py") for x in p); results.append("pipeline_015")
        assert "--git-ref" in p and "--work-root" in p; results.append("pipeline_exact_args")
        v=m.build_validation_command(root,root/"work"); assert any(x.endswith("019_runtime_bundle_gate.py") for x in v); results.append("validator_019")
        assert "--candidate-manifest" in v and "--candidates-jsonl" in v and "--slice-manifest" in v; results.append("three_runtime_inputs")
        source=(ROOT/"021_run_pipeline_and_validate_runtime_bundle.py").read_text()
        for literal in ('"actual_business_data_rows_written":0','"scores_written":0','"fake_data":False','"db_write":False','"migration":False','"production_deploy":False','"final_ready":False'): assert literal in source
        results.append("truth_flags")
        assert "--validate-existing-only" in source and "SKIPPED_VALIDATE_EXISTING_ONLY" in source; results.append("no_repeat_validate_mode")
    print(json.dumps({"passed":len(results),"total":len(results),"results":[{"test":x,"state":"PASS"} for x in results]},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())

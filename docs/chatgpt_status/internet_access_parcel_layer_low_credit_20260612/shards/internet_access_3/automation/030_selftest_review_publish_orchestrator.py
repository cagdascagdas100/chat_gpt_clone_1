#!/usr/bin/env python3
"""Static network-free tests for 029_run_validate_import_and_accept_web.py."""
from __future__ import annotations
import argparse, importlib.util, json, tempfile
from pathlib import Path
from typing import Any
ROOT=Path(__file__).parent

def load()->Any:
    spec=importlib.util.spec_from_file_location("orchestrator029",ROOT/"029_run_validate_import_and_accept_web.py")
    if spec is None or spec.loader is None: raise RuntimeError("cannot load orchestrator029")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def main()->int:
    module=load(); results=[]
    with tempfile.TemporaryDirectory() as temp:
        repo=Path(temp); work=repo/"work"; args=argparse.Namespace(git_ref="HEAD",download_retries=4,download_timeout_seconds=600,validate_existing_only=False,ofcom_zip=None,ofcom_url=None)
        wrapper=module.build_wrapper_command(args,repo,work); assert any(value.endswith("021_run_pipeline_and_validate_runtime_bundle.py") for value in wrapper); results.append("wrapper_021"); assert "--repo-root" in wrapper and "--work-root" in wrapper and "--git-ref" in wrapper; results.append("wrapper_exact_args")
        args.validate_existing_only=True; assert "--validate-existing-only" in module.build_wrapper_command(args,repo,work); results.append("validate_existing_only")
        importer=module.build_import_command(repo,work,repo/"web"); assert any(value.endswith("023_import_validated_runtime_bundle_to_web.py") for value in importer) and importer[-1].endswith("runtime_results_latest.json"); results.append("importer_023")
        http=module.build_http_command(repo,"http://127.0.0.1:8012/x/",work); assert any(value.endswith("025_http_8012_acceptance.py") for value in http) and "--base-url" in http; results.append("http_025")
        browser=module.build_browser_command(repo,"http://127.0.0.1:8012/x/index.html",work); assert any(value.endswith("027_browser_console_acceptance.py") for value in browser) and "--url" in browser; results.append("browser_027")
    source=(ROOT/"029_run_validate_import_and_accept_web.py").read_text(encoding="utf-8")
    for literal in ('"actual_business_data_rows_written":0','"scores_written":0','"fake_data":False','"db_write":False','"migration":False','"production_deploy":False','"final_ready":False','state["polygon_popup_acceptance"]=False'): assert literal in source
    results.append("truth_flags"); assert source.count("run_checked(build_wrapper_command")==1; results.append("single_pipeline_execution"); assert "ATOMIC_REVIEW_WEB_IMPORT" in source; results.append("atomic_import_stage"); assert "HTTP_8012_STATIC_DOM_ACCEPTANCE" in source and "BROWSER_CONSOLE_PROGRESS_DOM_ACCEPTANCE" in source; results.append("optional_acceptance_stages")
    print(json.dumps({"passed":len(results),"total":len(results),"results":[{"test":value,"state":"PASS"} for value in results]},sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())

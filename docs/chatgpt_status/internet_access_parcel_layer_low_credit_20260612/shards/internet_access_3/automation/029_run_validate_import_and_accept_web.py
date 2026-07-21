#!/usr/bin/env python3
"""Run pipeline validation, import real review results, and optionally accept the web page."""
from __future__ import annotations
import argparse, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
SLOT_ID="internet_access_3"
AUTOMATION_RELATIVE=Path("docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/automation")
WEB_RELATIVE=Path("england_map_web/data/aays_18_slots/internet_access_3")
WRAPPER="021_run_pipeline_and_validate_runtime_bundle.py"; IMPORTER="023_import_validated_runtime_bundle_to_web.py"; HTTP_ACCEPTANCE="025_http_8012_acceptance.py"; BROWSER_ACCEPTANCE="027_browser_console_acceptance.py"

def run_checked(command:list[str],state:dict[str,Any],name:str)->None:
    completed=subprocess.run(command,capture_output=True,text=True,check=False); state.setdefault("stages",[]).append({"name":name,"returncode":completed.returncode,"stdout_tail":completed.stdout[-4000:],"stderr_tail":completed.stderr[-4000:]})
    if completed.returncode!=0: raise RuntimeError(f"{name} blocked with return code {completed.returncode}")

def build_wrapper_command(args:argparse.Namespace,repo_root:Path,work_root:Path)->list[str]:
    command=[sys.executable,str(repo_root/AUTOMATION_RELATIVE/WRAPPER),"--repo-root",str(repo_root),"--work-root",str(work_root),"--git-ref",args.git_ref,"--download-retries",str(args.download_retries),"--download-timeout-seconds",str(args.download_timeout_seconds)]
    if args.validate_existing_only: command.append("--validate-existing-only")
    if args.ofcom_zip: command.extend(["--ofcom-zip",str(args.ofcom_zip.resolve())])
    if args.ofcom_url: command.extend(["--ofcom-url",args.ofcom_url])
    return command

def build_import_command(repo_root:Path,work_root:Path,web_root:Path)->list[str]: return [sys.executable,str(repo_root/AUTOMATION_RELATIVE/IMPORTER),"--runtime-gate",str(work_root/"internet_access_3_runtime_bundle_validation_latest.json"),"--output",str(web_root/"runtime_results_latest.json")]
def build_http_command(repo_root:Path,base_url:str,work_root:Path)->list[str]: return [sys.executable,str(repo_root/AUTOMATION_RELATIVE/HTTP_ACCEPTANCE),"--base-url",base_url,"--output",str(work_root/"internet_access_3_http_8012_acceptance_latest.json")]
def build_browser_command(repo_root:Path,page_url:str,work_root:Path)->list[str]: return [sys.executable,str(repo_root/AUTOMATION_RELATIVE/BROWSER_ACCEPTANCE),"--url",page_url,"--output",str(work_root/"internet_access_3_browser_console_acceptance_latest.json")]

def parse_args()->argparse.Namespace:
    parser=argparse.ArgumentParser(); parser.add_argument("--repo-root",required=True,type=Path); parser.add_argument("--work-root",type=Path); parser.add_argument("--git-ref",default="HEAD"); parser.add_argument("--ofcom-zip",type=Path); parser.add_argument("--ofcom-url"); parser.add_argument("--download-retries",type=int,default=4); parser.add_argument("--download-timeout-seconds",type=int,default=600); parser.add_argument("--validate-existing-only",action="store_true"); parser.add_argument("--http-base-url"); parser.add_argument("--browser-page-url"); return parser.parse_args()

def main()->int:
    args=parse_args(); repo_root=args.repo_root.resolve(); work_root=(args.work_root or (repo_root/"outputs/internet_access_3_verified_run")).resolve(); web_root=repo_root/WEB_RELATIVE; receipt_path=work_root/"internet_access_3_review_publish_and_acceptance_latest.json"
    state:dict[str,Any]={"schema_version":1,"slot_id":SLOT_ID,"started_at":datetime.now(timezone.utc).isoformat(),"validate_existing_only":args.validate_existing_only,"http_requested":bool(args.http_base_url),"browser_requested":bool(args.browser_page_url),"actual_business_data_rows_written":0,"scores_written":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}; work_root.mkdir(parents=True,exist_ok=True)
    try:
        for name in (WRAPPER,IMPORTER,HTTP_ACCEPTANCE,BROWSER_ACCEPTANCE):
            path=repo_root/AUTOMATION_RELATIVE/name
            if not path.is_file(): raise RuntimeError(f"required automation missing: {path}")
        run_checked(build_wrapper_command(args,repo_root,work_root),state,"PIPELINE_AND_RUNTIME_VALIDATION"); run_checked(build_import_command(repo_root,work_root,web_root),state,"ATOMIC_REVIEW_WEB_IMPORT")
        imported=json.loads((web_root/"runtime_results_latest.json").read_text(encoding="utf-8"))
        if imported.get("status")!="REAL_RUNTIME_BUNDLE_VALIDATED_REVIEW_ONLY": raise RuntimeError("imported runtime results state mismatch")
        state["counts"]=imported["counts"]; state["hashes"]=imported["hashes"]; state["samples"]=imported.get("samples",[])
        if args.http_base_url: run_checked(build_http_command(repo_root,args.http_base_url,work_root),state,"HTTP_8012_STATIC_DOM_ACCEPTANCE"); state["http_8012_acceptance"]=True
        else: state["http_8012_acceptance"]=False; state["http_state"]="SKIPPED_NO_URL"
        if args.browser_page_url: run_checked(build_browser_command(repo_root,args.browser_page_url,work_root),state,"BROWSER_CONSOLE_PROGRESS_DOM_ACCEPTANCE"); state["browser_console_acceptance"]=True
        else: state["browser_console_acceptance"]=False; state["browser_state"]="SKIPPED_NO_URL"
        state["polygon_popup_acceptance"]=False; state["state"]="COMPLETE_REVIEW_RUNTIME_IMPORTED_ACCEPTANCE_OPTIONAL"; receipt_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps({k:v for k,v in state.items() if k not in {"stages","samples"}},sort_keys=True)); return 0
    except Exception as exc:
        state["state"]="BLOCKED_REVIEW_PUBLISH_OR_ACCEPTANCE_GATE"; state["error"]=f"{type(exc).__name__}: {exc}"; receipt_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(state["error"],file=sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())

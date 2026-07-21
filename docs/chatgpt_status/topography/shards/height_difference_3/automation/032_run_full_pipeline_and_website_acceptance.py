#!/usr/bin/env python3
"""Run the existing real pipeline, then fail-closed website publication acceptance."""
from __future__ import annotations
import argparse, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+".tmp")
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temp.replace(path)

def run(command: list[str]) -> dict[str,Any]:
    started=now()
    proc=subprocess.run(command,text=True,capture_output=True,check=False)
    return {"started_at":started,"finished_at":now(),"command":command,"exit_code":proc.returncode,"stdout_tail":proc.stdout[-16000:],"stderr_tail":proc.stderr[-16000:]}

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--security-geojson",required=True,type=Path)
    ap.add_argument("--output-dir",required=True,type=Path)
    ap.add_argument("--web-runtime-status",required=True,type=Path)
    ap.add_argument("--web-operations-history",required=True,type=Path)
    ap.add_argument("--web-json",type=Path,default=Path("england_map_web/data/aays_18_slots/height_difference_3/verified_examples_latest.json"))
    ap.add_argument("--web-geojson",type=Path,default=Path("england_map_web/data/aays_18_slots/height_difference_3/verified_examples_latest.geojson"))
    ap.add_argument("--base-url",default="http://127.0.0.1:8012")
    ap.add_argument("--script-dir",type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument("--operation-start",type=int)
    ap.add_argument("--timeout",type=int,default=120)
    ap.add_argument("--preflight-timeout",type=int,default=30)
    ap.add_argument("--acceptance-timeout",type=int,default=30)
    ap.add_argument("--runtime-poll-seconds",type=float,default=0.5)
    ap.add_argument("--min-free-bytes",type=int,default=4*1024*1024*1024)
    ap.add_argument("--expected-git-blob-sha1",default="8afd1d2bac414cf0f6b9484014e7878a4ceff877")
    args=ap.parse_args()
    if min(args.timeout,args.preflight_timeout,args.acceptance_timeout)<1: raise ValueError("timeouts must be positive")
    scripts=args.script_dir.resolve()
    bootstrap=scripts/"029_preflight_then_execute_resumable.py"
    acceptance=scripts/"031_publish_verify_three_examples_port8012.py"
    for path in (bootstrap,acceptance):
        if not path.is_file(): raise FileNotFoundError(path)
    out=args.output_dir.resolve(); out.mkdir(parents=True,exist_ok=True)
    report_path=out/"full_pipeline_and_website_acceptance_execution.json"
    state={"schema_version":1,"slot_id":"height_difference_3","updated_at":now(),"status":"029_PIPELINE_STARTING","pipeline":None,"website_acceptance":None,"single_shared_runner_only":True,"new_runner_created":False,"parallel_runner_used":False,"queue_submission":False,"final_ready":False,"product_final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    write(report_path,state)
    pipeline=[sys.executable,str(bootstrap),"--security-geojson",str(args.security_geojson.resolve()),"--output-dir",str(out),"--web-runtime-status",str(args.web_runtime_status.resolve()),"--web-operations-history",str(args.web_operations_history.resolve()),"--timeout",str(args.timeout),"--preflight-timeout",str(args.preflight_timeout),"--runtime-poll-seconds",str(args.runtime_poll_seconds),"--min-free-bytes",str(args.min_free_bytes),"--expected-git-blob-sha1",args.expected_git_blob_sha1]
    if args.operation_start is not None: pipeline.extend(["--operation-start",str(args.operation_start)])
    state["pipeline"]=run(pipeline); state["updated_at"]=now()
    if state["pipeline"]["exit_code"]!=0:
        state["status"]="BLOCKED_029_PIPELINE_OR_PREFLIGHT"; write(report_path,state); return int(state["pipeline"]["exit_code"])
    state["status"]="031_WEBSITE_ACCEPTANCE_RUNNING"; write(report_path,state)
    command=[sys.executable,str(acceptance),"--output-dir",str(out),"--web-json",str(args.web_json.resolve()),"--web-geojson",str(args.web_geojson.resolve()),"--web-runtime-status",str(args.web_runtime_status.resolve()),"--base-url",args.base_url,"--timeout",str(args.acceptance_timeout),"--acceptance-output",str(out/"website_acceptance_latest.json")]
    state["website_acceptance"]=run(command); state["updated_at"]=now()
    if state["website_acceptance"]["exit_code"]!=0:
        state["status"]="BLOCKED_031_WEBSITE_PUBLICATION_OR_PORT_8012_ACCEPTANCE"; write(report_path,state); return int(state["website_acceptance"]["exit_code"])
    state["status"]="THREE_REAL_EXAMPLES_PUBLISHED_AND_PORT_8012_ACCEPTED"; write(report_path,state)
    print(json.dumps({"ok":True,"status":state["status"],"report":str(report_path)})); return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok":False,"error":f"{type(exc).__name__}: {exc}"}),file=sys.stderr); raise

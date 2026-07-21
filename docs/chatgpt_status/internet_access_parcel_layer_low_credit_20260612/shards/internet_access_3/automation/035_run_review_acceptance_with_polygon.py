#!/usr/bin/env python3
"""Run the existing review chain once, discover the map contract, then optionally accept an exact popup."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).parent

def build_commands(repo_root:Path,git_ref:str,validate_existing_only:bool,base_url:str,run_polygon:bool)->list[list[str]]:
 output=repo_root/'outputs/internet_access_3_verified_run';web=repo_root/'england_map_web/data/aays_18_slots/internet_access_3'
 first=[sys.executable,str(ROOT/'029_run_validate_import_and_accept_web.py'),'--repo-root',str(repo_root),'--git-ref',git_ref]
 if validate_existing_only:first.append('--validate-existing-only')
 discovery=[sys.executable,str(ROOT/'031_discover_polygon_popup_contract.py'),'--repo-root',str(repo_root),'--output',str(output/'internet_access_3_map_popup_discovery_latest.json')]
 commands=[first,discovery]
 if run_polygon:
  commands.append([sys.executable,str(ROOT/'033_polygon_popup_acceptance.py'),'--runtime-results',str(web/'runtime_results_latest.json'),'--discovery',str(output/'internet_access_3_map_popup_discovery_latest.json'),'--base-url',base_url,'--output',str(output/'internet_access_3_polygon_popup_acceptance_latest.json')])
 return commands

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--repo-root',type=Path,required=True);ap.add_argument('--git-ref',default='HEAD');ap.add_argument('--validate-existing-only',action='store_true');ap.add_argument('--base-url',default='http://127.0.0.1:8012/');ap.add_argument('--run-polygon',action='store_true');a=ap.parse_args()
 receipts=[]
 for cmd in build_commands(a.repo_root.resolve(),a.git_ref,a.validate_existing_only,a.base_url,a.run_polygon):
  proc=subprocess.run(cmd,text=True,capture_output=True);receipts.append({'command':cmd,'returncode':proc.returncode,'stdout':proc.stdout[-4000:],'stderr':proc.stderr[-4000:]})
  if proc.returncode!=0:print(json.dumps({'status':'FAILED','receipts':receipts},ensure_ascii=False));return proc.returncode
 print(json.dumps({'status':'PASS','receipts':receipts,'polygon_executed':a.run_polygon},ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())

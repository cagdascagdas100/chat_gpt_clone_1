#!/usr/bin/env python3
"""Run official Ofcom preflight and refresh preview without business writes."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from typing import Any
SLOT_ID='internet_access_1'
def sha256_file(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def load_json(path:Path)->dict[str,Any]:
 data=json.loads(path.read_text(encoding='utf-8'))
 if not isinstance(data,dict):raise ValueError(f'JSON object expected: {path}')
 return data
def run_checked(command:list[str],timeout_seconds:int)->dict[str,Any]:
 result=subprocess.run(command,text=True,capture_output=True,timeout=timeout_seconds,check=False)
 if result.returncode!=0:raise RuntimeError(f'command failed rc={result.returncode}; stderr={result.stderr[-1000:]!r}')
 return {'command':command,'returncode':result.returncode,'stdout_tail':result.stdout[-1000:],'stderr_tail':result.stderr[-1000:]}
def validate_preflight(data:dict[str,Any])->None:
 if data.get('slot_id')!=SLOT_ID:raise ValueError('preflight slot mismatch')
 if data.get('status')!='PASS_PREVIEW_ONLY':raise ValueError('preflight did not pass')
 if int(data.get('checks_passed',0))<18:raise ValueError('preflight check count below 18')
 if data.get('business_rows_written')!=0:raise ValueError('preflight business write detected')
 if data.get('migration_applied') is not False:raise ValueError('preflight migration detected')
 if data.get('fake_data') is not False:raise ValueError('preflight fake-data flag invalid')
 if data.get('final_ready') is not False:raise ValueError('preflight final_ready must remain false')
def validate_refresh(data:dict[str,Any])->None:
 if data.get('slot_id')!=SLOT_ID:raise ValueError('refresh slot mismatch')
 legacy=int(data.get('legacy_rows_in_slot',-1));refreshed=int(data.get('refreshed_preview_rows',-1));no_data=int(data.get('no_data_rows',-1))
 if legacy<=0:raise ValueError('refresh legacy row count invalid')
 if refreshed<0 or no_data<0 or refreshed+no_data!=legacy:raise ValueError('refresh row accounting mismatch')
 if int(data.get('unique_postcodes',0))<=0:raise ValueError('refresh unique postcode count invalid')
 if data.get('actual_business_rows_written')!=0:raise ValueError('refresh business write detected')
 if data.get('migration_applied') is not False:raise ValueError('refresh migration detected')
 if data.get('fake_data') is not False or data.get('db_write') is not False:raise ValueError('refresh safety flag invalid')
 if data.get('production_deploy') is not False or data.get('final_ready') is not False:raise ValueError('refresh final/deploy flag invalid')
 for row in data.get('rows',[]):
  if row.get('migration_state')!='VERIFIED_PREVIEW_NOT_APPLIED':raise ValueError('refreshed row migration state invalid')
 for row in data.get('no_data',[]):
  if row.get('status')!='NO_DATA_NOT_INFERRED':raise ValueError('no-data row was inferred')
def main()->int:
 p=argparse.ArgumentParser();p.add_argument('--matrix',type=Path,required=True);p.add_argument('--ofcom-zip',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--automation-dir',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--timeout-seconds',type=int,default=600);a=p.parse_args()
 matrix=a.matrix.resolve();ofcom_zip=a.ofcom_zip.resolve();out=a.output_dir.resolve();auto=a.automation_dir.resolve()
 if not matrix.is_file():raise FileNotFoundError(f'canonical matrix not found: {matrix}')
 if not ofcom_zip.is_file():raise FileNotFoundError(f'Ofcom ZIP not found: {ofcom_zip}')
 if matrix==ofcom_zip:raise ValueError('matrix and Ofcom ZIP must be different files')
 if a.timeout_seconds<1:raise ValueError('timeout must be positive')
 pre_script=auto/'014_preflight_official_bulk_inputs.py';refresh_script=auto/'001_refresh_ofcom_r2_postcode.py'
 if not pre_script.is_file() or not refresh_script.is_file():raise FileNotFoundError('required 001/014 automation scripts not found')
 out.mkdir(parents=True,exist_ok=True);pre_out=out/'official_bulk_preflight.json';refresh_out=out/'official_r2_refresh_preview.json';manifest_out=out/'official_bulk_orchestration_manifest.json'
 pre_run=run_checked([sys.executable,str(pre_script),'--matrix',str(matrix),'--ofcom-zip',str(ofcom_zip),'--output',str(pre_out)],a.timeout_seconds);pre=load_json(pre_out);validate_preflight(pre)
 refresh_run=run_checked([sys.executable,str(refresh_script),'--matrix',str(matrix),'--ofcom-zip',str(ofcom_zip),'--output',str(refresh_out)],a.timeout_seconds);refresh=load_json(refresh_out);validate_refresh(refresh)
 summary={'legacy_rows_in_slot':refresh['legacy_rows_in_slot'],'unique_postcodes':refresh['unique_postcodes'],'refreshed_preview_rows':refresh['refreshed_preview_rows'],'no_data_rows':refresh['no_data_rows'],'preflight_checks_passed':pre['checks_passed']}
 manifest={'schema_version':1,'slot_id':SLOT_ID,'status':'PASS_PREVIEW_ONLY_NOT_MIGRATED','input_files':{'canonical_matrix':str(matrix),'canonical_matrix_sha256':sha256_file(matrix),'official_ofcom_zip':str(ofcom_zip),'official_ofcom_zip_sha256':sha256_file(ofcom_zip)},'tool_outputs':{'preflight':str(pre_out),'refresh_preview':str(refresh_out)},'run_results':{'preflight':pre_run,'refresh_preview':refresh_run},'summary':summary,'actual_business_rows_written':0,'migration_applied':False,'fake_data':False,'db_write':False,'production_deploy':False,'final_ready':False}
 manifest_out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'slot_id':SLOT_ID,'status':manifest['status'],**summary,'manifest':str(manifest_out),'migration_applied':False},ensure_ascii=False));return 0
if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as exc:
  print(json.dumps({'slot_id':SLOT_ID,'status':'BLOCKED_FAIL_CLOSED','error':f'{type(exc).__name__}: {exc}','actual_business_rows_written':0,'migration_applied':False,'fake_data':False,'final_ready':False},ensure_ascii=False),file=sys.stderr);raise

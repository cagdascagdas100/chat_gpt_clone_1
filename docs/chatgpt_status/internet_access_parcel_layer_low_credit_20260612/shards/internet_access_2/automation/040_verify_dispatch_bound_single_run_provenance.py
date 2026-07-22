#!/usr/bin/env python3
"""Bind the fresh 13/13 dispatch execution gate into the completed provenance chain."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, re
from pathlib import Path
from typing import Any
BASE_SCRIPT=Path(__file__).with_name('034_verify_extended_single_run_provenance.py')
spec=importlib.util.spec_from_file_location('extended_provenance',BASE_SCRIPT)
if spec is None or spec.loader is None:raise RuntimeError('cannot import extended provenance verifier')
extended=importlib.util.module_from_spec(spec);spec.loader.exec_module(extended)
SLOT_ID='internet_access_2';HEX64=re.compile(r'^[0-9a-f]{64}$');COMMIT_RE=re.compile(r'^[0-9a-f]{40,64}$')
def sha(path:Path)->str:
 if not path.is_file():raise ValueError(f'required provenance artifact missing: {path.name}')
 d=hashlib.sha256()
 with path.open('rb') as h:
  for c in iter(lambda:h.read(1024*1024),b''):d.update(c)
 return d.hexdigest()
def load(path:Path)->dict[str,Any]:
 if not path.is_file():raise ValueError(f'dispatch execution gate missing: {path.name}')
 p=json.loads(path.read_text(encoding='utf-8-sig'))
 if not isinstance(p,dict):raise ValueError('dispatch execution gate must be an object')
 return p
def hex64(v:Any,label:str)->str:
 s=str(v or '')
 if not HEX64.fullmatch(s):raise ValueError(f'{label} is not lowercase SHA-256')
 return s
def audit(work_root:Path,web_root:Path,expected_review_head_sha:str,audit_output:Path|None=None)->dict[str,Any]:
 expected=str(expected_review_head_sha or '')
 if not COMMIT_RE.fullmatch(expected):raise ValueError('expected review head SHA must be lowercase 40-64 hex')
 base=extended.audit(work_root,web_root,None)
 if base.get('status')!='PASS_EXTENDED_SINGLE_RUN_PROVENANCE_CHAIN_AUDITED_REVIEW_ONLY' or int(base.get('provenance_artifact_count',-1))!=20:raise ValueError('extended provenance base contract mismatch')
 base_chain=hex64(base.get('provenance_chain_sha256'),'extended provenance chain')
 gate_path=web_root/'dispatch_execution_gate_latest.json';gate=load(gate_path)
 if gate.get('slot_id')!=SLOT_ID:raise ValueError('dispatch execution gate slot_id mismatch')
 if gate.get('status')!='PASS_FRESH_13_OF_13_DISPATCH_EXECUTION_GATE' or gate.get('dispatch_permitted') is not True:raise ValueError('dispatch execution gate status mismatch')
 if int(gate.get('gate_count',-1))!=13 or int(gate.get('passed_gate_count',-1))!=13 or int(gate.get('blocked_gate_count',-1))!=0:raise ValueError('dispatch execution gate count mismatch')
 if int(gate.get('evidence_file_count',-1))!=8:raise ValueError('dispatch execution evidence file count mismatch')
 hex64(gate.get('evidence_chain_sha256'),'dispatch evidence chain')
 if gate.get('review_pr_head_sha')!=expected or gate.get('expected_review_head_sha')!=expected:raise ValueError('dispatch execution review head SHA mismatch')
 if int(gate.get('actual_business_data_rows_written',-1))!=0 or gate.get('final_ready') is not False:raise ValueError('dispatch execution gate review-only boundary mismatch')
 gate_sha=sha(gate_path);chain=hashlib.sha256((base_chain+'\n'+gate_sha).encode('ascii')).hexdigest()
 result=dict(base);result.update({'schema_version':6,'status':'PASS_DISPATCH_BOUND_SINGLE_RUN_PROVENANCE_CHAIN_AUDITED_REVIEW_ONLY','base_extended_provenance_artifact_count':20,'dispatch_execution_gate_artifact_count':1,'provenance_artifact_count':21,'extended_provenance_chain_sha256':base_chain,'dispatch_execution_gate_sha256':gate_sha,'dispatch_evidence_chain_sha256':gate['evidence_chain_sha256'],'dispatch_review_pr_head_sha':expected,'provenance_chain_sha256':chain,'actual_business_data_rows_written':0,'scores_written':0,'db_write':False,'migration':False,'production_deploy':False,'final_ready':False})
 if audit_output:audit_output.parent.mkdir(parents=True,exist_ok=True);audit_output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 return result
def main()->int:
 p=argparse.ArgumentParser();p.add_argument('--work-root',required=True,type=Path);p.add_argument('--web-root',required=True,type=Path);p.add_argument('--expected-review-head-sha',required=True);p.add_argument('--audit-output',type=Path);a=p.parse_args();print(json.dumps(audit(a.work_root,a.web_root,a.expected_review_head_sha,a.audit_output),sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())

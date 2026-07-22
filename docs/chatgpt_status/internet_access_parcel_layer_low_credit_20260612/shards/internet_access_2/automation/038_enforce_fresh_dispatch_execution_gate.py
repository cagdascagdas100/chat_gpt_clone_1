#!/usr/bin/env python3
"""Re-evaluate all thirteen dispatch gates immediately before network execution."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
READINESS_SCRIPT=Path(__file__).with_name('011_runner_dispatch_readiness.py')
spec=importlib.util.spec_from_file_location('ia2_readiness',READINESS_SCRIPT)
if spec is None or spec.loader is None: raise RuntimeError('cannot import readiness evaluator')
readiness=importlib.util.module_from_spec(spec);spec.loader.exec_module(readiness)
SLOT_ID='internet_access_2';COMMIT_RE=re.compile(r'^[0-9a-f]{40,64}$')
EXPECTED_GATE_IDS={'SLOT_ID','CHECKPOINT','STATUS','OWNERSHIP','SLOT_HEARTBEAT','SLOT_TASK','ALLOWED_PATH','WATCHER_FRESH','RUNNER_FRESH','QUEUE_HEAD_FREE','REVIEW_MERGED','PR_MERGEABLE','NO_DIRECT_PUSH'}
FILES={'checkpoint':'checkpoint.json','status':'status.json','heartbeat':'heartbeat.json','current_task':'current_task.json','ownership':'ownership.json','watcher':'watcher_heartbeat.txt','active_runner_task':'active_runner_task.json','review_pr':'review_pr.json'}
def sha(path:Path)->str:
 d=hashlib.sha256()
 with path.open('rb') as h:
  for c in iter(lambda:h.read(1024*1024),b''):d.update(c)
 return d.hexdigest()
def load(path:Path)->dict[str,Any]:
 p=json.loads(path.read_text(encoding='utf-8-sig'))
 if not isinstance(p,dict):raise ValueError(f'evidence must be object: {path.name}')
 return p
def audit(evidence_root:Path,expected_review_head_sha:str,output:Path|None=None,*,now:datetime|None=None,freshness_seconds:int=300)->dict[str,Any]:
 expected=str(expected_review_head_sha or '')
 if not COMMIT_RE.fullmatch(expected):raise ValueError('expected review head SHA must be lowercase 40-64 hex')
 paths={k:evidence_root/v for k,v in FILES.items()};missing=[p.name for p in paths.values() if not p.is_file()]
 if missing:raise ValueError('dispatch evidence missing: '+', '.join(missing))
 checkpoint=load(paths['checkpoint']);status=load(paths['status']);heartbeat=load(paths['heartbeat']);current=load(paths['current_task']);ownership=load(paths['ownership']);active=load(paths['active_runner_task']);review=load(paths['review_pr']);watcher=readiness.parse_kv_text(paths['watcher']);moment=now or datetime.now(timezone.utc)
 report=readiness.evaluate(checkpoint,status,heartbeat,current,ownership,watcher,active,review,now=moment,freshness_seconds=freshness_seconds)
 gates=report.get('gates') or [];ids=[g.get('gate_id') for g in gates]
 if report.get('status')!='READY_FOR_EXISTING_RUNNER_DISPATCH' or report.get('dispatch_permitted') is not True:raise ValueError('dispatch readiness is not permitted')
 if int(report.get('gate_count',-1))!=13 or int(report.get('passed_gate_count',-1))!=13 or int(report.get('blocked_gate_count',-1))!=0:raise ValueError('dispatch gate count is not 13/13')
 if len(ids)!=len(set(ids)) or set(ids)!=EXPECTED_GATE_IDS:raise ValueError('dispatch gate IDs mismatch')
 if any(g.get('state')!='PASS' or g.get('blocker') is not None for g in gates):raise ValueError('dispatch gate contains non-PASS evidence')
 if review.get('merged') is not True or review.get('base')!='main' or review.get('mergeable') is not True or review.get('draft') is not False:raise ValueError('final integration PR contract mismatch')
 actual_head=str(review.get('head_sha') or '')
 if actual_head!=expected:raise ValueError('final integration PR head SHA mismatch')
 if active.get('runner_heartbeat_fresh') is not True:raise ValueError('shared runner heartbeat is not fresh')
 hashes={k:sha(v) for k,v in sorted(paths.items())};chain=hashlib.sha256('\n'.join(hashes[k] for k in sorted(hashes)).encode('ascii')).hexdigest()
 result={'schema_version':1,'slot_id':SLOT_ID,'status':'PASS_FRESH_13_OF_13_DISPATCH_EXECUTION_GATE','dispatch_permitted':True,'gate_count':13,'passed_gate_count':13,'blocked_gate_count':0,'gate_ids':ids,'expected_review_head_sha':expected,'review_pr_number':review.get('number'),'review_pr_head_sha':actual_head,'freshness_seconds':freshness_seconds,'evidence_file_count':len(hashes),'evidence_sha256':hashes,'evidence_chain_sha256':chain,'single_shared_runner_only':True,'new_runner_started':False,'ownership_claimed':False,'queue_entry_written':False,'actual_business_data_rows_written':0,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False,'final_ready':False,'evaluated_at':moment.isoformat().replace('+00:00','Z')}
 if output:output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 return result
def main()->int:
 p=argparse.ArgumentParser();p.add_argument('--evidence-root',required=True,type=Path);p.add_argument('--expected-review-head-sha',required=True);p.add_argument('--output',type=Path);p.add_argument('--freshness-seconds',type=int,default=300);a=p.parse_args();print(json.dumps(audit(a.evidence_root,a.expected_review_head_sha,a.output,freshness_seconds=a.freshness_seconds),sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())

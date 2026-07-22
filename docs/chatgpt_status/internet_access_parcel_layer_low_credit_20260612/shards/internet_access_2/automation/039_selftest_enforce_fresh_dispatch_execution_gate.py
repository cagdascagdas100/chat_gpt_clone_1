#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,json,tempfile
from datetime import datetime,timezone,timedelta
from pathlib import Path
SCRIPT=Path(__file__).with_name('038_enforce_fresh_dispatch_execution_gate.py');spec=importlib.util.spec_from_file_location('gate',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
NOW=datetime(2026,7,21,21,0,tzinfo=timezone.utc);HEAD='a'*40;passed=[]
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v)+'\n',encoding='utf-8')
def fixture(root):
 common={'slot_id':'internet_access_2'};dump(root/'checkpoint.json',dict(common,sequence=0,final_ready=False));dump(root/'status.json',dict(common,state='ready_for_claim',owner_page_session_id=None));dump(root/'heartbeat.json',dict(common,state='unclaimed',stale=True));dump(root/'current_task.json',dict(common,state='idle',task_id=None,allowed_paths=['england_map_web/data/aays_18_slots/internet_access_2'],direct_push_forbidden=True));dump(root/'ownership.json',dict(common,state='unclaimed',lease_token_hash=None));(root/'watcher_heartbeat.txt').write_text('updated_at='+NOW.isoformat()+'\n',encoding='utf-8');dump(root/'active_runner_task.json',{'slot_id':'internet_access_2','task_id':None,'status':'IDLE','runner_heartbeat_fresh':True,'runner_last_heartbeat_at':NOW.isoformat()});dump(root/'review_pr.json',{'number':999,'state':'closed','merged':True,'base':'main','mergeable':True,'draft':False,'head_sha':HEAD})
def check(n,v):
 if not v:raise AssertionError(n)
 passed.append(n)
def fail(n,mut,text,head=HEAD):
 with tempfile.TemporaryDirectory() as t:
  r=Path(t);fixture(r);mut(r)
  try:m.audit(r,head,now=NOW)
  except ValueError as e:
   if text not in str(e):raise AssertionError(f'{n}:{e}')
   passed.append(n)
  else:raise AssertionError(n)
with tempfile.TemporaryDirectory() as t:
 r=Path(t);fixture(r);out=r/'out.json';x=m.audit(r,HEAD,out,now=NOW)
 for n,v in [('status',x['status']=='PASS_FRESH_13_OF_13_DISPATCH_EXECUTION_GATE'),('dispatch',x['dispatch_permitted'] is True),('gates',x['passed_gate_count']==x['gate_count']==13),('ids',set(x['gate_ids'])==m.EXPECTED_GATE_IDS),('evidence_count',x['evidence_file_count']==8),('chain',len(x['evidence_chain_sha256'])==64),('head',x['review_pr_head_sha']==HEAD),('output',out.is_file()),('single_runner',x['single_shared_runner_only'] is True),('review_only',x['actual_business_data_rows_written']==0 and x['final_ready'] is False)]:check(n,v)
fail('stale_watcher',lambda r:(r/'watcher_heartbeat.txt').write_text('updated_at='+(NOW-timedelta(hours=1)).isoformat()+'\n'),'dispatch readiness')
fail('runner_stale',lambda r:dump(r/'active_runner_task.json',{'slot_id':'internet_access_2','task_id':None,'status':'IDLE','runner_heartbeat_fresh':False}),'dispatch readiness')
fail('other_queue_task',lambda r:dump(r/'active_runner_task.json',{'slot_id':'other','task_id':'x','status':'pickup_requested','runner_heartbeat_fresh':True}),'dispatch readiness')
fail('review_unmerged',lambda r:dump(r/'review_pr.json',{'number':999,'state':'open','merged':False,'base':'main','mergeable':True,'draft':False,'head_sha':HEAD}),'dispatch readiness')
fail('review_draft',lambda r:dump(r/'review_pr.json',{'number':999,'state':'closed','merged':True,'base':'main','mergeable':True,'draft':True,'head_sha':HEAD}),'final integration PR')
fail('head_mismatch',lambda r:None,'head SHA mismatch',head='b'*40)
fail('checkpoint_changed',lambda r:dump(r/'checkpoint.json',{'slot_id':'internet_access_2','sequence':1,'final_ready':False}),'dispatch readiness')
fail('ownership_claimed',lambda r:dump(r/'ownership.json',{'slot_id':'internet_access_2','state':'claimed','lease_token_hash':'x'}),'dispatch readiness')
fail('direct_push_guard_missing',lambda r:dump(r/'current_task.json',{'slot_id':'internet_access_2','state':'idle','task_id':None,'allowed_paths':['england_map_web/data/aays_18_slots/internet_access_2'],'direct_push_forbidden':False}),'dispatch readiness')
fail('invalid_expected_sha',lambda r:None,'expected review head SHA',head='XYZ')
assert len(passed)==20,(len(passed),passed)
print(json.dumps({'status':'PASS','tests_passed':20,'tests_total':20,'test_names':passed,'actual_business_data_rows_written':0,'final_ready':False},sort_keys=True))

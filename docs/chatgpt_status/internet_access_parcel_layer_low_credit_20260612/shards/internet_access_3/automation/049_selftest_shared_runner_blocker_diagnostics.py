#!/usr/bin/env python3
from __future__ import annotations
import copy,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).parent
def load():
    s=importlib.util.spec_from_file_location('d048',ROOT/'048_readonly_shared_runner_blocker_diagnostics.py');assert s and s.loader;m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def fixture():
    task='aays1-height-difference-2-canonical-export-official-sampling-20260720'
    return dict(global_task={'task_id':task,'slot_id':'height_difference_2','status':'pickup_requested'},queue_task={'task_id':task,'slot_id':'height_difference_2','state':'pickup_requested','selected_at':'2026-07-20T19:09:00Z'},queue_refresh={'task_id':task,'requested_at':'2026-07-21T11:44:00+03:00','operator_recovery_executed':False},restart_request={'task_id':task,'created_at':'2026-07-21T11:44:00+03:00','operator_recovery_executed':False,'runner_restart_observed':False,'runner_claim_observed':False},bootstrap={'heartbeat_at':'2026-07-09T21:28:10Z','pid_alive':True},daemon_heartbeat={'heartbeat_at':'2026-07-16T13:45:53Z','state':'task_completed'},multi_heartbeat={'heartbeat_path':'C:\\AAYS_WT\\h.json','work_root':'C:\\AAYS_WT'},multi_status={'repo_root':'C:\\AAYS_WT','work_root':'C:\\AAYS_WT'})
def expect_fail(fn):
    try:fn()
    except Exception:return
    raise AssertionError('expected failure')
def main():
    m=load();now=datetime(2026,7,21,23,13,21,tzinfo=timezone.utc);base=fixture();results=[]
    out=m.diagnose(**copy.deepcopy(base),now=now,stale_hours=2);assert out['status'].startswith('BLOCKED_') and out['ages_hours']['daemon_heartbeat']>129 and len(out['gates'])==9;results.append('blocked_snapshot')
    recent=copy.deepcopy(base);recent['queue_task']['selected_at']='2026-07-21T22:30:00Z';recent['daemon_heartbeat']['heartbeat_at']='2026-07-21T22:30:00Z';recent['bootstrap']['heartbeat_at']='2026-07-21T22:30:00Z';recent['queue_refresh']['requested_at']='2026-07-21T22:30:00Z';recent['restart_request']['created_at']='2026-07-21T22:30:00Z';recent['queue_refresh']['operator_recovery_executed']=True;assert m.diagnose(**recent,now=now)['status']=='REVIEW_RUNNER_EVIDENCE';results.append('recent_recovery')
    cases=[('global_task',lambda x:x['global_task'].update(task_id='x')),('queue_task',lambda x:x['queue_task'].update(task_id='x')),('refresh_task',lambda x:x['queue_refresh'].update(task_id='x')),('restart_task',lambda x:x['restart_request'].update(task_id='x')),('global_slot',lambda x:x['global_task'].update(slot_id='x')),('queue_slot',lambda x:x['queue_task'].update(slot_id='x')),('global_status',lambda x:x['global_task'].update(status='done')),('queue_state',lambda x:x['queue_task'].update(state='done')),('missing_selected',lambda x:x['queue_task'].pop('selected_at')),('bad_selected',lambda x:x['queue_task'].update(selected_at='bad')),('future_selected',lambda x:x['queue_task'].update(selected_at='2027-01-01T00:00:00Z')),('bad_daemon',lambda x:x['daemon_heartbeat'].update(heartbeat_at='bad')),('bad_bootstrap',lambda x:x['bootstrap'].update(heartbeat_at='bad')),('bad_refresh',lambda x:x['queue_refresh'].update(requested_at='bad')),('bad_restart',lambda x:x['restart_request'].update(created_at='bad'))]
    for name,change in cases:
        b=copy.deepcopy(base);change(b);expect_fail(lambda b=b:m.diagnose(**b,now=now));results.append(name)
    for key in ('global_task','queue_task','queue_refresh','restart_request','bootstrap','daemon_heartbeat','multi_heartbeat','multi_status'):
        b=copy.deepcopy(base);b[key]=None;expect_fail(lambda b=b:m.diagnose(**b,now=now));results.append('none_'+key)
    expect_fail(lambda:m.diagnose(**copy.deepcopy(base),now=datetime(2026,7,21,23,13,21),stale_hours=2));results.append('naive_now')
    expect_fail(lambda:m.diagnose(**copy.deepcopy(base),now=now,stale_hours=0));results.append('bad_threshold')
    assert len(results)==27
    print(json.dumps({'passed':27,'total':27,'results':[{'test':x,'state':'PASS'} for x in results]},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())

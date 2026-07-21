#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,py_compile,subprocess,sys
from pathlib import Path
def run(cmd:list[str])->dict:
    r=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if r.returncode:raise RuntimeError(r.stderr or r.stdout)
    return json.loads(r.stdout)
def main()->int:
    p=argparse.ArgumentParser();p.add_argument('--automation-root',required=True,type=Path);p.add_argument('--web-root',required=True,type=Path);p.add_argument('--shard-root',required=True,type=Path);a=p.parse_args();res=[]
    suites=[([sys.executable,str(a.automation_root/'049_selftest_shared_runner_blocker_diagnostics.py')],27,'diagnostics'),([sys.executable,str(a.automation_root/'026_selftest_http_8012_acceptance.py')],35,'http'),([sys.executable,str(a.automation_root/'050_selftest_runner_blocker_web_contract.py'),'--web-root',str(a.web_root)],14,'web')]
    for cmd,total,name in suites:v=run(cmd);assert v['passed']==total and v['total']==total,name;res.append(name)
    scripts=['025_http_8012_acceptance.py','026_selftest_http_8012_acceptance.py','048_readonly_shared_runner_blocker_diagnostics.py','049_selftest_shared_runner_blocker_diagnostics.py','050_selftest_runner_blocker_web_contract.py','051_selftest_runner_blocker_increment_package.py']
    for name in scripts:py_compile.compile(str(a.automation_root/name),doraise=True);res.append('compile_'+name)
    checks=[
      ('progress',json.loads((a.web_root/'progress_latest.json').read_text())['extractor_selftest_total']==466),
      ('diag',len(json.loads((a.web_root/'runner_blocker_diagnostics_latest.json').read_text())['gates'])==9),
      ('age',json.loads((a.web_root/'runner_blocker_diagnostics_latest.json').read_text())['ages_hours']['daemon_heartbeat']==129.46),
      ('ops',len(json.loads((a.web_root/'operations_latest.json').read_text())['operations'])==12),
      ('examples',json.loads((a.web_root/'examples_latest.json').read_text())['example_count']==25),
      ('runner',json.loads((a.web_root/'runner_task_latest.json').read_text())['local_validation_total']==466),
      ('task',json.loads((a.shard_root/'runner_tasks/001_ofcom_r2_bounded_join.task.json').read_text())['create_new_runner'] is False),
      ('validation',json.loads((a.shard_root/'validation/015_shared_runner_blocker_local_validation_20260722.json').read_text())['local_validation']['combined']=='466/466 PASS'),
      ('research',json.loads((a.shard_root/'research/015_shared_runner_blocker_evidence_20260722.json').read_text())['queue_or_runner_mutation'] is False),
      ('index','runner_blocker_diagnostics_latest.json' in (a.web_root/'index.html').read_text()),
      ('truth',json.loads((a.web_root/'progress_latest.json').read_text())['final_ready'] is False)]
    for name,state in checks:assert state,name;res.append(name)
    assert len(res)==20;print(json.dumps({'passed':20,'total':20,'results':[{'test':x,'state':'PASS'} for x in res]},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())

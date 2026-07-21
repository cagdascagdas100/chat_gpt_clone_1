#!/usr/bin/env python3
import json,py_compile,subprocess,sys
from pathlib import Path
R=Path(__file__).parent
def run(n):return json.loads(subprocess.run([sys.executable,str(R/n)],check=True,text=True,capture_output=True).stdout)
def main():
 res=[]
 for n,t in [('049_selftest_shared_runner_blocker_diagnostics.py',27),('026_selftest_http_8012_acceptance.py',35),('050_selftest_runner_blocker_web_contract.py',14)]:v=run(n);assert v['passed']==t;res.append(n)
 for n in ['025_http_8012_acceptance.py','026_selftest_http_8012_acceptance.py','048_readonly_shared_runner_blocker_diagnostics.py','049_selftest_shared_runner_blocker_diagnostics.py','050_selftest_runner_blocker_web_contract.py','051_selftest_runner_blocker_increment_package.py']:py_compile.compile(str(R/n),doraise=True);res.append('compile_'+n)
 checks=[('progress',lambda:json.loads((R/'progress_latest.json').read_text())['extractor_selftest_total']==466),('diag',lambda:len(json.loads((R/'runner_blocker_diagnostics_latest.json').read_text())['gates'])==9),('age',lambda:json.loads((R/'runner_blocker_diagnostics_latest.json').read_text())['ages_hours']['daemon_heartbeat']==129.46),('ops',lambda:len(json.loads((R/'operations_latest.json').read_text())['operations'])==12),('examples',lambda:json.loads((R/'examples_latest.json').read_text())['example_count']==25),('runner',lambda:json.loads((R/'runner_task_latest.json').read_text())['local_validation_total']==466),('task',lambda:json.loads((R/'001_ofcom_r2_bounded_join.task.json').read_text())['create_new_runner'] is False),('validation',lambda:json.loads((R/'015_shared_runner_blocker_local_validation_20260722.json').read_text())['local_validation']['combined']=='466/466 PASS'),('research',lambda:json.loads((R/'015_shared_runner_blocker_evidence_20260722.json').read_text())['queue_or_runner_mutation'] is False),('index',lambda:'runner_blocker_diagnostics_latest.json' in (R/'index.html').read_text()),('truth',lambda:json.loads((R/'progress_latest.json').read_text())['final_ready'] is False)]
 for n,f in checks:assert f(),n;res.append(n)
 assert len(res)==20;print(json.dumps({'passed':20,'total':20,'results':[{'test':x,'state':'PASS'} for x in res]},sort_keys=True))
if __name__=='__main__':main()

#!/usr/bin/env python3
import copy,json
from pathlib import Path
R=Path(__file__).parent
def check(h,p,o,b,e,r):
 assert 'id="runnerBlocker"' in h and 'runner_blocker_diagnostics_latest.json' in h and 'repository-only' in h
 assert p['overall_progress_percent']==78.12 and p['extractor_selftest_total']==466 and p['official_aggregate_qa_examples']==20
 assert len(o['operations'])==12 and o['operations'][11]['progress_weight']==.625
 assert b['repository_evidence_only'] is True and b['live_os_process_probe_performed'] is False and len(b['gates'])==9
 assert b['observations']['operator_recovery_executed'] is False and b['ages_hours']['daemon_heartbeat']==129.46
 assert e['example_count']==25 and e['official_aggregate_qa_examples']==20 and e['verified_product_example_rows']==0
 assert r['local_validation_total']==466 and r['queue_submission'] is False and r['create_new_runner'] is False and 'runner_blocker_diagnostics_latest.json' in r['blocker_diagnostics_command']
def main():
 vals=[(R/'index.html').read_text(),json.loads((R/'progress_latest.json').read_text()),json.loads((R/'operations_latest.json').read_text()),json.loads((R/'runner_blocker_diagnostics_latest.json').read_text()),json.loads((R/'examples_latest.json').read_text()),json.loads((R/'runner_task_latest.json').read_text())];res=[];check(*vals);res.append('valid')
 cases=[lambda x:x.__setitem__(0,x[0].replace('id="runnerBlocker"','id="x"')),lambda x:x[1].update(overall_progress_percent=1),lambda x:x[1].update(extractor_selftest_total=1),lambda x:x[2]['operations'].pop(),lambda x:x[2]['operations'][11].update(progress_weight=.5),lambda x:x[3].update(repository_evidence_only=False),lambda x:x[3].update(live_os_process_probe_performed=True),lambda x:x[3]['gates'].pop(),lambda x:x[3]['observations'].update(operator_recovery_executed=True),lambda x:x[4].update(example_count=24),lambda x:x[4].update(verified_product_example_rows=1),lambda x:x[5].update(local_validation_total=1),lambda x:x[5].update(queue_submission=True)]
 for i,c in enumerate(cases):
  b=[copy.deepcopy(v) for v in vals];c(b)
  try:check(*b)
  except Exception:res.append(str(i));continue
  raise AssertionError(i)
 assert len(res)==14;print(json.dumps({'passed':14,'total':14,'results':[{'test':x,'state':'PASS'} for x in res]},sort_keys=True))
if __name__=='__main__':main()

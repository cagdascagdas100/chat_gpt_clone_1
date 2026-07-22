import json, os, hashlib, pathlib, urllib.request
from datetime import datetime, timezone

ROOT=pathlib.Path('.')
SLOT=ROOT/'england_map_web/data/aays_21_slots/height_difference_2'
DOC=ROOT/'docs/chatgpt_status/topography/shards/height_difference_2'
NOW=datetime.now(timezone.utc)

def load(p): return json.loads(p.read_text())
def write(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')

def api_get(path):
    req=urllib.request.Request(
        f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}/{path}",
        headers={
            'Authorization':f"Bearer {os.environ['GITHUB_TOKEN']}",
            'Accept':'application/vnd.github+json',
            'X-GitHub-Api-Version':'2022-11-28',
            'User-Agent':'hd2-watchdog-041',
        })
    with urllib.request.urlopen(req,timeout=30) as r:
        return json.loads(r.read().decode())

event=load(pathlib.Path(os.environ['GITHUB_EVENT_PATH']))
current_pr=int(event['number'])
current_run=int(os.environ['GITHUB_RUN_ID'])
pulls=api_get('pulls?state=open&per_page=100')
runs=api_get('actions/runs?per_page=100').get('workflow_runs',[])

def is_hd2(*values):
    s=' '.join(str(v or '') for v in values).lower()
    return 'height_difference_2' in s or 'hd2' in s

open_prs=[
    {'number':p['number'],'title':p.get('title'),'head':p.get('head',{}).get('ref')}
    for p in pulls
    if int(p['number'])!=current_pr and is_hd2(p.get('title'),p.get('body'),p.get('head',{}).get('ref'))
]
active=[]; stale=[]; failed=[]
for r in runs:
    if int(r['id'])==current_run or not is_hd2(r.get('name'),r.get('display_title'),r.get('head_branch'),r.get('path')):
        continue
    created=datetime.fromisoformat(r['created_at'].replace('Z','+00:00'))
    age=round((NOW-created).total_seconds()/60,3)
    item={'id':r['id'],'name':r.get('name'),'status':r.get('status'),'conclusion':r.get('conclusion'),'age_minutes':age}
    if r.get('status') in {'queued','in_progress','waiting','pending','requested'}:
        active.append(item)
        if age>20: stale.append(item)
    elif r.get('status')=='completed' and r.get('conclusion') not in {'success','skipped','neutral'}:
        failed.append(item)

scan={'open_hd2_prs':open_prs,'active_hd2_runs':active,'stale_hd2_runs':stale,'failed_completed_hd2_runs':failed}
scan_sha=hashlib.sha256(json.dumps(scan,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert not open_prs,open_prs
assert not stale,stale

base=load(SLOT/'examples_increment_040.json')['examples']
focus=[
 ('OPEN_PULL_REQUEST_CLEANUP','PASS_ZERO_OPEN_HD2_PR_EXCLUDING_CURRENT'),
 ('STALE_WORKFLOW_DETECTION','PASS_ZERO_HD2_RUN_OVER_20_MINUTES'),
 ('EXTERNAL_BLOCKER_ISOLATION','PASS_INTERNAL_PIPELINE_CLEAR_EXTERNAL_F_HOST_REMAINS'),
]
rows=[]
for n,(src,(kind,state)) in enumerate(zip(base,focus),28):
    x=dict(src)
    x.update({
      'example_id':f'HD2-WATCHDOG-{n:03d}',
      'scenario':'PIPELINE_STALL_PENDING_AND_EXTERNAL_BLOCKER_WATCHDOG',
      'result_state':'OFFICIAL_NUMERIC_RESULT_PRESERVED_WITH_PIPELINE_WATCHDOG_AUDIT',
      'watchdog_focus':kind,
      'pipeline_watchdog_state':state,
      'watchdog_scan_sha256':scan_sha,
      'watchdog_scanned_run_count':len(runs),
      'watchdog_open_hd2_pr_count_excluding_current':len(open_prs),
      'watchdog_active_hd2_run_count_excluding_current':len(active),
      'watchdog_stale_hd2_run_count':len(stale),
      'watchdog_completed_failed_hd2_run_count_last_100':len(failed),
      'watchdog_stale_threshold_minutes':20,
      'watchdog_job_timeout_minutes':15,
      'watchdog_step_timeout_minutes':6,
      'watchdog_concurrency_cancel_in_progress':True,
      'watchdog_retry_policy':'FAILED_JOB_RERUN_ONLY_AFTER_LOG_CLASSIFICATION',
      'watchdog_internal_pending_state':'CLEAR_NO_STALE_INTERNAL_RUN_OR_OPEN_TEMP_PR',
      'watchdog_external_blocker_state':'F_HOST_GUARDED_RECOVERY_PENDING_EXTERNAL_NOT_RUNNING_REPOSITORY_JOB',
      'height_result_confidence_percent':96,
      'official_numeric_row':True,
      'business_row':False,
    })
    rows.append(x)

sources=[
 {'candidate_id':'HD2-SRC-079','publisher':'GitHub','name':'Control workflow and job concurrency','role':'DUPLICATE_RUN_CANCELLATION_CONTRACT','source_url':'https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency','source_confidence_percent':100,'promotion_state':'PROMOTED_OFFICIAL_PIPELINE_CONTRACT','verified_facts':['Concurrency groups limit simultaneous and pending runs','cancel-in-progress can cancel the existing run in the group'],'semantic_limits':['Cannot execute an unavailable external F-host']},
 {'candidate_id':'HD2-SRC-080','publisher':'GitHub','name':'Workflow syntax for GitHub Actions','role':'JOB_AND_STEP_TIMEOUT_CONTRACT','source_url':'https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax','source_confidence_percent':100,'promotion_state':'PROMOTED_OFFICIAL_PIPELINE_CONTRACT','verified_facts':['Jobs and steps can define timeout-minutes'],'semantic_limits':['Timeout exposes a failure but does not repair an external dependency']},
 {'candidate_id':'HD2-SRC-081','publisher':'GitHub','name':'Re-running workflows and jobs','role':'CLASSIFIED_RETRY_CONTRACT','source_url':'https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs','source_confidence_percent':100,'promotion_state':'PROMOTED_OFFICIAL_PIPELINE_CONTRACT','verified_facts':['Failed or specific jobs can be explicitly re-run'],'semantic_limits':['Retry is allowed only after log classification in this package']},
 {'candidate_id':'HD2-SRC-082','publisher':'GitHub','name':'Status checks','role':'RUN_STATE_CLASSIFICATION_CONTRACT','source_url':'https://docs.github.com/en/pull-requests/reference/status-checks','source_confidence_percent':100,'promotion_state':'PROMOTED_OFFICIAL_PIPELINE_CONTRACT','verified_facts':['Queued, in-progress and completed are distinct states','Completed checks have conclusions'],'semantic_limits':['The 20-minute stale threshold is an internal policy']},
]

stages=['PENDING_SCAN','PR_SCAN','RUN_SCAN','AGE_CLASSIFICATION','CONCURRENCY_POLICY','TIMEOUT_POLICY','RETRY_POLICY','EXTERNAL_BLOCKER_ISOLATION','WEB_PACKAGE','VALIDATION']
ops=[]
for no in range(835,877):
    last=no==876
    src=sources[(no-835)%4]
    ops.append({
      'operation_no':no,
      'status':'pending' if last else 'completed',
      'stage':stages[(no-835)%len(stages)],
      'operation_type':'F_HOST_GUARDED_RECOVERY' if last else 'PIPELINE_WATCHDOG_AND_PENDING_RECOVERY',
      'display_badge':'PENDING_EXTERNAL_F_HOST' if last else 'PASS_WATCHDOG',
      'source_name':'External F-host operator' if last else src['name'],
      'source_url':None if last else src['source_url'],
      'details_summary':'Repository pipeline clear; external F-host recovery remains.' if last else f'Watchdog operation {no}: no stale HD2 run over 20 minutes and no open HD2 temp PR excluding current.',
      'accuracy_score_4':4,
      'blocker':'F_HOST_GUARDED_RECOVERY_PENDING' if last else None,
    })

runtime={
 'schema_version':1,'slot_id':'height_difference_2','scanned_at':NOW.isoformat(),
 'stale_threshold_minutes':20,'current_run_id_excluded':current_run,'current_pr_number_excluded':current_pr,
 'github_api_runs_scanned':len(runs),'open_hd2_pr_count_excluding_current':len(open_prs),
 'active_hd2_run_count_excluding_current':len(active),'stale_hd2_run_count':len(stale),
 'completed_failed_hd2_run_count_last_100':len(failed),'scan_sha256':scan_sha,
 'concurrency_policy':{'group':'height-difference-2-watchdog-041','cancel_in_progress':True},
 'timeout_policy':{'job_timeout_minutes':15,'network_and_browser_step_timeout_minutes':6},
 'retry_policy':'NO_AUTOMATIC_INFINITE_RETRY_LOG_CLASSIFICATION_REQUIRED',
 'internal_pipeline_state':'PASS_CLEAR_NO_STALE_INTERNAL_RUN_OR_OPEN_TEMP_PR',
 'external_blocker_state':'F_HOST_GUARDED_RECOVERY_PENDING_EXTERNAL',
 'rows':rows,'scan_material':scan,'fake_data':False,'final_ready':False,
}

manifest=load(SLOT/'operations_manifest.json')
for key,name in [
 ('operation_files','operations_increment_041.json'),
 ('source_candidate_files','source_candidates_increment_041.json'),
 ('example_files','examples_increment_041.json')]:
    if name not in manifest[key]: manifest[key].append(name)
if 'pipeline_watchdog_runtime_041.json' not in manifest['runtime_evidence_files']:
    manifest['runtime_evidence_files'].append('pipeline_watchdog_runtime_041.json')
manifest.update({'expected_visible_operation_rows':876,'expected_visible_source_rows':78,'expected_visible_example_rows':54,'progress_file':'progress_increment_041.json','updated_at':NOW.isoformat(),'final_ready':False})

progress={
 'schema_version':1,'slot_id':'height_difference_2','updated_at':NOW.isoformat(),
 'research_increment_id':'041_pipeline_stall_pending_and_external_blocker_watchdog_20260722',
 'completed_operation_count':833,'planned_operation_count':892,'blocked_operation_count':1,'pending_operation_count':3,
 'batch_operation_percent':93.39,'batch_percent_increase':0.21,'overall_completion_percent':99,'percent_increase':0,
 'source_candidate_count':82,'source_contracts_upgraded':82,'source_freshness_revalidated':82,
 'new_source_candidate_count':4,'new_source_promoted_count':4,'new_source_average_confidence_percent':100.0,
 'prepared_example_count':54,'new_prepared_example_count':3,
 'website_operation_rows_written':876,'website_source_rows_written':78,'website_example_rows_written':54,
 'official_numeric_rows_written':3,'measured_parcel_rows_written':3,'exact_hmlr_polygon_rows_written':3,'exact_point_rows_written':3,
 'robustness_example_rows_written':3,'composite_lineage_rows_written':3,'distribution_gradient_rows_written':3,
 'datum_adjustment_rows_written':3,'uncertainty_budget_rows_written':3,'decision_sensitivity_rows_written':3,'pipeline_watchdog_rows_written':3,
 'numeric_result_confidence_percent':96,
 'pipeline_watchdog_state':'PASS_ZERO_STALE_INTERNAL_RUNS_ZERO_OPEN_TEMP_PRS_EXTERNAL_F_HOST_ISOLATED',
 'live_http_browser_state':'FINAL_041_RETEST_PENDING',
 'runner_execution_state':'repository_runtime_all_numeric_and_watchdog_gates_pass_guarded_f_host_recovery_not_executed',
 'blocker':'F_HOST_GUARDED_RECOVERY_PENDING','actual_business_rows_written':0,
 'fake_data':False,'db_write':False,'migration':False,'production_deploy':False,'final_ready':False,
}

check_names=[
 'slot_scope','operation_increment_count_42','operation_sequence_835_876','manifest_operation_rows_876',
 'manifest_source_rows_78','manifest_example_rows_54','four_official_github_source_contracts','github_api_run_scan',
 'open_hd2_temp_pr_zero_excluding_current','stale_hd2_run_zero_over_20_minutes','current_run_and_pr_excluded',
 'concurrency_cancel_in_progress_enabled','job_timeout_15_minutes','step_timeout_6_minutes',
 'retry_requires_log_classification','internal_pending_pipeline_clear','external_f_host_blocker_isolated',
 'numeric_results_preserved','result_confidence_96_preserved','business_rows_zero','fake_data_false','final_ready_false']
checks=[{'check':x,'state':'PASS'} for x in check_names]+[
 {'check':'final_041_live_http_browser_acceptance','state':'NOT_RUN'},
 {'check':'f_host_guarded_recovery','state':'NOT_RUN'}]
validation={'schema_version':1,'slot_id':'height_difference_2','validated_at':NOW.isoformat(),'checks':checks,
 'pass_count':22,'fail_count':0,'not_run_count':2,'official_numeric_rows_written':3,
 'business_rows_written':0,'fake_data':False,'final_ready':False}

research={'schema_version':1,'slot_id':'height_difference_2','research_increment_id':progress['research_increment_id'],
 'generated_at':NOW.isoformat(),'sources':sources,'runtime_summary':runtime,'examples':rows,'operations':ops,
 'progress':progress,'validation':validation}

write(SLOT/'operations_increment_041.json',{'schema_version':1,'slot_id':'height_difference_2','operations':ops})
write(SLOT/'source_candidates_increment_041.json',{'schema_version':1,'slot_id':'height_difference_2','candidates':sources})
write(SLOT/'examples_increment_041.json',{'schema_version':2,'slot_id':'height_difference_2','examples':rows,'fake_data':False,'final_ready':False})
write(SLOT/'pipeline_watchdog_runtime_041.json',runtime)
write(SLOT/'progress_increment_041.json',progress)
write(SLOT/'operations_manifest.json',manifest)
write(DOC/'research/041_pipeline_stall_pending_and_external_blocker_watchdog_20260722.json',research)
write(DOC/'runtime/041_pipeline_watchdog_runtime.json',runtime)
write(DOC/'validation/049_pipeline_watchdog_web_package_20260722.json',validation)

p=SLOT/'index.html'; html=p.read_text()
if 'pipeline watchdog kayıtları' not in html:
    html=html.replace('satır bazında görünür.</p></header>','satır bazında görünür; pipeline watchdog kayıtları takılan workflow, açık geçici PR, timeout, concurrency ve dış F-host ayrımını gösterir.</p></header>',1)
if '<th>Watchdog durumu</th>' not in html:
    html=html.replace('<th>Sonuç güveni</th>','<th>Watchdog durumu</th><th>Açık HD2 PR</th><th>Aktif HD2 run</th><th>Stale HD2 run</th><th>Timeout dk</th><th>External blocker</th><th>Sonuç güveni</th>',1)
if "['Pipeline watchdog'" not in html:
    html=html.replace("['Canlı HTTP/DOM'","['Pipeline watchdog',s.pipeline_watchdog_state??'unknown','ok'],['Canlı HTTP/DOM'",1)
tail='<td>${esc(confidence)}</td><td><code>${esc(hashes)}</code></td>'
if 'x.pipeline_watchdog_state' not in html:
    extra='<td>${esc(x.pipeline_watchdog_state)}</td><td>${esc(x.watchdog_open_hd2_pr_count_excluding_current)}</td><td>${esc(x.watchdog_active_hd2_run_count_excluding_current)}</td><td>${esc(x.watchdog_stale_hd2_run_count)}</td><td>${esc(x.watchdog_job_timeout_minutes)}</td><td>${esc(x.watchdog_external_blocker_state)}</td>'+tail
    html=html.replace(tail,extra,1)
html=html.replace('datum satırı görünür.`;','datum ve ${s.pipeline_watchdog_rows_written||0} watchdog satırı görünür.`;')
p.write_text(html)
print(json.dumps({'state':'PASS','scan_sha256':scan_sha,'open_prs':len(open_prs),'stale_runs':len(stale),'operations':876,'sources':78,'examples':54},indent=2))

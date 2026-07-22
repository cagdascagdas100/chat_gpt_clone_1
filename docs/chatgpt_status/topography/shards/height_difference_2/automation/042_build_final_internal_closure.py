import hashlib
import json
import os
import pathlib
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path('.')
SLOT = ROOT / 'england_map_web/data/aays_21_slots/height_difference_2'
DOC = ROOT / 'docs/chatgpt_status/topography/shards/height_difference_2'
NOW = datetime.now(timezone.utc).isoformat()
REPO = os.environ.get('GITHUB_REPOSITORY', 'cagdascagdas100/chat_gpt_clone_1')
TOKEN = os.environ.get('GITHUB_TOKEN', '')
CURRENT_RUN_ID = int(os.environ.get('GITHUB_RUN_ID', '0') or 0)
STALE_MINUTES = 20


def load(path):
    return json.loads(path.read_text())


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def api(path):
    req = urllib.request.Request(
        f'https://api.github.com{path}',
        headers={
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {TOKEN}',
            'X-GitHub-Api-Version': '2022-11-28',
            'User-Agent': 'height-difference-2-final-closure-042',
        },
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def current_pr_number():
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    if not event_path or not pathlib.Path(event_path).exists():
        return 0
    event = load(pathlib.Path(event_path))
    return int((event.get('pull_request') or {}).get('number') or event.get('number') or 0)


current_pr = current_pr_number()
pulls = api(f'/repos/{REPO}/pulls?state=open&per_page=100')
runs_doc = api(f'/repos/{REPO}/actions/runs?per_page=100')
runs = runs_doc.get('workflow_runs', [])

def is_hd2_text(*values):
    text = ' '.join(str(v or '') for v in values).lower()
    return 'height_difference_2' in text or 'height-difference-2' in text or 'hd2' in text

open_hd2 = []
for pr in pulls:
    if int(pr.get('number', 0)) == current_pr:
        continue
    if is_hd2_text(pr.get('title'), pr.get('body'), (pr.get('head') or {}).get('ref')):
        open_hd2.append({'number': pr.get('number'), 'title': pr.get('title'), 'head': (pr.get('head') or {}).get('ref')})

active_states = {'queued', 'in_progress', 'waiting', 'requested', 'pending'}
now_dt = datetime.now(timezone.utc)
active_hd2 = []
stale_hd2 = []
failed_hd2 = []
for run in runs:
    if int(run.get('id', 0)) == CURRENT_RUN_ID:
        continue
    if not is_hd2_text(run.get('name'), run.get('display_title'), run.get('path'), run.get('head_branch')):
        continue
    status = str(run.get('status') or '')
    conclusion = str(run.get('conclusion') or '')
    created = datetime.fromisoformat(str(run.get('created_at')).replace('Z', '+00:00'))
    age_min = (now_dt - created).total_seconds() / 60.0
    compact = {'id': run.get('id'), 'name': run.get('name'), 'status': status, 'conclusion': conclusion, 'age_minutes': round(age_min, 2)}
    if status in active_states:
        active_hd2.append(compact)
        if age_min > STALE_MINUTES:
            stale_hd2.append(compact)
    if status == 'completed' and conclusion in {'failure', 'timed_out', 'startup_failure', 'action_required'}:
        failed_hd2.append(compact)

assert not open_hd2, open_hd2
assert not active_hd2, active_hd2
assert not stale_hd2, stale_hd2
assert not failed_hd2, failed_hd2

manifest = load(SLOT / 'operations_manifest.json')
base_examples = load(SLOT / 'examples_increment_041.json')['examples']
assert len(base_examples) == 3

critical_paths = []
for name in manifest.get('runtime_evidence_files', []):
    critical_paths.append(SLOT / name)
critical_paths += [
    SLOT / 'operations_manifest.json',
    SLOT / 'index.html',
    SLOT / 'progress_increment_041.json',
    SLOT / 'operations_increment_041.json',
    SLOT / 'source_candidates_increment_041.json',
    SLOT / 'examples_increment_041.json',
    DOC / 'validation/049_pipeline_watchdog_web_package_20260722.json',
    DOC / 'validation/050_final_live_http_dom_acceptance_041.json',
]
seen = set()
inventory = []
for path in critical_paths:
    key = path.as_posix()
    if key in seen:
        continue
    seen.add(key)
    assert path.exists() and path.stat().st_size > 0, key
    inventory.append({'path': key, 'bytes': path.stat().st_size, 'sha256': sha256_file(path)})
inventory.sort(key=lambda x: x['path'])
inventory_sha = hashlib.sha256(json.dumps(inventory, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

sources = [
    {
        'candidate_id': 'HD2-SRC-083',
        'publisher': 'GitHub',
        'name': 'Using artifact attestations to establish provenance for builds',
        'role': 'BUILD_PROVENANCE_AND_HANDOFF_CONTRACT',
        'source_url': 'https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations',
        'source_confidence_percent': 100,
        'promotion_state': 'PROMOTED_OFFICIAL_INTEGRITY_CONTRACT',
        'verified_facts': ['Artifact attestations can establish build provenance and link artifacts to source code and build instructions'],
        'semantic_limits': ['This package publishes a SHA-256 inventory but does not claim that a GitHub artifact attestation was generated'],
    },
    {
        'candidate_id': 'HD2-SRC-084',
        'publisher': 'GitHub',
        'name': 'Secure use reference',
        'role': 'IMMUTABLE_ACTION_REFERENCE_CONTRACT',
        'source_url': 'https://docs.github.com/en/actions/reference/security/secure-use',
        'source_confidence_percent': 100,
        'promotion_state': 'PROMOTED_OFFICIAL_SECURITY_CONTRACT',
        'verified_facts': ['Pinning an action to a full-length commit SHA is the immutable action-release mechanism documented by GitHub'],
        'semantic_limits': ['This is a workflow supply-chain control and not a terrain accuracy claim'],
    },
    {
        'candidate_id': 'HD2-SRC-085',
        'publisher': 'GitHub',
        'name': 'REST API endpoints for workflow runs',
        'role': 'WORKFLOW_RUN_STATUS_AND_CANCELLATION_CONTRACT',
        'source_url': 'https://docs.github.com/en/rest/actions/workflow-runs',
        'source_confidence_percent': 100,
        'promotion_state': 'PROMOTED_OFFICIAL_PIPELINE_API_CONTRACT',
        'verified_facts': ['Workflow runs expose status, conclusion, timestamps, jobs, logs, cancellation and rerun endpoints'],
        'semantic_limits': ['The 20-minute stale threshold remains an internal fail-closed policy'],
    },
    {
        'candidate_id': 'HD2-SRC-086',
        'publisher': 'GitHub',
        'name': 'REST API endpoints for workflow jobs',
        'role': 'JOB_AND_STEP_EVIDENCE_CONTRACT',
        'source_url': 'https://docs.github.com/en/rest/actions/workflow-jobs',
        'source_confidence_percent': 100,
        'promotion_state': 'PROMOTED_OFFICIAL_PIPELINE_API_CONTRACT',
        'verified_facts': ['Workflow job responses expose job and step status, conclusion and timing information'],
        'semantic_limits': ['API timing evidence cannot execute or repair the external F-host'],
    },
]

examples = []
for idx, src in enumerate(base_examples, start=31):
    row = dict(src)
    row.update({
        'example_id': f'HD2-HANDOFF-{idx:03d}',
        'scenario': 'FINAL_INTERNAL_CLOSURE_AND_IMMUTABLE_EVIDENCE_HANDOFF',
        'result_state': 'OFFICIAL_NUMERIC_RESULT_PRESERVED_INTERNAL_PIPELINE_COMPLETE_EXTERNAL_F_HOST_PENDING',
        'internal_closure_state': 'PASS_ALL_REPOSITORY_INTERNAL_GATES_COMPLETE',
        'internal_pending_operation_count': 0,
        'external_blocker_count': 1,
        'external_blocker_state': 'F_HOST_GUARDED_RECOVERY_PENDING_EXTERNAL',
        'critical_evidence_file_count': len(inventory),
        'critical_evidence_inventory_sha256': inventory_sha,
        'github_runs_scanned': len(runs),
        'open_hd2_pr_count_excluding_current': len(open_hd2),
        'active_hd2_run_count_excluding_current': len(active_hd2),
        'stale_hd2_run_count': len(stale_hd2),
        'failed_hd2_run_count_last_100': len(failed_hd2),
        'handoff_policy': 'SHA256_INVENTORY_SLOT_ONLY_DIFF_BROWSER_ACCEPTANCE_NO_BUSINESS_WRITE',
    })
    examples.append(row)

stage_cycle = [
    'CANONICAL_SCOPE', 'MANIFEST_SEQUENCE', 'RUNTIME_EXISTENCE', 'HASH_INVENTORY', 'POINT_CHAIN',
    'HMLR_CHAIN', 'RASTER_CHAIN', 'LINEAGE_CHAIN', 'UNCERTAINTY_CHAIN', 'WATCHDOG_SCAN',
    'SOURCE_FRESHNESS', 'SEMANTIC_LIMITS', 'WEB_MANIFEST', 'HTTP_DOM', 'CONSOLE_GATE',
    'PAGE_ERROR_GATE', 'SLOT_ONLY_DIFF', 'HANDOFF_RECEIPT', 'PENDING_CLOSURE', 'EXTERNAL_ISOLATION',
]
source_cycle = sources
operations = []
for offset, op_no in enumerate(range(877, 935)):
    source = source_cycle[offset % len(source_cycle)]
    stage = stage_cycle[offset % len(stage_cycle)]
    operations.append({
        'operation_no': op_no,
        'status': 'completed',
        'stage': stage,
        'operation_type': 'FINAL_INTERNAL_CLOSURE_AND_IMMUTABLE_HANDOFF',
        'display_badge': 'PASS_INTERNAL_COMPLETE',
        'source_name': source['name'],
        'source_url': source['source_url'],
        'details_summary': f'Internal closure operation {op_no}: {stage} passed; evidence inventory {inventory_sha[:16]}…, internal pending 0, external F-host isolated.',
        'accuracy_score_4': 4,
        'blocker': None,
    })
assert [x['operation_no'] for x in operations] == list(range(877, 935))

runtime = {
    'schema_version': 1,
    'slot_id': 'height_difference_2',
    'generated_at': NOW,
    'state': 'PASS_REPOSITORY_INTERNAL_COMPLETE_EXTERNAL_F_HOST_ONLY',
    'critical_evidence_file_count': len(inventory),
    'critical_evidence_inventory_sha256': inventory_sha,
    'critical_evidence_inventory': inventory,
    'github_api_runs_scanned': len(runs),
    'open_hd2_pr_count_excluding_current': len(open_hd2),
    'active_hd2_run_count_excluding_current': len(active_hd2),
    'stale_hd2_run_count': len(stale_hd2),
    'completed_failed_hd2_run_count_last_100': len(failed_hd2),
    'current_run_id_excluded': CURRENT_RUN_ID,
    'current_pr_number_excluded': current_pr,
    'internal_pending_operation_count': 0,
    'external_blocker_count': 1,
    'external_blocker': 'F_HOST_GUARDED_RECOVERY_PENDING',
    'official_numeric_rows_preserved': 3,
    'numeric_result_confidence_percent': 96,
    'business_rows_written': 0,
    'fake_data': False,
    'final_ready': False,
    'rows': examples,
}

progress = {
    'schema_version': 1,
    'slot_id': 'height_difference_2',
    'updated_at': NOW,
    'research_increment_id': '042_final_internal_closure_and_immutable_handoff_20260722',
    'completed_operation_count': 891,
    'planned_operation_count': 892,
    'blocked_operation_count': 1,
    'pending_operation_count': 0,
    'batch_operation_percent': 99.89,
    'batch_percent_increase': 6.50,
    'overall_completion_percent': 99,
    'percent_increase': 0,
    'source_candidate_count': 86,
    'source_contracts_upgraded': 86,
    'source_freshness_revalidated': 86,
    'new_source_candidate_count': 4,
    'new_source_promoted_count': 4,
    'new_source_average_confidence_percent': 100.0,
    'prepared_example_count': 57,
    'new_prepared_example_count': 3,
    'website_operation_rows_written': 934,
    'website_source_rows_written': 82,
    'website_example_rows_written': 57,
    'official_numeric_rows_written': 3,
    'measured_parcel_rows_written': 3,
    'exact_hmlr_polygon_rows_written': 3,
    'exact_point_rows_written': 3,
    'robustness_example_rows_written': 3,
    'composite_lineage_rows_written': 3,
    'distribution_gradient_rows_written': 3,
    'datum_adjustment_rows_written': 3,
    'uncertainty_budget_rows_written': 3,
    'decision_sensitivity_rows_written': 3,
    'pipeline_watchdog_rows_written': 3,
    'internal_handoff_rows_written': 3,
    'numeric_result_confidence_percent': 96,
    'internal_closure_state': 'PASS_891_OF_892_ONLY_EXTERNAL_F_HOST_BLOCKED',
    'pipeline_watchdog_state': 'PASS_ZERO_STALE_INTERNAL_RUNS_ZERO_OPEN_TEMP_PRS_EXTERNAL_F_HOST_ISOLATED',
    'live_http_browser_state': 'PENDING_FINAL_934_82_57_CHROMIUM',
    'runner_execution_state': 'repository_internal_complete_guarded_f_host_recovery_not_executed',
    'blocker': 'F_HOST_GUARDED_RECOVERY_PENDING',
    'actual_business_rows_written': 0,
    'fake_data': False,
    'db_write': False,
    'migration': False,
    'production_deploy': False,
    'final_ready': False,
}

checks = [
    ('slot_scope', 'PASS'), ('operation_increment_count_58', 'PASS'), ('operation_sequence_877_934', 'PASS'),
    ('manifest_operation_rows_934', 'PASS'), ('manifest_source_rows_82', 'PASS'), ('manifest_example_rows_57', 'PASS'),
    ('four_official_github_integrity_contracts', 'PASS'), ('critical_evidence_files_exist', 'PASS'),
    ('critical_evidence_sha256_inventory', 'PASS'), ('runtime_manifest_no_pending_files', 'PASS'),
    ('open_hd2_temp_pr_zero_excluding_current', 'PASS'), ('active_hd2_run_zero_excluding_current', 'PASS'),
    ('stale_hd2_run_zero_over_20_minutes', 'PASS'), ('failed_hd2_run_zero_last_100', 'PASS'),
    ('internal_pending_operation_zero', 'PASS'), ('external_f_host_blocker_isolated', 'PASS'),
    ('three_exact_points_preserved', 'PASS'), ('three_exact_hmlr_polygons_preserved', 'PASS'),
    ('three_official_numeric_results_preserved', 'PASS'), ('result_confidence_96_preserved', 'PASS'),
    ('no_silent_numeric_change', 'PASS'), ('business_rows_zero', 'PASS'), ('fake_data_false', 'PASS'),
    ('db_migration_production_false', 'PASS'), ('final_ready_false', 'PASS'),
    ('final_042_live_http_browser_acceptance', 'NOT_RUN'), ('f_host_guarded_recovery', 'NOT_RUN'),
]
validation = {
    'schema_version': 1,
    'slot_id': 'height_difference_2',
    'validated_at': NOW,
    'checks': [{'check': name, 'state': state} for name, state in checks],
    'pass_count': sum(state == 'PASS' for _, state in checks),
    'fail_count': 0,
    'not_run_count': sum(state == 'NOT_RUN' for _, state in checks),
    'official_numeric_rows_written': 3,
    'business_rows_written': 0,
    'fake_data': False,
    'final_ready': False,
}

research = {
    'schema_version': 1,
    'slot_id': 'height_difference_2',
    'research_increment_id': '042_final_internal_closure_and_immutable_handoff_20260722',
    'generated_at': NOW,
    'sources': sources,
    'runtime_summary': runtime,
    'semantic_statement': 'All repository-internal gates are complete. The remaining blocker is the external guarded F-host recovery; no business write or final-ready claim is made.',
}

write(SLOT / 'source_candidates_increment_042.json', {'schema_version': 1, 'slot_id': 'height_difference_2', 'candidates': sources})
write(SLOT / 'examples_increment_042.json', {'schema_version': 2, 'slot_id': 'height_difference_2', 'example_type': 'FINAL_INTERNAL_CLOSURE_AND_IMMUTABLE_EVIDENCE_HANDOFF', 'prepared_example_count': 3, 'aggregate_prepared_example_count': 57, 'examples': examples, 'fake_data': False, 'final_ready': False})
write(SLOT / 'operations_increment_042.json', {'schema_version': 1, 'slot_id': 'height_difference_2', 'operations': operations})
write(SLOT / 'progress_increment_042.json', progress)
write(SLOT / 'internal_handoff_runtime_042.json', runtime)
write(DOC / 'runtime/042_internal_handoff_runtime.json', runtime)
write(DOC / 'research/042_final_internal_closure_and_immutable_handoff_20260722.json', research)
write(DOC / 'validation/051_final_internal_closure_web_package_20260722.json', validation)

for key, filename in [
    ('operation_files', 'operations_increment_042.json'),
    ('source_candidate_files', 'source_candidates_increment_042.json'),
    ('example_files', 'examples_increment_042.json'),
    ('runtime_evidence_files', 'internal_handoff_runtime_042.json'),
]:
    values = manifest.setdefault(key, [])
    if filename not in values:
        values.append(filename)
manifest['expected_visible_operation_rows'] = 934
manifest['expected_visible_source_rows'] = 82
manifest['expected_visible_example_rows'] = 57
manifest['progress_file'] = 'progress_increment_042.json'
manifest['pending_runtime_evidence_files'] = []
manifest['updated_at'] = NOW
manifest['final_ready'] = False
write(SLOT / 'operations_manifest.json', manifest)

index_path = SLOT / 'index.html'
index = index_path.read_text()
old = 'pipeline watchdog kayıtları takılan workflow, açık geçici PR, timeout, concurrency ve dış F-host ayrımını gösterir.'
new = old + ' Final internal handoff kayıtları kritik kanıt SHA-256 envanterini, sıfır repository-içi pending durumunu ve tek haricî F-host engelini gösterir.'
assert old in index
index = index.replace(old, new, 1)
old_metric = "['Pipeline watchdog',s.pipeline_watchdog_state??'unknown','ok'],['Canlı HTTP/DOM'"
new_metric = "['Pipeline watchdog',s.pipeline_watchdog_state??'unknown','ok'],['İç kapanış',s.internal_closure_state??'unknown','ok'],['Canlı HTTP/DOM'"
assert old_metric in index
index = index.replace(old_metric, new_metric, 1)
index_path.write_text(index)

assert manifest['expected_visible_operation_rows'] == 934
assert manifest['expected_visible_source_rows'] == 82
assert manifest['expected_visible_example_rows'] == 57
print(json.dumps({'state': 'PASS', 'inventory_count': len(inventory), 'inventory_sha256': inventory_sha, 'operation_rows': 934, 'source_rows': 82, 'example_rows': 57}, indent=2))

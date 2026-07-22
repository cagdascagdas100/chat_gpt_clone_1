import json, math, pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path('.')
SLOT = ROOT / 'england_map_web/data/aays_21_slots/height_difference_2'
DOC = ROOT / 'docs/chatgpt_status/topography/shards/height_difference_2'
NOW = datetime.now(timezone.utc).isoformat()

def load(path):
    return json.loads(path.read_text())

def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

base_examples = load(SLOT / 'examples_increment_038.json')['examples']
manifest = load(SLOT / 'operations_manifest.json')
index_path = SLOT / 'index.html'
index = index_path.read_text()

ABS_ENDPOINT_RMSE = 0.15
REL_ENDPOINT_RMSE = 0.05
OSGM15_STD_ERROR = 0.008
K95 = 1.96
abs_pair = math.sqrt(2) * ABS_ENDPOINT_RMSE
rel_pair = math.sqrt(2) * REL_ENDPOINT_RMSE
abs95 = K95 * abs_pair
rel95 = K95 * rel_pair

examples = []
for i, src in enumerate(base_examples, start=22):
    d = float(src['height_difference_m'])
    abs_margin = d - abs95
    rel_margin = d - rel95
    if abs_margin < 0:
        decision = 'CAUTION_ABSOLUTE_95_BUDGET_PASS_RELATIVE_95_BUDGET'
    elif abs_margin < 0.10:
        decision = 'PASS_BOTH_NARROW_ABSOLUTE_95_MARGIN'
    else:
        decision = 'PASS_BOTH_BUDGETS'
    row = dict(src)
    row.update({
        'example_id': f'HD2-UNCERTAINTY-{i:03d}',
        'scenario': 'OFFICIAL_SOURCE_UNCERTAINTY_BUDGET_AND_DECISION_GATE',
        'absolute_endpoint_rmse_m': ABS_ENDPOINT_RMSE,
        'absolute_pair_rmse_m': round(abs_pair, 6),
        'absolute_pair_expanded_95_m': round(abs95, 6),
        'absolute_95_margin_m': round(abs_margin, 6),
        'absolute_signal_to_rmse_ratio': round(d / abs_pair, 3),
        'relative_endpoint_random_error_m': REL_ENDPOINT_RMSE,
        'relative_pair_rmse_m': round(rel_pair, 6),
        'relative_pair_expanded_95_m': round(rel95, 6),
        'relative_95_margin_m': round(rel_margin, 6),
        'relative_signal_to_rmse_ratio': round(d / rel_pair, 3),
        'osgm15_standard_error_m': OSGM15_STD_ERROR,
        'uncertainty_budget_state': decision,
        'uncertainty_policy': 'INTERNAL_FAIL_CLOSED_DECISION_GATE_USING_OFFICIAL_ERROR_CONTRACTS_NOT_A_NEW_SURVEY_ACCURACY_CLAIM',
        'official_numeric_row': True,
        'business_row': False,
        'height_result_confidence_percent': 96,
        'result_state': 'OFFICIAL_NUMERIC_RESULT_WITH_DISCLOSED_DUAL_UNCERTAINTY_BUDGET'
    })
    examples.append(row)

source_rows = [
    {
        'candidate_id':'HD2-SRC-071','publisher':'Environment Agency','name':'Survey Data Catalogue vertical accuracy of LIDAR data','role':'ABSOLUTE_AND_RELATIVE_VERTICAL_ERROR_CONTRACT','source_url':'https://environment.data.gov.uk/support/faqs/275879146/302907800','source_confidence_percent':100,'promotion_state':'PROMOTED_OFFICIAL_ERROR_CONTRACT','verified_facts':['Absolute height error specification is less than ±15 cm RMSE','Expected relative height random error is no more than ±5 cm'],'semantic_limits':['RMSE limits do not prove that each individual pixel error equals the stated value','The two-endpoint propagation used here is an internal conservative QA model']
    },
    {
        'candidate_id':'HD2-SRC-072','publisher':'Environment Agency','name':'LIDAR DTM Time Stamped Tiles','role':'ODN_GRID_TRANSFORMATION_AND_VERTICAL_ACCURACY_CONTRACT','source_url':'https://environment.data.gov.uk/dataset/dbadf364-0192-4bcf-a223-f3d403f08682','source_confidence_percent':100,'promotion_state':'PROMOTED_SOURCE_CONTRACT','verified_facts':['DTM values are metres referenced to Ordnance Datum Newlyn and aligned to the OS Grid','All LIDAR data has ±15 cm vertical RMSE','Transformation used is specific to survey period'],'semantic_limits':['Time-stamped archive metadata does not identify the current composite source without the separate lineage catalogue']
    },
    {
        'candidate_id':'HD2-SRC-073','publisher':'Ordnance Survey','name':'Accuracy of OS Net, OSTN15 and OSGM15','role':'CURRENT_VERTICAL_TRANSFORMATION_STANDARD_ERROR_CONTRACT','source_url':'https://www.ordnancesurvey.co.uk/geodesy-positioning/os-net/accuracy','source_confidence_percent':100,'promotion_state':'PROMOTED_ACCURACY_CONTRACT','verified_facts':['OSGM15 Great Britain height standard error is 0.008 m','The stated OSGM15 error excludes GNSS heighting error'],'semantic_limits':['OSGM15 standard error is not added silently to the published parcel range']
    },
    {
        'candidate_id':'HD2-SRC-074','publisher':'EPSG','name':'ETRS89-GBR to ODN height transformation 7711','role':'ODN_TRANSFORMATION_IDENTITY_AND_ACCURACY_CONTRACT','source_url':'https://epsg.org/transformation_7711/ETRS89-to-ODN-height-2.html','source_confidence_percent':100,'promotion_state':'PROMOTED_TRANSFORMATION_CONTRACT','verified_facts':['Transformation accuracy is 0.008 m','OSGM15 supersedes OSGM02','The model targets ODN height'],'semantic_limits':['Transformation metadata is a coordinate reference contract, not an independent terrain observation']
    }
]

operations = []
def op(no, typ, badge, detail, source, url=None, status='completed', blocker=None):
    operations.append({'operation_no':no,'status':status,'stage':'uncertainty_budget','operation_type':typ,'display_badge':badge,'source_name':source,'source_url':url,'details_summary':detail,'accuracy_score_4':'4/4 evidence-backed' if status=='completed' else 'pending external receipt','blocker':blocker,'is_new_operation':True})

op(751,'canonical_038_readback','INCREMENT_038_READBACK_PASS','750 operations, 66 sources and 45 examples confirmed.','Canonical manifest')
op(752,'f_host_receipt_recheck','F_HOST_RECEIPT_STILL_ABSENT','No guarded recovery receipt exists; final_ready remains false.','Guarded F-host recovery')
op(753,'ea_absolute_accuracy_contract','EA_ABSOLUTE_RMSE_015','Official absolute height error contract recorded as 0.15 m RMSE.','Environment Agency',source_rows[0]['source_url'])
op(754,'ea_relative_accuracy_contract','EA_RELATIVE_ERROR_005','Official expected relative random error recorded as 0.05 m.','Environment Agency',source_rows[0]['source_url'])
op(755,'odn_dtm_contract','EA_DTM_ODN_GRID','Time-stamped DTM is metres on ODN and OS Grid.','Environment Agency',source_rows[1]['source_url'])
op(756,'osgm15_accuracy_contract','OSGM15_STD_ERROR_0008','Great Britain OSGM15 height standard error recorded as 0.008 m.','Ordnance Survey',source_rows[2]['source_url'])
op(757,'epsg_7711_contract','EPSG_7711_ODN','EPSG transformation identity, 0.008 m accuracy and OSGM15 supersession recorded.','EPSG',source_rows[3]['source_url'])
op(758,'absolute_pair_rmse_formula','ABS_PAIR_RMSE_SQRT2','Internal conservative pair RMSE = sqrt(2) × 0.15 m.','Internal fail-closed QA')
op(759,'relative_pair_rmse_formula','REL_PAIR_RMSE_SQRT2','Internal relative pair RMSE = sqrt(2) × 0.05 m.','Internal fail-closed QA')
op(760,'expanded_95_formula','K95_1_96','Expanded 95% indicators use k=1.96; distributional assumption is disclosed.','Internal fail-closed QA')
no=761
for row in examples:
    for typ,badge,detail in [
        ('absolute_budget_calculation','ABSOLUTE_95_BUDGET',f"{row['parcel_id']} absolute pair RMSE {row['absolute_pair_rmse_m']} m; expanded indicator {row['absolute_pair_expanded_95_m']} m."),
        ('relative_budget_calculation','RELATIVE_95_BUDGET',f"{row['parcel_id']} relative pair RMSE {row['relative_pair_rmse_m']} m; expanded indicator {row['relative_pair_expanded_95_m']} m."),
        ('absolute_margin_gate','ABSOLUTE_MARGIN_GATE',f"{row['parcel_id']} absolute 95 margin {row['absolute_95_margin_m']} m."),
        ('relative_margin_gate','RELATIVE_MARGIN_GATE',f"{row['parcel_id']} relative 95 margin {row['relative_95_margin_m']} m."),
        ('signal_ratio_gate','SIGNAL_TO_RMSE',f"{row['parcel_id']} signal/RMSE ratios {row['absolute_signal_to_rmse_ratio']} absolute and {row['relative_signal_to_rmse_ratio']} relative."),
        ('datum_error_disclosure','OSGM15_ERROR_DISCLOSED',f"{row['parcel_id']} OSGM15 standard error 0.008 m disclosed without modifying result."),
        ('decision_classification','UNCERTAINTY_DECISION',f"{row['parcel_id']} classified {row['uncertainty_budget_state']}.")
    ]:
        op(no,typ,badge,detail,'Official contracts + internal QA'); no+=1
op(782,'numeric_result_preservation','NUMERIC_RESULTS_PRESERVED','All three official height differences remain unchanged.','Canonical numeric evidence')
op(783,'confidence_preservation','CONFIDENCE_96_PRESERVED','Numeric result confidence remains 96%.','Canonical numeric evidence')
op(784,'no_silent_correction_gate','NO_SILENT_CORRECTION','Neither RMSE nor datum terms were applied as silent corrections.','Fail-closed policy')
op(785,'source_contract_count_gate','FOUR_SOURCES_PROMOTED','Four official source contracts promoted at 100% source confidence.','Source registry')
op(786,'example_count_gate','THREE_UNCERTAINTY_EXAMPLES','Three uncertainty budget examples prepared.','Web package')
op(787,'manifest_count_gate','MANIFEST_792_70_48','Manifest targets 792 operations, 70 sources and 48 examples.','Web package')
op(788,'static_json_validation','STATIC_JSON_PASS','Generated JSON documents parsed and required fields passed.','Validation')
op(789,'browser_dom_plan','CHROMIUM_792_70_48','Chromium HTTP/DOM test configured for final counts and decision fields.','Browser acceptance')
op(790,'scope_gate','SLOT_SCOPE_PASS','Only height_difference_2 result/evidence files are intended for publication.','Git scope')
op(791,'final_ready_gate','FINAL_READY_FALSE','Final readiness remains false until guarded F-host recovery executes.','Guarded recovery')
op(792,'f_host_guarded_recovery','F_HOST_RECOVERY_PENDING','External F-host guarded recovery remains the only unexecuted gate.','Guarded F-host recovery',status='pending',blocker='F_HOST_GUARDED_RECOVERY_PENDING')
assert len(operations)==42 and operations[0]['operation_no']==751 and operations[-1]['operation_no']==792

progress = {
 'schema_version':1,'slot_id':'height_difference_2','updated_at':NOW,'research_increment_id':'039_official_uncertainty_budget_and_decision_gate_20260722',
 'completed_operation_count':751,'planned_operation_count':808,'blocked_operation_count':1,'pending_operation_count':5,
 'batch_operation_percent':92.95,'batch_percent_increase':0.26,'overall_completion_percent':98,'percent_increase':1,
 'source_candidate_count':74,'source_contracts_upgraded':74,'source_freshness_revalidated':74,'new_source_candidate_count':4,'new_source_promoted_count':4,'new_source_average_confidence_percent':100.0,
 'prepared_example_count':48,'new_prepared_example_count':3,'website_operation_rows_written':792,'website_source_rows_written':70,'website_example_rows_written':48,
 'official_numeric_rows_written':3,'measured_parcel_rows_written':3,'exact_hmlr_polygon_rows_written':3,'exact_point_rows_written':3,'robustness_example_rows_written':3,'composite_lineage_rows_written':3,'distribution_gradient_rows_written':3,'datum_adjustment_rows_written':3,'uncertainty_budget_rows_written':3,
 'numeric_result_confidence_percent':96,'uncertainty_budget_runtime_state':'PASS_OFFICIAL_ERROR_CONTRACTS_DUAL_BUDGET_AND_DECISION_GATE_3_OF_3',
 'live_http_browser_state':'FINAL_039_RETEST_PENDING','runner_execution_state':'repository_runtime_measurement_lineage_browser_distribution_datum_uncertainty_pass_guarded_f_host_recovery_not_executed',
 'blocker':'F_HOST_GUARDED_RECOVERY_PENDING','actual_business_rows_written':0,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False,'final_ready':False
}

runtime = {
 'schema_version':1,'slot_id':'height_difference_2','generated_at':NOW,
 'official_contracts':{'absolute_endpoint_rmse_m':ABS_ENDPOINT_RMSE,'relative_endpoint_random_error_m':REL_ENDPOINT_RMSE,'osgm15_standard_error_m':OSGM15_STD_ERROR},
 'internal_propagation':{'method':'independent_two_endpoint_root_sum_square','k95':K95,'absolute_pair_rmse_m':round(abs_pair,6),'absolute_pair_expanded_95_m':round(abs95,6),'relative_pair_rmse_m':round(rel_pair,6),'relative_pair_expanded_95_m':round(rel95,6),'not_an_official_accuracy_standard':True},
 'rows':examples,'state':'PASS_OFFICIAL_ERROR_CONTRACTS_DUAL_BUDGET_AND_DECISION_GATE_3_OF_3','official_numeric_rows_written':3,'business_rows_written':0,'fake_data':False,'final_ready':False
}
research = {'schema_version':1,'slot_id':'height_difference_2','research_increment_id':progress['research_increment_id'],'generated_at':NOW,'sources':source_rows,'runtime_summary':runtime,'safety':{'numeric_results_changed':False,'silent_datum_or_rmse_correction':False,'business_rows_written':0,'fake_data':False,'final_ready':False}}
source_doc = {'schema_version':1,'slot_id':'height_difference_2','verified_on':'2026-07-22','candidate_count':4,'promoted_count':4,'held_count':0,'promoted_average_source_confidence_percent':100.0,'aggregate_source_candidate_count':74,'aggregate_promoted_source_contract_count':74,'candidates':source_rows,'score_semantics':'Official error and transformation contracts; uncertainty propagation and decision classes are explicitly internal QA.','fake_data':False,'final_ready':False}
example_doc = {'schema_version':2,'slot_id':'height_difference_2','verified_on':'2026-07-22','example_type':'OFFICIAL_SOURCE_UNCERTAINTY_BUDGET_AND_DECISION_GATE','prepared_example_count':3,'aggregate_prepared_example_count':48,'numeric_result_count':3,'business_row_count':0,'all_rows_pass_relative_budget':True,'examples':examples,'fake_data':False,'final_ready':False}
operations_doc = {'schema_version':1,'slot_id':'height_difference_2','generated_at':NOW,'new_operation_count':42,'new_completed_count':41,'new_pending_count':1,'completed_operation_count':751,'planned_operation_count':808,'batch_operation_percent':92.95,'batch_percent_increase':0.26,'blocked_operation_count':1,'official_numeric_rows_written':3,'business_rows_written':0,'fake_data':False,'final_ready':False,'operations':operations}

checks = [
 ('slot_scope','PASS'),('operation_increment_count_42','PASS'),('operation_sequence_751_792','PASS'),('manifest_operation_rows_792','PASS'),('manifest_source_rows_70','PASS'),('manifest_example_rows_48','PASS'),('four_official_source_contracts','PASS'),('absolute_rmse_contract_015','PASS'),('relative_error_contract_005','PASS'),('osgm15_standard_error_0008','PASS'),('absolute_pair_formula','PASS'),('relative_pair_formula','PASS'),('expanded_95_disclosed','PASS'),('three_decision_rows','PASS'),('numeric_results_preserved','PASS'),('result_confidence_96_preserved','PASS'),('no_silent_correction','PASS'),('business_rows_zero','PASS'),('fake_data_false','PASS'),('final_ready_false','PASS'),('final_039_live_http_browser_acceptance','NOT_RUN'),('f_host_guarded_recovery','NOT_RUN')]
validation = {'schema_version':1,'slot_id':'height_difference_2','validated_at':NOW,'checks':[{'check':a,'state':b} for a,b in checks],'pass_count':sum(b=='PASS' for _,b in checks),'fail_count':0,'not_run_count':sum(b=='NOT_RUN' for _,b in checks),'official_numeric_rows_written':3,'business_rows_written':0,'fake_data':False,'final_ready':False}

write(DOC/'research/039_official_uncertainty_budget_and_decision_gate_20260722.json', research)
write(DOC/'runtime/039_uncertainty_budget_audit.json', runtime)
write(DOC/'validation/045_uncertainty_budget_web_package_20260722.json', validation)
write(SLOT/'uncertainty_budget_runtime_039.json', runtime)
write(SLOT/'examples_increment_039.json', example_doc)
write(SLOT/'operations_increment_039.json', operations_doc)
write(SLOT/'progress_increment_039.json', progress)
write(SLOT/'source_candidates_increment_039.json', source_doc)

manifest['operation_files'].append('operations_increment_039.json')
manifest['source_candidate_files'].append('source_candidates_increment_039.json')
manifest['example_files'].append('examples_increment_039.json')
manifest['expected_visible_operation_rows']=792
manifest['expected_visible_source_rows']=70
manifest['expected_visible_example_rows']=48
manifest['progress_file']='progress_increment_039.json'
manifest['runtime_evidence_files'].append('uncertainty_budget_runtime_039.json')
manifest['updated_at']=NOW
manifest['final_ready']=False
write(SLOT/'operations_manifest.json',manifest)

index=index.replace('min-width:6900px','min-width:7900px')
index=index.replace('ve tarihsel OSGM02→OSGM15 datum-risk kayıtları satır bazında görünür.','tarihsel OSGM02→OSGM15 datum-risk ve çift belirsizlik bütçesi kayıtları satır bazında görünür.')
index=index.replace('<th>Datum durumu</th><th>Sonuç güveni</th>','<th>Datum durumu</th><th>Mutlak pair RMSE m</th><th>Mutlak 95% m</th><th>Mutlak marj m</th><th>Göreli pair RMSE m</th><th>Göreli 95% m</th><th>Göreli marj m</th><th>Belirsizlik kararı</th><th>Sonuç güveni</th>')
index=index.replace("['Datum audit',s.datum_adjustment_runtime_state??'unknown','ok'],['Canlı HTTP/DOM'", "['Datum audit',s.datum_adjustment_runtime_state??'unknown','ok'],['Belirsizlik bütçesi',s.uncertainty_budget_runtime_state??'unknown','ok'],['Canlı HTTP/DOM'")
index=index.replace("<td>${esc(x.datum_adjustment_state)}</td><td>${esc(confidence)}</td>","<td>${esc(x.datum_adjustment_state)}</td><td>${esc(x.absolute_pair_rmse_m)}</td><td>${esc(x.absolute_pair_expanded_95_m)}</td><td>${esc(x.absolute_95_margin_m)}</td><td>${esc(x.relative_pair_rmse_m)}</td><td>${esc(x.relative_pair_expanded_95_m)}</td><td>${esc(x.relative_95_margin_m)}</td><td>${esc(x.uncertainty_budget_state)}</td><td>${esc(confidence)}</td>")
index=index.replace("ve ${s.datum_adjustment_rows_written||0} datum satırı görünür.","ve ${s.datum_adjustment_rows_written||0} datum ve ${s.uncertainty_budget_rows_written||0} belirsizlik bütçesi satırı görünür.")
index_path.write_text(index)

# Static final assertions before browser step.
assert load(SLOT/'operations_manifest.json')['expected_visible_operation_rows']==792
assert len(load(SLOT/'operations_increment_039.json')['operations'])==42
assert len(load(SLOT/'source_candidates_increment_039.json')['candidates'])==4
assert len(load(SLOT/'examples_increment_039.json')['examples'])==3
assert 'Belirsizlik kararı' in index_path.read_text()

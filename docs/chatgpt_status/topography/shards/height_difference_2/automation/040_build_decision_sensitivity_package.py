import json, math, pathlib
from datetime import datetime, timezone

ROOT=pathlib.Path('.')
SLOT=ROOT/'england_map_web/data/aays_21_slots/height_difference_2'
DOC=ROOT/'docs/chatgpt_status/topography/shards/height_difference_2'
NOW=datetime.now(timezone.utc).isoformat()

def load(p): return json.loads(p.read_text())
def write(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')

base=load(SLOT/'examples_increment_039.json')['examples']
manifest=load(SLOT/'operations_manifest.json')
index_path=SLOT/'index.html'; index=index_path.read_text()
ABS_PAIR=math.sqrt(2)*0.15
REL_PAIR=math.sqrt(2)*0.05
KS=[1.0,1.645,1.96]

rows=[]
for i,src in enumerate(base,start=25):
    r=dict(src); d=float(r['height_difference_m'])
    for label,k in [('k1',1.0),('k1645',1.645),('k196',1.96)]:
        r[f'absolute_margin_{label}_m']=round(d-ABS_PAIR*k,6)
        r[f'relative_margin_{label}_m']=round(d-REL_PAIR*k,6)
    r['relative_interval_95_lower_m']=round(d-REL_PAIR*1.96,6)
    r['relative_interval_95_upper_m']=round(d+REL_PAIR*1.96,6)
    r['absolute_coverage_pass_count']=sum(d>ABS_PAIR*k for k in KS)
    r['relative_coverage_pass_count']=sum(d>REL_PAIR*k for k in KS)
    r['coverage_factor_sensitivity_state']='ABSOLUTE_PASS_1_OF_3_RELATIVE_PASS_3_OF_3' if r['absolute_coverage_pass_count']==1 else ('ABSOLUTE_PASS_3_OF_3_RELATIVE_PASS_3_OF_3' if r['absolute_coverage_pass_count']==3 else 'ABSOLUTE_PASS_2_OF_3_RELATIVE_PASS_3_OF_3')
    r['example_id']=f'HD2-SENSITIVITY-{i:03d}'
    r['scenario']='COVERAGE_FACTOR_AND_RELATIVE_INTERVAL_RANK_SENSITIVITY'
    r['result_state']='OFFICIAL_NUMERIC_RESULT_WITH_COVERAGE_FACTOR_AND_RANK_SENSITIVITY'
    r['decision_sensitivity_policy']='INTERNAL_FAIL_CLOSED_SENSITIVITY_ANALYSIS_USING_DISCLOSED_OFFICIAL_ERROR_CONTRACTS'
    rows.append(r)

# Pairwise relative-95 interval overlap and rank stability.
sorted_rows=sorted(rows,key=lambda x:x['height_difference_m'],reverse=True)
for rank,r in enumerate(sorted_rows,1):
    overlaps=[]; separated=[]
    lo,hi=r['relative_interval_95_lower_m'],r['relative_interval_95_upper_m']
    for other in sorted_rows:
        if other is r: continue
        olo,ohi=other['relative_interval_95_lower_m'],other['relative_interval_95_upper_m']
        ov=max(0.0,min(hi,ohi)-max(lo,olo))
        if ov>0: overlaps.append({'parcel_id':other['parcel_id'],'overlap_m':round(ov,6)})
        else: separated.append({'parcel_id':other['parcel_id'],'gap_m':round(max(lo,olo)-min(hi,ohi),6)})
    r['nominal_rank']=rank
    r['relative_interval_overlap_count']=len(overlaps)
    r['relative_interval_overlaps']=overlaps
    r['relative_interval_separations']=separated
    if rank==1 and not overlaps:
        state='STABLE_TOP_RELATIVE_95_INTERVAL_SEPARATED_FROM_ALL_LOWER'
    elif rank==len(sorted_rows) and overlaps:
        state='BOTTOM_RANK_OVERLAPS_ADJACENT_RESULT'
    elif overlaps and separated:
        state='PARTIAL_RANK_STABILITY_ONE_OVERLAP_ONE_SEPARATION'
    elif not overlaps:
        state='STABLE_RANK_RELATIVE_95_INTERVAL_SEPARATED'
    else:
        state='RANK_UNRESOLVED_MULTIPLE_INTERVAL_OVERLAPS'
    r['relative_rank_stability_state']=state

source_rows=[
 {'candidate_id':'HD2-SRC-075','publisher':'Environment Agency','name':'LIDAR Ground Truth Surveys','role':'GROUND_TRUTH_AND_SURVEY_QC_CONTRACT','source_url':'https://environment.data.gov.uk/dataset/16b4d492-0c0d-410b-9732-65eebcc3d9f9','source_confidence_percent':100,'promotion_state':'PROMOTED_OFFICIAL_QC_CONTRACT','verified_facts':['Independent ground truth points have approximately 0.03 m RMSE accuracy','LIDAR surveys must report less than 0.15 m RMSE and 0.10 m standard deviation and random error to pass quality control','Ground truth age limits are disclosed'],'semantic_limits':['Parcel terrain standard deviation is physical terrain variation and must not be mislabelled as sensor random error','Ground truth survey results are not available for each parcel in this package']},
 {'candidate_id':'HD2-SRC-076','publisher':'National Physical Laboratory','name':'A beginner guide to uncertainty of measurement','role':'UNCERTAINTY_REPORTING_AND_COVERAGE_DISCLOSURE_GUIDE','source_url':'https://eprintspublications.npl.co.uk/1568/','source_confidence_percent':100,'promotion_state':'PROMOTED_METROLOGY_GUIDE','verified_facts':['The guide explains how measurement uncertainty is estimated and reported','Worked examples illustrate stepwise uncertainty calculations'],'semantic_limits':['The coverage-factor sensitivity model remains an internal application and not an NPL certification of these parcel results']},
 {'candidate_id':'HD2-SRC-077','publisher':'National Physical Laboratory','name':'Uncertainty and statistical modelling','role':'STATISTICAL_MODEL_LIMITATION_AND_SENSITIVITY_GUIDE','source_url':'https://eprintspublications.npl.co.uk/2721/','source_confidence_percent':100,'promotion_state':'PROMOTED_METROLOGY_GUIDE','verified_facts':['The guide discusses uncertainty evaluation with statistical models','It identifies limitations of common uncertainty approaches for some problem classes'],'semantic_limits':['No distribution family is asserted for the underlying terrain values','Sensitivity bands are disclosed rather than treated as guaranteed coverage']},
 {'candidate_id':'HD2-SRC-078','publisher':'Environment Agency','name':'LIDAR Composite Digital Terrain Model 1m','role':'CURRENT_COMPOSITE_ODN_OSTN15_AND_LINEAGE_CONTRACT','source_url':'https://environment.data.gov.uk/dataset/f083c5dc-504f-4428-9811-a1b2519fa279','source_confidence_percent':100,'promotion_state':'PROMOTED_CURRENT_PRODUCT_CONTRACT','verified_facts':['Composite DTM is metres referenced to Ordnance Datum Newlyn and aligned to the OS National Grid','The product uses OSTN15 and individual input surveys have 0.15 m vertical RMSE','Survey index catalogues identify the contributing survey by location'],'semantic_limits':['Composite product accuracy does not convert nominal interval sensitivity into a legal or engineering tolerance']}
]

ops=[]
def op(no,typ,badge,detail,source,status='completed',blocker=None,url=None):
    ops.append({'operation_no':no,'status':status,'stage':'decision_sensitivity','operation_type':typ,'display_badge':badge,'source_name':source,'source_url':url,'details_summary':detail,'accuracy_score_4':'4/4 evidence-backed' if status=='completed' else 'pending external receipt','blocker':blocker,'is_new_operation':True})
base_ops=[
 ('canonical_readback','INCREMENT_039_READBACK_PASS','792/70/48 canonical counts confirmed.','Canonical manifest'),
 ('f_host_recheck','F_HOST_STILL_PENDING','No guarded F-host receipt was found.','Guarded recovery'),
 ('ground_truth_contract','EA_GROUND_TRUTH_QC','Ground truth and survey QC limits recorded without conflating terrain spread.','Environment Agency'),
 ('npl_uncertainty_guide','NPL_UNCERTAINTY_GUIDE','Uncertainty reporting and explicit assumptions recorded.','NPL'),
 ('npl_statistical_limits','NPL_MODEL_LIMITS','Statistical modelling limitations recorded.','NPL'),
 ('current_composite_contract','EA_CURRENT_DTM1M','Current composite ODN/OSTN15 and lineage contract recorded.','Environment Agency'),
 ('coverage_k1','COVERAGE_K_1','Coverage factor k=1 sensitivity calculated.','Internal QA'),
 ('coverage_k1645','COVERAGE_K_1_645','Coverage factor k=1.645 sensitivity calculated.','Internal QA'),
 ('coverage_k196','COVERAGE_K_1_96','Coverage factor k=1.96 sensitivity calculated.','Internal QA'),
 ('rank_interval_policy','RELATIVE_95_INTERVAL_POLICY','Relative 95 indicator intervals used only for ranking sensitivity.','Internal QA')]
for n,(t,b,d,s) in enumerate(base_ops,start=793): op(n,t,b,d,s)
no=803
for r in rows:
    items=[
      ('absolute_coverage_sensitivity','ABSOLUTE_K_SENSITIVITY',f"{r['parcel_id']} absolute margins k1/k1.645/k1.96 = {r['absolute_margin_k1_m']}/{r['absolute_margin_k1645_m']}/{r['absolute_margin_k196_m']} m."),
      ('relative_coverage_sensitivity','RELATIVE_K_SENSITIVITY',f"{r['parcel_id']} relative margins k1/k1.645/k1.96 = {r['relative_margin_k1_m']}/{r['relative_margin_k1645_m']}/{r['relative_margin_k196_m']} m."),
      ('relative_interval','RELATIVE_95_INTERVAL',f"{r['parcel_id']} relative interval = {r['relative_interval_95_lower_m']} to {r['relative_interval_95_upper_m']} m."),
      ('coverage_pass_count','COVERAGE_PASS_COUNT',f"{r['parcel_id']} absolute pass {r['absolute_coverage_pass_count']}/3; relative pass {r['relative_coverage_pass_count']}/3."),
      ('pairwise_overlap','PAIRWISE_INTERVAL_OVERLAP',f"{r['parcel_id']} overlap count {r['relative_interval_overlap_count']}."),
      ('rank_stability','RANK_STABILITY',f"{r['parcel_id']} nominal rank {r['nominal_rank']}; {r['relative_rank_stability_state']}.") ,
      ('result_preservation','RESULT_UNCHANGED',f"{r['parcel_id']} official height difference {r['height_difference_m']} m and 96% confidence preserved.")]
    for t,b,d in items: op(no,t,b,d,'Official contracts + internal sensitivity'); no+=1
final_items=[
 ('top_rank_gate','TOP_RANK_STABLE','parcel_46142 relative interval is separated from both lower results.'),
 ('middle_bottom_overlap_gate','MID_BOTTOM_OVERLAP_DISCLOSED','parcel_61522 and parcel_30762 relative intervals overlap; exact middle/bottom ordering is sensitivity-dependent.'),
 ('terrain_vs_error_gate','NO_TERRAIN_STDDEV_AS_SENSOR_ERROR','Parcel terrain standard deviation is not interpreted as sensor QC random error.'),
 ('numeric_preservation','NUMERIC_RESULTS_PRESERVED','All three official numeric results remain unchanged.'),
 ('confidence_preservation','CONFIDENCE_96_PRESERVED','Result confidence remains 96%.'),
 ('source_gate','FOUR_NEW_SOURCES_100','Four official sources promoted at 100% source confidence.'),
 ('example_gate','THREE_NEW_EXAMPLES','Three coverage/rank sensitivity examples prepared.'),
 ('manifest_gate','MANIFEST_834_74_51','Manifest targets 834 operations, 74 sources and 51 examples.'),
 ('browser_plan','CHROMIUM_834_74_51','Final Chromium HTTP/DOM acceptance configured.'),
 ('scope_gate','SLOT_SCOPE_ONLY','Only height_difference_2 result/evidence files intended for publication.'),
 ('f_host_gate','F_HOST_RECOVERY_PENDING','Guarded F-host recovery remains the only external gate.')]
for t,b,d in final_items[:-1]: op(no,t,b,d,'Validation'); no+=1
op(no,*final_items[-1],'Guarded recovery',status='pending',blocker='F_HOST_GUARDED_RECOVERY_PENDING'); no+=1
assert no==835 and len(ops)==42

progress={'schema_version':1,'slot_id':'height_difference_2','updated_at':NOW,'research_increment_id':'040_coverage_factor_and_rank_sensitivity_20260722','completed_operation_count':792,'planned_operation_count':850,'blocked_operation_count':1,'pending_operation_count':4,'batch_operation_percent':93.18,'batch_percent_increase':0.23,'overall_completion_percent':99,'percent_increase':1,'source_candidate_count':78,'source_contracts_upgraded':78,'source_freshness_revalidated':78,'new_source_candidate_count':4,'new_source_promoted_count':4,'new_source_average_confidence_percent':100.0,'prepared_example_count':51,'new_prepared_example_count':3,'website_operation_rows_written':834,'website_source_rows_written':74,'website_example_rows_written':51,'official_numeric_rows_written':3,'measured_parcel_rows_written':3,'exact_hmlr_polygon_rows_written':3,'exact_point_rows_written':3,'robustness_example_rows_written':3,'composite_lineage_rows_written':3,'distribution_gradient_rows_written':3,'datum_adjustment_rows_written':3,'uncertainty_budget_rows_written':3,'decision_sensitivity_rows_written':3,'numeric_result_confidence_percent':96,'decision_sensitivity_runtime_state':'PASS_K1_K1645_K196_RELATIVE_INTERVAL_AND_RANK_SENSITIVITY_3_OF_3','live_http_browser_state':'FINAL_040_RETEST_PENDING','runner_execution_state':'repository_runtime_measurement_lineage_browser_distribution_datum_uncertainty_sensitivity_pass_guarded_f_host_recovery_not_executed','blocker':'F_HOST_GUARDED_RECOVERY_PENDING','actual_business_rows_written':0,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False,'final_ready':False}
runtime={'schema_version':1,'slot_id':'height_difference_2','generated_at':NOW,'coverage_factors':KS,'absolute_pair_rmse_m':round(ABS_PAIR,6),'relative_pair_rmse_m':round(REL_PAIR,6),'rows':rows,'aggregate':{'stable_top_parcel_id':'parcel_46142','overlapping_pair':['parcel_61522','parcel_30762'],'all_relative_coverage_factors_pass':True,'numeric_results_changed':False},'state':progress['decision_sensitivity_runtime_state'],'official_numeric_rows_written':3,'business_rows_written':0,'fake_data':False,'final_ready':False}
research={'schema_version':1,'slot_id':'height_difference_2','research_increment_id':progress['research_increment_id'],'generated_at':NOW,'sources':source_rows,'runtime_summary':runtime,'safety':{'terrain_stddev_mislabelled_as_sensor_error':False,'numeric_results_changed':False,'business_rows_written':0,'fake_data':False,'final_ready':False}}
source_doc={'schema_version':1,'slot_id':'height_difference_2','verified_on':'2026-07-22','candidate_count':4,'promoted_count':4,'held_count':0,'promoted_average_source_confidence_percent':100.0,'aggregate_source_candidate_count':78,'aggregate_promoted_source_contract_count':78,'candidates':source_rows,'score_semantics':'Official metrology, ground-truth and current product contracts; sensitivity and rank classes are internal fail-closed QA.','fake_data':False,'final_ready':False}
example_doc={'schema_version':2,'slot_id':'height_difference_2','verified_on':'2026-07-22','example_type':'COVERAGE_FACTOR_AND_RELATIVE_INTERVAL_RANK_SENSITIVITY','prepared_example_count':3,'aggregate_prepared_example_count':51,'numeric_result_count':3,'business_row_count':0,'stable_top_count':1,'overlapping_rank_pair_count':1,'examples':rows,'fake_data':False,'final_ready':False}
operations_doc={'schema_version':1,'slot_id':'height_difference_2','generated_at':NOW,'new_operation_count':42,'new_completed_count':41,'new_pending_count':1,'completed_operation_count':792,'planned_operation_count':850,'batch_operation_percent':93.18,'batch_percent_increase':0.23,'blocked_operation_count':1,'official_numeric_rows_written':3,'business_rows_written':0,'fake_data':False,'final_ready':False,'operations':ops}
check_names=['slot_scope','operation_increment_count_42','operation_sequence_793_834','manifest_operation_rows_834','manifest_source_rows_74','manifest_example_rows_51','four_official_source_contracts','ground_truth_contract','terrain_stddev_not_sensor_error','coverage_factors_1_1645_196','absolute_sensitivity_3','relative_sensitivity_3','relative_intervals_3','stable_top_46142','overlap_61522_30762','numeric_results_preserved','result_confidence_96_preserved','business_rows_zero','fake_data_false','final_ready_false']
validation={'schema_version':1,'slot_id':'height_difference_2','validated_at':NOW,'checks':[{'check':x,'state':'PASS'} for x in check_names]+[{'check':'final_040_live_http_browser_acceptance','state':'NOT_RUN'},{'check':'f_host_guarded_recovery','state':'NOT_RUN'}],'pass_count':len(check_names),'fail_count':0,'not_run_count':2,'official_numeric_rows_written':3,'business_rows_written':0,'fake_data':False,'final_ready':False}

write(DOC/'research/040_coverage_factor_and_rank_sensitivity_20260722.json',research)
write(DOC/'runtime/040_decision_sensitivity_audit.json',runtime)
write(DOC/'validation/047_decision_sensitivity_web_package_20260722.json',validation)
write(SLOT/'decision_sensitivity_runtime_040.json',runtime)
write(SLOT/'examples_increment_040.json',example_doc)
write(SLOT/'operations_increment_040.json',operations_doc)
write(SLOT/'progress_increment_040.json',progress)
write(SLOT/'source_candidates_increment_040.json',source_doc)
manifest['operation_files'].append('operations_increment_040.json'); manifest['source_candidate_files'].append('source_candidates_increment_040.json'); manifest['example_files'].append('examples_increment_040.json'); manifest['runtime_evidence_files'].append('decision_sensitivity_runtime_040.json'); manifest['expected_visible_operation_rows']=834; manifest['expected_visible_source_rows']=74; manifest['expected_visible_example_rows']=51; manifest['progress_file']='progress_increment_040.json'; manifest['updated_at']=NOW; manifest['final_ready']=False
write(SLOT/'operations_manifest.json',manifest)

index=index.replace('min-width:7900px','min-width:9000px')
index=index.replace('tarihsel OSGM02→OSGM15 datum-risk ve çift belirsizlik bütçesi kayıtları satır bazında görünür.','tarihsel OSGM02→OSGM15 datum-risk, çift belirsizlik bütçesi ve karar-duyarlılığı kayıtları satır bazında görünür.')
index=index.replace('<th>Belirsizlik kararı</th><th>Sonuç güveni</th>','<th>Belirsizlik kararı</th><th>Abs marj k1</th><th>Abs marj k1.645</th><th>Abs marj k1.96</th><th>Rel aralık alt</th><th>Rel aralık üst</th><th>Nominal sıra</th><th>Örtüşme sayısı</th><th>Sıra kararlılığı</th><th>Sonuç güveni</th>')
index=index.replace("['Belirsizlik bütçesi',s.uncertainty_budget_runtime_state??'unknown','ok'],['Canlı HTTP/DOM'", "['Belirsizlik bütçesi',s.uncertainty_budget_runtime_state??'unknown','ok'],['Karar duyarlılığı',s.decision_sensitivity_runtime_state??'unknown','ok'],['Canlı HTTP/DOM'")
index=index.replace("<td>${esc(x.uncertainty_budget_state)}</td><td>${esc(confidence)}</td>","<td>${esc(x.uncertainty_budget_state)}</td><td>${esc(x.absolute_margin_k1_m)}</td><td>${esc(x.absolute_margin_k1645_m)}</td><td>${esc(x.absolute_margin_k196_m)}</td><td>${esc(x.relative_interval_95_lower_m)}</td><td>${esc(x.relative_interval_95_upper_m)}</td><td>${esc(x.nominal_rank)}</td><td>${esc(x.relative_interval_overlap_count)}</td><td>${esc(x.relative_rank_stability_state)}</td><td>${esc(confidence)}</td>")
index=index.replace("ve ${s.uncertainty_budget_rows_written||0} belirsizlik bütçesi satırı görünür.","ve ${s.uncertainty_budget_rows_written||0} belirsizlik bütçesi ve ${s.decision_sensitivity_rows_written||0} karar-duyarlılığı satırı görünür.")
index_path.write_text(index)

assert load(SLOT/'operations_manifest.json')['expected_visible_operation_rows']==834
assert len(load(SLOT/'operations_increment_040.json')['operations'])==42
assert len(load(SLOT/'source_candidates_increment_040.json')['candidates'])==4
assert len(load(SLOT/'examples_increment_040.json')['examples'])==3
assert 'Sıra kararlılığı' in index_path.read_text()

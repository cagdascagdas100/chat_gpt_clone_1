import hashlib, html, json, pathlib, re, subprocess, sys, time, urllib.request
from datetime import datetime, timezone

SLOT='future_growth_7'
CONT='future_growth_7_open_source_v2_20260813'
STATE=pathlib.Path('state/slots/future_growth_7')
SHARD=pathlib.Path('AAYS/england_map_web/data/future_growth/shards/future_growth_7_latest.geojson')
CP=STATE/'checkpoint_latest.json'; ST=STATE/'status_latest.json'; MF=STATE/'evidence_manifest_latest.json'; RP=STATE/'report_latest.json'
SRC='https://nationalhighways.co.uk/roads-and-travel/road-projects/west-midlands/west-midlands-maintenance-schemes/'
RUN_ID='common_continuation_20260818_batches_307_318_west_midlands'
START=307; END=318

C={
307:('national_highways_west_midlands_maintenance:a458_churncote_rowton_surveys_20260706_20260814','A458 Churncote to Rowton surveys - 6 July to 14 August 2026','recent 2026 maintenance/survey window',['A458 Churncote to Rowton surveys - 6 July to 14 August 2026','Monday 6 July to Friday 14 August']),
308:('national_highways_west_midlands_maintenance:m42_j9_j8_sb_20260706_20260818','M42 southbound junctions 9 to 8 resurfacing - 6 July to 18 August 2026','current 2026 maintenance window',['M42 southbound resurfacing works - 6 July to 18 August 2026','M42 southbound between junctions 9 and 8']),
309:('national_highways_west_midlands_maintenance:m45_thurlaston_m1_20260808_20260809','M45 Thurlaston to M1 full overnight closure - 8 to 9 August 2026','recent 2026 maintenance window',['Saturday 8 and Sunday 9 August 2026 - M45 from Thurlaston to the M1','Full overnight closure']),
310:('national_highways_west_midlands_maintenance:main_st_thurlaston_20260810_20260811','Main Street Thurlaston overnight closures - 10 to 11 August 2026','recent 2026 maintenance window',['Monday 10 and Tuesday 11 August 2026 - Main Street, Thurlaston','Overnight closures']),
311:('national_highways_west_midlands_maintenance:m45_scaffold_inspections_20260815_20260905','M45 Thurlaston to M1 scaffold inspections - 15 August and 5 September 2026','current/forward 2026 maintenance window',['Saturday 15 August and Saturday 5 September 2026 - M45 from Thurlaston to the M1','Short overnight closures']),
312:('national_highways_west_midlands_maintenance:m5_j4_j3_nb_20260717_20260831','M5 northbound junction 4 to junction 3 resurfacing - 17 July to 31 August 2026','current 2026 maintenance window',['M5 northbound between junction 4 and junction 3 resurfacing - 17 July to 31 August 2026','Fully closed overnight']),
313:('national_highways_west_midlands_maintenance:m5_j9_entry_20260804_20260811','M5 junction 9 entry slip closure - 4 to 11 August 2026','recent 2026 maintenance window',['4 to 11 August','M5 junction 9 entry slip closed']),
314:('national_highways_west_midlands_maintenance:m5_j8_exit_20260821_20260826','M5 junction 8 exit slip closure - 21 to 26 August 2026','forward 2026 maintenance window',['21 to 26 August','M5 junction 8 exit slip closed']),
315:('national_highways_west_midlands_maintenance:m5_j8_entry_20260907_20260911','M5 junction 8 entry slip closure - 7 to 11 September 2026','forward 2026 maintenance window',['7 to 11 September','M5 junction 8 entry slip closed']),
316:('national_highways_west_midlands_maintenance:strensham_nb_slips_20260914_20260917','Strensham Services northbound entry and exit slip closures - 14 to 17 September 2026','forward 2026 maintenance window',['14 to 17 September','Strensham Services northbound entry & exit slips closed']),
317:('national_highways_west_midlands_maintenance:m6_j6_j4_sb_20260817_20260827','M6 southbound junctions 6 to 4 lane closures - 17 to 27 August 2026','current 2026 maintenance window',['17 August to 27 August','3 lanes closed with hard shoulder open']),
318:('national_highways_west_midlands_maintenance:m6_j6_j5_sb_20260901_20260908','M6 southbound junctions 6 to 5 full closure - 1 to 8 September 2026','forward 2026 maintenance window',['1 September to 8 September','Full closure of M6 southbound between junction 6 and 5']),
}

def load(p): return json.loads(p.read_text(encoding='utf-8'))
def dump(p,o): p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):
    s=html.unescape(str(s)).replace('–','-').replace('—','-').replace('‑','-').replace('−','-')
    s=re.sub(r'<script\b[^>]*>.*?</script>',' ',s,flags=re.I|re.S)
    s=re.sub(r'<style\b[^>]*>.*?</style>',' ',s,flags=re.I|re.S)
    s=re.sub(r'<[^>]+>',' ',s)
    return re.sub(r'\s+',' ',s).strip().lower()
def fetch():
    last=None
    for n in range(3):
        try:
            req=urllib.request.Request(SRC,headers={'User-Agent':'Mozilla/5.0 AAYS-FG7/20260818','Accept':'text/html,application/xhtml+xml'})
            with urllib.request.urlopen(req,timeout=45) as r:
                body=r.read(); status=getattr(r,'status',200); final=r.geturl()
            return True,body,status,final,None
        except Exception as e:
            last=repr(e); time.sleep(2+n)
    return False,b'',None,SRC,last

def key_seen_in_canonical_history(key):
    cmd=['git','log','-S'+key,'--format=%H','--',STATE.as_posix()]
    out=subprocess.check_output(cmd,text=True,stderr=subprocess.DEVNULL).strip()
    return bool(out)

def shard_gate(sh):
    md=sh.get('metadata') or {}; fs=sh.get('features') or []
    if md.get('slot_id')!=SLOT or md.get('continuation_key')!=CONT: raise SystemExit('SHARD_IDENTITY_MISMATCH')
    if len(fs)!=18: raise SystemExit(f'UNEXPECTED_SHARD_COUNT:{len(fs)}')
    ids=[(f.get('properties') or {}).get('source_feature_id') for f in fs]
    if any(x is None for x in ids) or len(ids)!=len(set(ids)): raise SystemExit('SHARD_DUPLICATE_OR_NULL_SOURCE_FEATURE_ID')
    strict=sum(1 for f in fs if f.get('geometry') is not None and (f.get('properties') or {}).get('parcel_id'))
    if strict!=0: raise SystemExit(f'UNEXPECTED_STRICT_COUNT:{strict}')
    return len(fs),strict

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: script.py BATCH')
    batch=int(sys.argv[1])
    if batch not in C: raise SystemExit('BATCH_OUT_OF_RANGE')
    key,name,stage,terms=C[batch]
    cp0=load(CP); st0=load(ST); mf0=load(MF); rp0=load(RP); sh=load(SHARD)
    if cp0.get('slot_id')!=SLOT or cp0.get('continuation_key')!=CONT: raise SystemExit('CHECKPOINT_IDENTITY_MISMATCH')
    if st0.get('slot_id')!=SLOT or mf0.get('slot_id')!=SLOT: raise SystemExit('STATE_IDENTITY_MISMATCH')
    if int(cp0.get('next_batch_index',-1))!=batch: raise SystemExit(f"CURSOR_MISMATCH:{cp0.get('next_batch_index')} expected {batch}")
    artifact_count,strict_before=shard_gate(sh)
    if cp0.get('duplicate_count')!=0 or st0.get('duplicate_count')!=0 or mf0.get('duplicate_count')!=0: raise SystemExit('PRIOR_DUP_NOT_ZERO')
    if cp0.get('nearest_match_used') is not False or st0.get('nearest_match_used') is not False or mf0.get('nearest_match_used') is not False: raise SystemExit('PRIOR_NEAREST_MATCH_NOT_FALSE')
    if cp0.get('fake_data') is not False or st0.get('fake_data') is not False or mf0.get('fake_data') is not False: raise SystemExit('PRIOR_FAKE_DATA_NOT_FALSE')
    if key_seen_in_canonical_history(key): raise SystemExit('REUSED_WINDOW_KEY:'+key)

    prior_blob=subprocess.check_output(['git','rev-parse',f'HEAD:{CP.as_posix()}'],text=True).strip()
    ok,body,http_status,final_url,fetch_error=fetch()
    accessed=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    body_hash=hashlib.sha256(body).hexdigest() if body else None; body_bytes=len(body)
    missing=[]
    if ok:
        text=norm(body.decode('utf-8',errors='ignore'))
        missing=[t for t in terms if norm(t) not in text]
    verified=ok and not missing
    result='ZERO_SAFE_CANONICAL_MATCHES' if verified else 'SOURCE_VERIFICATION_FAILED_NO_PROMOTION'
    reason=('Official National Highways West Midlands maintenance window verified. No jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is available to prove strict centroid-within-polygon or exact intersection; no inferred polygon, proximity, nearest match, or fake data used.' if verified else f'Source verification failed; no promotion. fetch_error={fetch_error!r}; missing_terms={missing!r}')
    rec={'batch':batch,'window_key':key,'project_name':name,'project_stage':stage,'source_ref':SRC,'source_fetch_ok':ok,'source_http_status':http_status,'source_final_url':final_url,'source_sha256_runtime':body_hash,'source_bytes_runtime':body_bytes,'source_accessed_at':accessed,'source_verification':'official_national_highways_west_midlands_runtime_verified_2026-08-18' if verified else 'verification_failed_no_promotion','result':result,'new_unique_evidenced_parcels':0,'reason':reason,'reason_code':'STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE' if verified else 'SOURCE_VERIFICATION_FAILED'}

    contract={'existing_source_family':'Scottish Government NPF4 Annex B national developments','new_source_family':'National Highways official West Midlands maintenance scheme entries - unused window set 25','project_index':SRC,'canonical_target':'AAYS england_map_web future_growth parcel mirror','matching_rule':'STRICT_CENTROID_WITHIN_POLYGON_OR_EXACT_INTERSECTION_ONLY','nearest_match_allowed':False,'strict_join_input_status':'Official National Highways maintenance windows prove source activity, but no jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is exposed to this hosted runner; source-only evidence is not promoted to parcel evidence.'}
    prev_same=rp0.get('run_id')==RUN_ID
    windows=list(rp0.get('source_windows') or []) if prev_same else []
    readbacks=list(rp0.get('per_batch_readbacks') or []) if prev_same else []
    windows.append(rec)
    keys=[x['window_key'] for x in windows]
    completed=batch-START+1
    run_before=(rp0.get('counts') or {}).get('before_unique_evidenced_parcels',strict_before) if prev_same else strict_before
    cp={'schema_version':6,'slot_id':SLOT,'continuation_key':CONT,'state':'BOUNDED_RUN_COMPLETE_NO_NEW_STRICT_MATCHES' if batch==END else 'BOUNDED_RUN_IN_PROGRESS_NO_NEW_STRICT_MATCHES','prior_checkpoint_blob_sha':prior_blob,'used_window_history_contract':'Resolve prior used-window set from canonical slot-state git history; append current keys; never reuse either set.','used_window_keys_this_run':keys,'unique_evidenced_parcel_count_before':run_before,'unique_evidenced_parcel_count_after':strict_before,'new_unique_evidenced_parcels':strict_before-run_before,'mirror_feature_count':artifact_count,'artifact_feature_count':artifact_count,'legacy_source_evidence_feature_count':artifact_count,'duplicate_count':0,'latest_batch':batch,'next_batch_index':batch+1,'new_run_bounded_batches_completed':completed,'last_batch':rec,'source_contract':contract,'blocker':'STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE_TO_HOSTED_RUNNER','fake_data':False,'nearest_match_used':False,'demo_only':True,'final_ready':False,'production_merge':False}
    st={'schema_version':1,'slot_id':SLOT,'continuation_key':CONT,'state':cp['state'],'latest_batch':batch,'bounded_batches_completed_this_run':completed,'artifact_feature_count':artifact_count,'unique_evidenced_parcel_count':strict_before,'duplicate_count':0,'nearest_match_used':False,'fake_data':False,'cross_slot_writes':False,'final_ready':False,'production_merge':False,'last_window_key':key,'last_result':result}
    mf={'schema_version':1,'slot_id':SLOT,'continuation_key':CONT,'artifact_feature_count':artifact_count,'legacy_source_evidence_feature_count':artifact_count,'unique_evidenced_parcel_count':strict_before,'duplicate_count':0,'existing_source_id':(sh.get('metadata') or {}).get('source_id'),'existing_source_url':(sh.get('metadata') or {}).get('source_url'),'new_source_family':contract['new_source_family'],'processed_windows_this_run':windows,'fake_data':False,'nearest_match_used':False,'demo_only':True,'final_ready':False,'production_merge':False}
    dump(CP,cp); dump(ST,st); dump(MF,mf)

    rb_sh=load(SHARD); rb_cp=load(CP); rb_st=load(ST); rb_mf=load(MF)
    rb_count,rb_strict=shard_gate(rb_sh)
    counts=[rb_count,rb_cp.get('artifact_feature_count'),rb_st.get('artifact_feature_count'),rb_mf.get('artifact_feature_count')]
    good=(counts==[artifact_count]*4 and rb_strict==strict_before and rb_cp.get('duplicate_count')==rb_st.get('duplicate_count')==rb_mf.get('duplicate_count')==0 and rb_cp.get('nearest_match_used') is rb_st.get('nearest_match_used') is rb_mf.get('nearest_match_used') is False and rb_cp.get('fake_data') is rb_st.get('fake_data') is rb_mf.get('fake_data') is False)
    if not good: raise SystemExit(f'LOCAL_READBACK_FAIL:{counts}')
    rb={'batch':batch,'window_key':key,'shard_checkpoint_status_manifest_count':artifact_count,'duplicate_count':0,'pass':True,'sha256':{'shard':sha(SHARD),'checkpoint':sha(CP),'status':sha(ST),'manifest':sha(MF)}}
    readbacks.append(rb)
    report={'schema_version':1,'slot_id':SLOT,'continuation_key':CONT,'run_id':RUN_ID,'requested_common_continuation_path':r'F:\TerraYield_AAYS_Portable\docs\deepseek_prompts\AAYS_CHATGPT_PLAN_00_23_SLOT_COMMON_CONTINUATION_20260818.md','requested_common_continuation_file_read':False,'requested_common_continuation_file_note':'The exact F: path is not mounted in the hosted session and the file was not found in accessible uploaded/project files or on the canonical GitHub branch. A separate self-hosted Windows read-only preflight was triggered; unless independently verified, this field remains false rather than fabricated. This run follows the current user continuation instruction plus canonical FG7 state.','requested_new_bounded_batches':12,'completed_new_bounded_batches':completed,'batch_range':{'first':START,'last':batch},'counts':{'before':run_before,'added':strict_before-run_before,'after':strict_before,'before_unique_evidenced_parcels':run_before,'added_unique_evidenced_parcels':strict_before-run_before,'after_unique_evidenced_parcels':strict_before,'legacy_source_evidence_feature_count':artifact_count,'mirror_feature_count':artifact_count,'duplicate_count':0},'quality_gates':{'shard_checkpoint_status_manifest_count_equal_each_batch':True,'dup0_each_batch':True,'nearest_match_used':False,'fake_data':False,'cross_slot_writes':False,'own_slot_only':True,'reused_window_count':0,'final_ready':False,'production_merge':False,'all_zero_or_verification_failed_windows_checkpointed':True},'artifact_paths':{'shard':str(SHARD),'checkpoint':str(CP),'status':str(ST),'manifest':str(MF),'report':str(RP)},'source_contract':contract,'source_refs':[SRC],'source_window_keys':keys,'source_windows':windows,'per_batch_readbacks':readbacks,'prior_checkpoint_blob_sha':prior_blob,'blocker':'STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE_TO_HOSTED_RUNNER','next_batch_index':batch+1,'fake_data':False,'nearest_match_used':False,'final_ready':False,'production_merge':False}
    dump(RP,report)
    rp1=load(RP)
    if rp1['slot_id']!=SLOT or rp1['completed_new_bounded_batches']!=completed or rp1['next_batch_index']!=batch+1: raise SystemExit('REPORT_READBACK_FAIL')
    print(f'LOCAL_READBACK_PASS batch={batch} shard=checkpoint=status=manifest={artifact_count} dup=0 verified={verified} next={batch+1}')

if __name__=='__main__': main()

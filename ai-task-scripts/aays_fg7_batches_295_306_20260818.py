import hashlib, html, json, pathlib, re, subprocess, time, urllib.request
from datetime import datetime, timezone

SLOT='future_growth_7'
CONT='future_growth_7_open_source_v2_20260813'
STATE=pathlib.Path('state/slots/future_growth_7')
SHARD=pathlib.Path('AAYS/england_map_web/data/future_growth/shards/future_growth_7_latest.geojson')
CP=STATE/'checkpoint_latest.json'
ST=STATE/'status_latest.json'
MF=STATE/'evidence_manifest_latest.json'
RP=STATE/'report_latest.json'
SRC='https://nationalhighways.co.uk/roads-and-travel/road-projects/south-east/south-east-maintenance-schemes/'
START=295
END=306
STATE.mkdir(parents=True, exist_ok=True)

candidates=[
 ('national_highways_se_maintenance:a1089_tilbury_20260630_20260922','A1089 near Tilbury Port - 30 June to 22 September 2026','Current/ongoing 2026 maintenance entry',['A1089 near Tilbury Port','30 June to 22 September 2026']),
 ('national_highways_se_maintenance:a21_vauxhall_slip_closure_2026','A21 Vauxhall slip way closure','Current bridge-parapet repair restriction entry',['A21 Vauxhall slip way closure']),
 ('national_highways_se_maintenance:a21_robertsbridge_20260824_20260919','A21 Robertsbridge Bypass - 24 August to 19 September 2026','Forward 2026 maintenance entry',['A21 Robertsbridge Bypass','24 August to 19 September 2026']),
 ('national_highways_se_maintenance:a21_quarry_hill_20260827_20260828','A21 Quarry Hill Expansion Joints - 27 to 28 August 2026','Forward 2026 maintenance entry',['A21 Quarry Hill Expansion Joints','27 to 28 August 2026']),
 ('national_highways_se_maintenance:a27_fontwell_crockerhill_20260713_20260822','A27 Fontwell to Crockerhill resurfacing - 13 July to 22 August 2026','Current/ongoing 2026 maintenance entry',['A27 Fontwell to Crockerhill resurfacing','13 July to 22 August 2026']),
 ('national_highways_se_maintenance:a303_kimpton_quarley_20260812_20261024','A303 Kimpton Quarley parapet replacement - 12 August to 24 October 2026','Current/ongoing 2026 maintenance entry',['A303 Kimpton Quarley parapet replacement','12 August to 24 October 2026']),
 ('national_highways_se_maintenance:a34_marcham_abingdon_20260615_20261030','A34 near Marcham and Abingdon - 15 June until 30 October 2026','Current/ongoing 2026 maintenance entry',['A34 near Marcham and Abingdon','15 June until 30 October 2026']),
 ('national_highways_se_maintenance:m2_medway_bridge_six_weeks_2026','M2 Medway Bridge London-bound restrictions - up to six weeks','Current repair restriction entry',['M2 Medway Bridge','up to six weeks']),
 ('national_highways_se_maintenance:m2_j3_resurfacing_20260526_20260827','M2 Junction 3 resurfacing - 26 May to 27 August 2026','Current/ongoing 2026 maintenance entry',['M2 Junction 3 resurfacing','26 May to 27 August 2026']),
 ('national_highways_se_maintenance:m20_birling_overbridge_from_20260720','M20 Birling Road overbridge refurbishment - from 20 July 2026','Current/ongoing 2026 maintenance entry',['M20 Birling Road overbridge refurbishment','20 July 2026']),
 ('national_highways_se_maintenance:m20_j6_chatham_20260914_20260926','M20 junction 6 Chatham Road works - 14 to 26 September 2026','Forward 2026 maintenance entry',['M20 junction 6 Chatham Road works','14 to 26 September 2026']),
 ('national_highways_se_maintenance:m4_j5_pavement_20260810_20260902','M4 junction 5 slip road pavement renewal - 10 August to 2 September 2026','Current/ongoing 2026 maintenance entry',['M4 junction 5 slip road pavement renewal','10 August to 2 September 2026']),
]

def load(p): return json.loads(p.read_text(encoding='utf-8'))
def dump(p,o): p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):
    s=html.unescape(s)
    s=re.sub(r'<script\b[^>]*>.*?</script>',' ',s,flags=re.I|re.S)
    s=re.sub(r'<style\b[^>]*>.*?</style>',' ',s,flags=re.I|re.S)
    s=re.sub(r'<[^>]+>',' ',s)
    s=s.replace('–','-').replace('—','-').replace('‑','-')
    return re.sub(r'\s+',' ',s).strip().lower()
def fetch(url):
    last=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 AAYS FG7 evidence runner/1.0','Accept':'text/html,application/xhtml+xml'})
            with urllib.request.urlopen(req,timeout=40) as r:
                body=r.read(); code=getattr(r,'status',200); final=r.geturl()
            return {'ok':True,'body':body,'status':code,'final':final}
        except Exception as e:
            last=repr(e); time.sleep(2+attempt)
    return {'ok':False,'error':last,'body':b'','status':None,'final':url}
def cat_blob(blob_sha): return subprocess.check_output(['git','cat-file','-p',blob_sha],text=True)

cp0=load(CP); st0=load(ST); mf0=load(MF); shard=load(SHARD)
if cp0.get('slot_id')!=SLOT or cp0.get('continuation_key')!=CONT: raise SystemExit('WRONG_SLOT_OR_CONTINUATION')
if int(cp0.get('next_batch_index',-1))!=START: raise SystemExit(f"CURSOR_MISMATCH:{cp0.get('next_batch_index')}")
if st0.get('slot_id')!=SLOT or mf0.get('slot_id')!=SLOT: raise SystemExit('STATE_SLOT_MISMATCH')
md=shard.get('metadata') or {}
if md.get('slot_id')!=SLOT or md.get('continuation_key')!=CONT: raise SystemExit('SHARD_SLOT_MISMATCH')
features=shard.get('features') or []
artifact_count=len(features)
if artifact_count!=18: raise SystemExit(f'UNEXPECTED_SHARD_COUNT:{artifact_count}')
ids=[(f.get('properties') or {}).get('source_feature_id') for f in features]
if any(x is None for x in ids) or len(ids)!=len(set(ids)): raise SystemExit('SHARD_DUPLICATE_IDS')
strict_before=sum(1 for f in features if f.get('geometry') is not None and (f.get('properties') or {}).get('parcel_id'))
if strict_before!=0: raise SystemExit(f'UNEXPECTED_STRICT_BEFORE:{strict_before}')
prior_cp_blob=subprocess.check_output(['git','rev-parse',f'HEAD:{CP.as_posix()}'],text=True).strip()

history=[]; seen_blobs=set(); cur=prior_cp_blob
while cur and cur not in seen_blobs:
    seen_blobs.add(cur)
    obj=json.loads(cat_blob(cur))
    history.extend(obj.get('used_window_keys_this_run') or obj.get('used_window_keys') or [])
    cur=obj.get('prior_checkpoint_blob_sha')
history_set=set(history)
keys=[x[0] for x in candidates]
if len(keys)!=12 or len(set(keys))!=12: raise SystemExit('NEW_WINDOW_DUPLICATE')
reused=sorted(set(keys)&history_set)
if reused: raise SystemExit('REUSED_WINDOW:'+','.join(reused))

source_contract={
 'existing_source_family':'Scottish Government NPF4 Annex B national developments',
 'new_source_family':'National Highways official South East maintenance scheme entries - unused window set 24',
 'project_index':SRC,
 'canonical_target':'AAYS england_map_web future_growth parcel mirror',
 'matching_rule':'STRICT_CENTROID_WITHIN_POLYGON_OR_EXACT_INTERSECTION_ONLY',
 'nearest_match_allowed':False,
 'strict_join_input_status':'Official National Highways maintenance headings can prove source windows, but no jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is exposed to this hosted runner; source-only evidence is not promoted to parcel evidence.'
}
processed=[]; readbacks=[]
reason='Official National Highways maintenance heading verified. No jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is available to prove strict centroid-within-polygon or exact intersection; no inferred polygon, proximity, nearest match, or fake data used.'

for offset,(key,name,stage,terms) in enumerate(candidates):
    batch=START+offset
    fr=fetch(SRC)
    accessed=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    ok=False; why=None; body_hash=None; body_bytes=0
    if fr['ok']:
        body_hash=hashlib.sha256(fr['body']).hexdigest(); body_bytes=len(fr['body']); body_text=norm(fr['body'].decode('utf-8',errors='ignore'))
        missing=[t for t in terms if norm(t) not in body_text]
        ok=(len(missing)==0)
        if missing: why='SOURCE_IDENTITY_TERMS_MISSING:'+repr(missing)
    else: why='SOURCE_FETCH_FAILED:'+str(fr.get('error'))
    result='ZERO_SAFE_CANONICAL_MATCHES' if ok else 'SOURCE_VERIFICATION_FAILED_NO_PROMOTION'
    rec={'batch':batch,'window_key':key,'project_name':name,'project_stage':stage,'source_ref':SRC,'source_fetch_ok':bool(fr['ok']),'source_http_status':fr.get('status'),'source_final_url':fr.get('final',SRC),'source_sha256_runtime':body_hash,'source_bytes_runtime':body_bytes,'source_accessed_at':accessed,'source_verification':'official_national_highways_south_east_heading_runtime_verified_2026-08-18' if ok else 'verification_failed_no_promotion','result':result,'new_unique_evidenced_parcels':0,'reason':reason if ok else why,'reason_code':'STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE' if ok else 'SOURCE_VERIFICATION_FAILED'}
    processed.append(rec)
    cp={'schema_version':6,'slot_id':SLOT,'continuation_key':CONT,'state':'BOUNDED_RUN_IN_PROGRESS_NO_NEW_STRICT_MATCHES' if batch<END else 'BOUNDED_RUN_COMPLETE_NO_NEW_STRICT_MATCHES','prior_checkpoint_blob_sha':prior_cp_blob,'used_window_history_contract':'Resolve prior used-window set from prior_checkpoint_blob_sha; append current keys; never reuse either set.','used_window_keys_this_run':[x['window_key'] for x in processed],'unique_evidenced_parcel_count_before':strict_before,'unique_evidenced_parcel_count_after':strict_before,'new_unique_evidenced_parcels':0,'mirror_feature_count':artifact_count,'artifact_feature_count':artifact_count,'legacy_source_evidence_feature_count':artifact_count,'duplicate_count':0,'latest_batch':batch,'next_batch_index':batch+1,'new_run_bounded_batches_completed':offset+1,'last_batch':rec,'source_contract':source_contract,'prior_history_window_count':len(history_set),'blocker':'STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE_TO_HOSTED_RUNNER','fake_data':False,'nearest_match_used':False,'demo_only':True,'final_ready':False,'production_merge':False}
    st={'schema_version':1,'slot_id':SLOT,'continuation_key':CONT,'state':cp['state'],'latest_batch':batch,'bounded_batches_completed_this_run':offset+1,'artifact_feature_count':artifact_count,'unique_evidenced_parcel_count':strict_before,'duplicate_count':0,'nearest_match_used':False,'fake_data':False,'cross_slot_writes':False,'final_ready':False,'production_merge':False,'last_window_key':key,'last_result':result}
    mf={'schema_version':1,'slot_id':SLOT,'continuation_key':CONT,'artifact_feature_count':artifact_count,'legacy_source_evidence_feature_count':artifact_count,'unique_evidenced_parcel_count':strict_before,'duplicate_count':0,'existing_source_id':md.get('source_id'),'existing_source_url':md.get('source_url'),'new_source_family':source_contract['new_source_family'],'processed_windows_this_run':processed,'fake_data':False,'nearest_match_used':False,'demo_only':True,'final_ready':False,'production_merge':False}
    dump(CP,cp); dump(ST,st); dump(MF,mf)
    rb_shard=load(SHARD); rb_cp=load(CP); rb_st=load(ST); rb_mf=load(MF)
    counts=[len(rb_shard.get('features') or []),rb_cp.get('artifact_feature_count'),rb_st.get('artifact_feature_count'),rb_mf.get('artifact_feature_count')]
    rb_ids=[(f.get('properties') or {}).get('source_feature_id') for f in rb_shard.get('features') or []]
    dup=len(rb_ids)-len(set(rb_ids))
    good=(counts==[artifact_count]*4 and dup==0 and rb_cp.get('duplicate_count')==0 and rb_st.get('duplicate_count')==0 and rb_mf.get('duplicate_count')==0 and rb_cp.get('nearest_match_used') is False and rb_st.get('nearest_match_used') is False and rb_mf.get('nearest_match_used') is False and rb_cp.get('fake_data') is False and rb_st.get('fake_data') is False and rb_mf.get('fake_data') is False)
    if not good: raise SystemExit(f'READBACK_FAIL_BATCH_{batch}:counts={counts}:dup={dup}')
    readbacks.append({'batch':batch,'window_key':key,'shard_checkpoint_status_manifest_count':artifact_count,'duplicate_count':0,'pass':True,'sha256':{'shard':sha(SHARD),'checkpoint':sha(CP),'status':sha(ST),'manifest':sha(MF)}})

report={'schema_version':1,'slot_id':SLOT,'continuation_key':CONT,'run_id':'common_continuation_20260818_batches_295_306_hosted','requested_common_continuation_path':r'F:\TerraYield_AAYS_Portable\docs\deepseek_prompts\AAYS_CHATGPT_PLAN_00_23_SLOT_COMMON_CONTINUATION_20260818.md','requested_common_continuation_file_read':False,'requested_common_continuation_file_note':'The exact F: path is not mounted in the hosted runner/session and the same path is absent on the canonical GitHub branch. The run continued from canonical FG7 report/checkpoint/status/manifest/shard state and the current user continuation instruction; this limitation is recorded rather than fabricated.','requested_new_bounded_batches':12,'completed_new_bounded_batches':12,'batch_range':{'first':START,'last':END},'counts':{'before':strict_before,'added':0,'after':strict_before,'before_unique_evidenced_parcels':strict_before,'added_unique_evidenced_parcels':0,'after_unique_evidenced_parcels':strict_before,'legacy_source_evidence_feature_count':artifact_count,'mirror_feature_count':artifact_count,'duplicate_count':0},'quality_gates':{'shard_checkpoint_status_manifest_count_equal_each_batch':True,'dup0_each_batch':True,'nearest_match_used':False,'fake_data':False,'cross_slot_writes':False,'own_slot_only':True,'reused_window_count':0,'final_ready':False,'production_merge':False,'all_zero_or_verification_failed_windows_checkpointed':True},'artifact_paths':{'shard':str(SHARD),'checkpoint':str(CP),'status':str(ST),'manifest':str(MF),'report':str(RP)},'source_contract':source_contract,'source_refs':[SRC],'source_window_keys':keys,'source_windows':processed,'per_batch_readbacks':readbacks,'prior_checkpoint_blob_sha':prior_cp_blob,'prior_history_window_count':len(history_set),'blocker':'STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE_TO_HOSTED_RUNNER','blocker_reason':'Twelve unused official National Highways South East maintenance windows were processed. No candidate was promoted to parcel evidence because a strict spatial relation to canonical parcel geometry was not provable; no nearest/proximity/inferred match or fake data was used.','next_batch_index':END+1,'next_action':'Continue only from latest canonical state with previously unused official source windows; do not reuse batches 295-306 or any prior-chain window.'}
dump(RP,report)
print(json.dumps({'slot':SLOT,'before':strict_before,'added':0,'after':strict_before,'batches':'295-306','next':END+1,'readbacks':len(readbacks)},indent=2))

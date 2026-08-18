import json, pathlib, subprocess, datetime, time
CANON='codex/aays-single-runner-v5-20260706'
SLOT='future_growth_3'
START=217
END=228
P={
 'shard': pathlib.Path('AAYS/england_map_web/data/future_growth/shards/future_growth_3_latest.geojson'),
 'checkpoint': pathlib.Path('state/slots/future_growth_3/checkpoint_latest.json'),
 'status': pathlib.Path('state/slots/future_growth_3/status_latest.json'),
 'manifest': pathlib.Path('state/slots/future_growth_3/evidence_manifest_latest.json'),
 'report': pathlib.Path('state/slots/future_growth_3/report_latest.json'),
}
def rj(p): return json.loads(p.read_text())
def wj(p,o): p.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n')
def git(*a,check=True,capture=False):
    x=subprocess.run(['git',*a],text=True,capture_output=capture)
    if check and x.returncode: raise RuntimeError('git '+' '.join(a)+': '+x.stderr)
    return x
def push(paths,msg):
    git('add',*paths)
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines()
    if any(x not in paths for x in staged): raise RuntimeError('CROSS_SLOT_STAGED:'+repr(staged))
    if not staged: raise RuntimeError('NO_STAGED_STATE')
    git('commit','-m',msg)
    for n in range(1,7):
        git('fetch','origin',CANON)
        if git('merge-base','--is-ancestor','origin/'+CANON,'HEAD',check=False).returncode: git('rebase','origin/'+CANON)
        x=git('push','origin','HEAD:'+CANON,check=False,capture=True)
        if not x.returncode: break
        if n==6: raise RuntimeError('PUSH_FAILED:'+x.stderr)
        time.sleep(2*n)
    git('fetch','origin',CANON)
def remote(p): return json.loads(subprocess.check_output(['git','show','origin/'+CANON+':'+str(p)],text=True))
ck,st,mf,sh,rp=(rj(P[x]) for x in ('checkpoint','status','manifest','shard','report'))
assert ck.get('slot_id')==st.get('slot_id')==mf.get('slot_id')==rp.get('slot_id')==SLOT
assert int(ck.get('next_batch_index',0))==END
assert int(st.get('bounded_batches_completed_this_continuation',0))==END
assert int(mf.get('bounded_batches_completed',0))==END
assert rp.get('batch_range')=={'first':START,'last':END}
assert rp.get('requested_new_bounded_batches')==12
assert rp.get('completed_new_bounded_batches')==12
q=rp.get('quality_gates',{})
assert q.get('remote_readback_verified') is True
assert q.get('reused_window_count')==0
assert q.get('nearest_match_used') is False
assert q.get('fake_data') is False
assert q.get('cross_slot_writes') is False
assert q.get('own_slot_only') is True
windows=rp.get('source_windows') or []
assert len(windows)==12 and [int(x.get('batch_index',0)) for x in windows]==list(range(START,END+1))
ids=[x.get('window_id') for x in windows]
assert len(ids)==len(set(ids))==12
processed=ck.get('processed_window_ids') or []
assert len(processed)==END and len(set(processed))==END and all(x in processed for x in ids)
counts=rp.get('counts') or {}
before=int(counts.get('before_unique_evidenced_parcels',0))
added=int(counts.get('added_unique_evidenced_parcels',0))
after=int(counts.get('after_unique_evidenced_parcels',0))
assert after-before==added
assert int(counts.get('duplicate_count',0))==0
now=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
mf.update({
 'updated_at':now,
 'bounded_batches_completed':END,
 'request_batch_start':START,
 'request_batch_end':END,
 'completed_new_bounded_batches_this_request':12,
 'accepted_new_canonical_parcels':after,
 'rejected_or_blocked_candidates':len(processed),
 'fake_data':False,
 'nearest_match_used':False,
 'duplicate_count':0,
 'feature_count_before':before,
 'new_features_added':added,
 'feature_count_after':after,
 'feature_count':after,
 'processed_window_ids':processed,
 'processed_window_count':len(processed),
 'request_source_windows':windows,
 'processed_windows_this_request':ids,
 'discovery_pages':rp.get('discovery_pages',[]),
 'canonical_parcel_inventory':rp.get('canonical_parcel_inventory',{}),
 'source_contract':rp.get('source_contract',{}),
 'report_path':str(P['report']),
 'report_counts':{
   'before':before,
   'added':added,
   'after':after,
   'dup':0,
   'new_bounded_batches_this_request':12,
   'request_batch_range':f'{START}-{END}',
   'bounded_batches_total':END,
   'processed_windows_total':len(processed),
 },
 'blocker_reason':f'Twelve new distinct authoritative source windows (batches {START}-{END}) were processed and checkpointed, but the canonical geometry inventory still has no explicit parcel_id rows, so no strict evidenced parcel could be emitted without identity inference.',
 'remote_readback_verified':True,
 'remote_readback_summary':{'shard':after,'checkpoint':after,'status':after,'manifest':after,'bounded_batches_total':END,'new_batches':12,'dup':0},
 'normalization_note':f'Final current-request normalization after batches {START}-{END}; legacy reconciliation fields from older request ranges were replaced without creating parcel evidence.'
})
rp.setdefault('quality_gates',{})['manifest_current_request_fields_normalized']=True
rp['manifest_normalization']={'updated_at':now,'processed_window_count':len(processed),'request_batch_range':f'{START}-{END}','bounded_batches_total':END,'dup':0,'remote_readback_verified':True}
wj(P['manifest'],mf); wj(P['report'],rp)
push([str(P['manifest']),str(P['report'])],f'future_growth_3: normalize manifest/report after strict batches {START}-{END}')
R={k:remote(P[k]) for k in ('shard','checkpoint','status','manifest','report')}
shard_n=len(R['shard'].get('features',[]))
ck_n=int(R['checkpoint'].get('feature_count_after',0))
st_n=int(R['status'].get('feature_count_after',0))
mf_n=int(R['manifest'].get('feature_count_after',R['manifest'].get('feature_count',0)))
assert shard_n==ck_n==st_n==mf_n==after
assert int(R['shard'].get('metadata',{}).get('last_batch_index',0))==END
assert int(R['checkpoint'].get('next_batch_index',0))==END
assert int(R['status'].get('bounded_batches_completed_this_continuation',0))==END
assert int(R['manifest'].get('bounded_batches_completed',0))==END
assert int(R['manifest'].get('processed_window_count',0))==END
assert R['manifest'].get('report_counts',{}).get('request_batch_range')==f'{START}-{END}'
assert int(R['manifest'].get('report_counts',{}).get('bounded_batches_total',0))==END
assert int(R['manifest'].get('remote_readback_summary',{}).get('bounded_batches_total',0))==END
assert len(R['manifest'].get('request_source_windows') or [])==12
assert [int(x.get('batch_index',0)) for x in R['manifest'].get('request_source_windows') or []]==list(range(START,END+1))
assert R['manifest'].get('processed_windows_this_request')==ids
assert all(int(R[x].get('duplicate_count',0))==0 for x in ('checkpoint','status','manifest'))
assert R['report'].get('quality_gates',{}).get('manifest_current_request_fields_normalized') is True
print(json.dumps({'slot_id':SLOT,'before':before,'added':added,'after':after,'cursor':END,'processed_window_count':END,'dup':0,'normalized':True}))

import datetime, json, os, re, shutil, subprocess, sys, tempfile, textwrap
from pathlib import Path

REPO='cagdascagdas100/chat_gpt_clone_1'
CANON='codex/aays-single-runner-v5-20260706'
SLOT='building_type_9'
CONT='building-type-9-england-classification-v1-20260808'
START=229
NEXT=241
BEFORE=7945
TRIGGER=Path('trigger')
WORK=Path('canonical')
HIST='.github/workflows/aays-bt9-strict-12batches-20260818-once.yml'
HIST_COMMIT='434fa3dd744ccafb6c38aaeb6a849e90f8837bf2'
PATHS=[
 'england_map_web/data/building_type/shards/building_type_9_latest.geojson',
 'england_map_web/data/building_type/shards/building_type_9_manifest_latest.json',
 'docs/chatgpt_status/building_type/slots/building_type_9/runner_outputs/building_type_9_classification_latest.json',
 'docs/chatgpt_status/_shared/slots_21/building_type_9/status_latest.json',
 'docs/chatgpt_status/_shared/slots_21/building_type_9/checkpoint_latest.json',
 'docs/chatgpt_status/_shared/slots_21/building_type_9/current_task_latest.json',
]
GP,MP,RP,SP,CP,TP=PATHS

def run(cmd,cwd=None,check=True,capture=False):
    p=subprocess.run(cmd,cwd=cwd,text=True,check=check,stdout=subprocess.PIPE if capture else None,stderr=subprocess.STDOUT if capture else None)
    return p.stdout if capture else ''

def git_show_json(repo,ref,path):
    return json.loads(run(['git','show',f'{ref}:{path}'],cwd=repo,capture=True))

def file_json(repo,path):
    return json.loads((Path(repo)/path).read_text(encoding='utf-8'))

def write_json(path,obj):
    Path(path).write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')

def remote_snapshot(repo):
    ref=f'origin/{CANON}'
    r=git_show_json(repo,ref,RP); s=git_show_json(repo,ref,SP); c=git_show_json(repo,ref,CP); m=git_show_json(repo,ref,MP); g=git_show_json(repo,ref,GP)
    n=len(g.get('features') or [])
    return r,s,c,m,g,n

def validate_preflight():
    run(['git','fetch','origin',CANON],cwd=WORK)
    run(['git','reset','--hard',f'origin/{CANON}'],cwd=WORK)
    r,s,c,m,g,n=remote_snapshot(WORK)
    if c.get('slot_id')!=SLOT or c.get('continuation_key')!=CONT: raise SystemExit('SLOT_OR_CONTINUATION_CHANGED')
    if s.get('owner') not in (None,''): raise SystemExit('LIVE_OWNER_PRESENT:'+repr(s.get('owner')))
    if (c.get('next_batch_index'),s.get('next_batch_index'),r.get('next_batch_index'))!=(START,START,START): raise SystemExit('PREFLIGHT_CURSOR_CHANGED')
    vals=[n,c.get('feature_count_after'),s.get('total_elements'),m.get('total_features'),r.get('feature_count_after')]
    if len(set(vals))!=1 or n!=BEFORE: raise SystemExit('PREFLIGHT_COUNT_MISMATCH:'+repr(vals))
    sc=str(r.get('source_contract') or '')
    if 'AAYS_CHATGPT_PLAN_00_23_SLOT_COMMON_CONTINUATION_20260818' not in sc or 'source_contract_v2' not in sc: raise SystemExit('SOURCE_CONTRACT_CHANGED:'+sc)
    if r.get('duplicate_count')!=0 or r.get('nearest_matching_used') or r.get('fake_data'): raise SystemExit('PREFLIGHT_DATA_POLICY_FAILED')
    print(json.dumps({'preflight':True,'slot':SLOT,'before':n,'cursor':START,'owner':s.get('owner'),'source_contract':sc},ensure_ascii=False))

def extract_runner():
    old=run(['git','show',f'{HIST_COMMIT}:{HIST}'],cwd=TRIGGER,capture=True)
    m=re.search(r"cat > /tmp/bt9_181_192\.py <<'PY'\n(.*?)\n\s*PY\n\s*python /tmp/bt9_181_192\.py",old,re.S)
    if not m: raise SystemExit('VERIFIED_PARENT_RUNNER_NOT_FOUND')
    s=textwrap.dedent(m.group(1))
    repl=[
      ('W=[]; bi=181','W=[]; bi=229'),
      ('for y in (575000,580000,585000):','for y in (635000,640000,645000):'),
      ('if start!=181:','if start!=229:'),
      ('if len(fs)!=7200:','if len(fs)!=7945:'),
      ("'start_batch_index':181","'start_batch_index':229"),
      ("'next_batch_index':181","'next_batch_index':229"),
      ("rep['next_batch_index']=193","rep['next_batch_index']=241"),
      ("cp['next_batch_index']=193","cp['next_batch_index']=241"),
      ("st['next_batch_index']=193","st['next_batch_index']=241"),
      ("task['next_batch_index']=193","task['next_batch_index']=241"),
      ('BATCH_193_STRICT_SPATIAL_BINDING_SOURCE_BYTES','BATCH_241_STRICT_SPATIAL_BINDING_SOURCE_BYTES'),
      ('Continue from batch 193','Continue from batch 241'),
      ('Batches 181-192 processed','Batches 229-240 processed'),
      ("'next_batch':193","'next_batch':241")]
    for a,b in repl:
        if a not in s: raise SystemExit('EXPECTED_PARENT_TOKEN_MISSING:'+a)
        s=s.replace(a,b)
    p=Path('/tmp/bt9_229_240.py'); p.write_text(s,encoding='utf-8'); return p

def validate_local_after():
    r=file_json(WORK,RP); s=file_json(WORK,SP); c=file_json(WORK,CP); m=file_json(WORK,MP); g=file_json(WORK,GP); n=len(g.get('features') or [])
    vals=[n,m.get('total_features'),c.get('feature_count_after'),s.get('total_elements'),r.get('feature_count_after')]
    if len(set(vals))!=1: raise SystemExit('LOCAL_COUNT_MISMATCH:'+repr(vals))
    if (r.get('next_batch_index'),c.get('next_batch_index'),s.get('next_batch_index'))!=(NEXT,NEXT,NEXT): raise SystemExit('LOCAL_CURSOR_FAILED')
    if r.get('duplicate_count')!=0: raise SystemExit('LOCAL_DUP_FAILED')
    bs=r.get('batches') or []
    if [x.get('batch_index') for x in bs]!=list(range(START,NEXT)): raise SystemExit('LOCAL_BATCH_RANGE_FAILED')
    if not all(x.get('readback_verified') and x.get('dup')==0 and x.get('shard_equals_checkpoint_equals_status_equals_manifest') and not x.get('nearest_matching_used') and not x.get('fake_data') for x in bs): raise SystemExit('LOCAL_PER_BATCH_READBACK_FAILED')
    return r,n

def package_payload():
    payload=Path('/tmp/bt9_payload'); shutil.rmtree(payload,ignore_errors=True); payload.mkdir(parents=True)
    for p in PATHS:
        q=payload/p; q.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(WORK/p,q)
    return payload

def remote_guard(repo,expected_cursor):
    run(['git','fetch','origin',CANON],cwd=repo)
    c=git_show_json(repo,f'origin/{CANON}',CP)
    if c.get('slot_id')!=SLOT or c.get('continuation_key')!=CONT or c.get('next_batch_index')!=expected_cursor:
        raise SystemExit('REMOTE_BT9_MOVED_ABORT:'+repr((c.get('slot_id'),c.get('continuation_key'),c.get('next_batch_index'))))

def publish_payload(payload):
    pub=Path('/tmp/bt9_publish'); shutil.rmtree(pub,ignore_errors=True)
    run(['git','fetch','origin',CANON],cwd=WORK)
    run(['git','worktree','add','--detach',str(pub),f'origin/{CANON}'],cwd=WORK)
    run(['git','config','user.name','TerraYield AAYS Bot'],cwd=pub); run(['git','config','user.email','aays-bot@users.noreply.github.com'],cwd=pub)
    ok=False
    for attempt in (1,2,3):
        remote_guard(pub,START)
        run(['git','reset','--hard',f'origin/{CANON}'],cwd=pub)
        for p in PATHS: shutil.copy2(payload/p,pub/p)
        run(['git','add','--',*PATHS],cwd=pub)
        if not run(['git','diff','--cached','--quiet'],cwd=pub,check=False):
            pass
        run(['git','commit','-m','aays: building_type_9 strict bounded batches 229-240'],cwd=pub)
        p=subprocess.run(['git','push','origin',f'HEAD:{CANON}'],cwd=pub,text=True)
        if p.returncode==0: ok=True; break
        print('PUSH_RACE_RETRY',attempt)
    if not ok: raise SystemExit('MATERIAL_PUSH_FAILED')
    return pub

def verify_remote(repo,require_flag=False):
    run(['git','fetch','origin',CANON],cwd=repo)
    r,s,c,m,g,n=remote_snapshot(repo)
    vals=[n,m.get('total_features'),c.get('feature_count_after'),s.get('total_elements'),r.get('feature_count_after')]
    if len(set(vals))!=1: raise SystemExit('REMOTE_COUNT_MISMATCH:'+repr(vals))
    if (r.get('next_batch_index'),c.get('next_batch_index'),s.get('next_batch_index'))!=(NEXT,NEXT,NEXT): raise SystemExit('REMOTE_CURSOR_FAILED')
    if r.get('duplicate_count')!=0: raise SystemExit('REMOTE_DUP_FAILED')
    bs=r.get('batches') or []
    if [x.get('batch_index') for x in bs]!=list(range(START,NEXT)): raise SystemExit('REMOTE_BATCH_RANGE_FAILED')
    if not all(x.get('readback_verified') and x.get('dup')==0 and x.get('shard_equals_checkpoint_equals_status_equals_manifest') and not x.get('nearest_matching_used') and not x.get('fake_data') for x in bs): raise SystemExit('REMOTE_PER_BATCH_READBACK_FAILED')
    if require_flag and not r.get('remote_readback_verified'): raise SystemExit('REMOTE_READBACK_FLAG_FAILED')
    return r,s,c,m,n,vals,[x.get('batch_index') for x in bs if (x.get('added_feature_count') or 0)==0]

def stamp_remote_readback(pub):
    meta=[RP,SP,CP,MP]
    ok=False
    for attempt in (1,2,3):
        remote_guard(pub,NEXT)
        run(['git','reset','--hard',f'origin/{CANON}'],cwd=pub)
        r,s,c,m,n,vals,zeros=verify_remote(pub)
        sha=run(['git','rev-parse',f'origin/{CANON}'],cwd=pub,capture=True).strip()
        stamp=datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
        for p in meta:
            o=file_json(pub,p); o['remote_readback_verified']=True; o['last_material_commit_sha']=sha; o['remote_readback_at']=stamp
            if p==RP: o['remote_readback_counts']={'shard':n,'manifest':vals[1],'checkpoint':vals[2],'status':vals[3],'report':vals[4],'dup':0}
            write_json(pub/p,o)
        run(['git','add','--',*meta],cwd=pub)
        run(['git','commit','-m','aays: verify building_type_9 remote readback 229-240'],cwd=pub)
        p=subprocess.run(['git','push','origin',f'HEAD:{CANON}'],cwd=pub,text=True)
        if p.returncode==0: ok=True; break
        print('READBACK_PUSH_RACE_RETRY',attempt)
    if not ok: raise SystemExit('READBACK_METADATA_PUSH_FAILED')

validate_preflight()
runner=extract_runner()
run([sys.executable,str(runner)],cwd=WORK)
local_r,local_n=validate_local_after()
payload=package_payload()
pub=publish_payload(payload)
r,s,c,m,n,vals,zeros=verify_remote(pub)
stamp_remote_readback(pub)
r,s,c,m,n,vals,zeros=verify_remote(pub,require_flag=True)
print(json.dumps({'report':RP,'slot':SLOT,'batches':list(range(START,NEXT)),'before':r.get('feature_count_before'),'added':r.get('new_added'),'after':n,'next_batch':NEXT,'dup':0,'zero_batches':zeros,'remote_counts':vals,'remote_readback_verified':True},ensure_ascii=False))
